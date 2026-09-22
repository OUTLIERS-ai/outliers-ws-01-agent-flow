"""Shared helpers for the agent-flow workspace kit.

Every path is worked out when a function is called, never at import, so the
tests can point HOME / USERPROFILE / APPDATA at a temporary folder.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

# Hide every console window a child program would otherwise open on Windows.
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"

# The package version this kit was checked against on 2026-09-22.
DEFAULT_PACKAGE = "agent-flow-app@0.9.1"
UI_PORT = 3001

# The 9 Claude Code events the upstream installer hooks.
EVENTS = [
    "SessionStart",
    "PreToolUse",
    "PostToolUse",
    "PostToolUseFailure",
    "SubagentStart",
    "SubagentStop",
    "Notification",
    "Stop",
    "SessionEnd",
]
HOOK_TIMEOUT_S = 2
MARKER = "agent-flow/hook.js"

KIT_DIR = Path(__file__).resolve().parent
QUIET_ENV = {"AGENT_FLOW_TELEMETRY": "false", "DO_NOT_TRACK": "1"}


# ---------------------------------------------------------------- paths
def home() -> Path:
    return Path.home()


def claude_dir() -> Path:
    """Where Claude Code keeps settings.json (honours CLAUDE_CONFIG_DIR)."""
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(env) if env else home() / ".claude"


def settings_path() -> Path:
    return claude_dir() / "settings.json"


def discovery_dir() -> Path:
    """agent-flow always uses <home>/.claude/agent-flow, whatever CLAUDE_CONFIG_DIR says."""
    return home() / ".claude" / "agent-flow"


def hook_script() -> Path:
    return discovery_dir() / "hook.js"


def config_path() -> Path:
    return KIT_DIR / "config.json"


def logs_dir() -> Path:
    return KIT_DIR / "logs"


def startup_dir() -> Path:
    appdata = os.environ.get("APPDATA") or str(home() / "AppData" / "Roaming")
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def launch_agents_dir() -> Path:
    return home() / "Library" / "LaunchAgents"


# ---------------------------------------------------------------- files
def detect_eol(path: Path) -> str:
    """Keep the file's own line endings, so an uninstall gives back the same bytes."""
    try:
        return "\r\n" if b"\r\n" in path.read_bytes() else "\n"
    except OSError:
        return "\n"


def atomic_write_text(path: Path, text: str, eol: str = "\n") -> None:
    """Write to a temp file beside the target, then swap it in. Never truncates."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline=eol) as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def backup(path: Path, tag: str) -> Path | None:
    if not path.exists():
        return None
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = path.with_name(f"{path.name}.bak-{tag}-{stamp}")
    n = 1
    while dest.exists():
        n += 1
        dest = path.with_name(f"{path.name}.bak-{tag}-{stamp}-{n}")
    shutil.copy2(path, dest)
    return dest


def read_settings(path: Path | None = None) -> dict:
    path = path or settings_path()
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8-sig")
    if not text.strip():
        return {}
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a JSON object")
    return data


def dump_settings(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def load_config() -> dict:
    p = config_path()
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- hooks
def norm_command(cmd: str) -> str:
    return " ".join(cmd.replace("\\", "/").split()).lower()


def is_agent_flow_command(cmd) -> bool:
    return isinstance(cmd, str) and MARKER in norm_command(cmd)


def hook_command(node_path: str | None = None) -> str:
    """The hook line we install. Forward slashes on purpose: agent-flow 0.9.1 looks for
    the text 'agent-flow/hook.js' to decide it is already set up. A Windows path with
    backslashes never matches, so every server start used to add another copy."""
    node = node_path or shutil.which("node") or "node"
    node = str(node).replace("\\", "/")
    return f'"{node}" "{hook_script().as_posix()}"'


def count_agent_flow(settings: dict) -> dict:
    out = {}
    hooks = settings.get("hooks") or {}
    for ev in EVENTS:
        n = 0
        for group in hooks.get(ev) or []:
            for h in (group or {}).get("hooks") or []:
                if is_agent_flow_command(h.get("command")):
                    n += 1
        out[ev] = n
    return out


def remove_agent_flow(settings: dict) -> tuple[dict, int]:
    """Return a copy with every agent-flow hook removed, and how many were removed.
    Empty groups, empty events and an empty 'hooks' block are dropped so an
    uninstall leaves the file as it was before we came."""
    data = json.loads(json.dumps(settings))
    hooks = data.get("hooks")
    removed = 0
    if not isinstance(hooks, dict):
        return data, 0
    for ev in list(hooks.keys()):
        groups = hooks[ev]
        if not isinstance(groups, list):
            continue
        new_groups = []
        touched = False
        for group in groups:
            inner = (group or {}).get("hooks")
            if not isinstance(inner, list):
                new_groups.append(group)
                continue
            keep = [h for h in inner if not is_agent_flow_command(h.get("command"))]
            if len(keep) != len(inner):
                removed += len(inner) - len(keep)
                touched = True
                if not keep:
                    continue
                group = dict(group)
                group["hooks"] = keep
            new_groups.append(group)
        if touched and not new_groups:
            del hooks[ev]
        else:
            hooks[ev] = new_groups
    if not hooks:
        del data["hooks"]
    return data, removed


def install_agent_flow(settings: dict, command: str) -> tuple[dict, dict]:
    """Make every one of the 9 events carry exactly 1 agent-flow hook.
    Returns (new settings, {event: copies removed}). An event that already has
    exactly our hook is left untouched, so a second run changes nothing."""
    data = json.loads(json.dumps(settings))
    hooks = data.setdefault("hooks", {})
    removed = {}
    for ev in EVENTS:
        groups = hooks.get(ev) or []
        mine = [h for g in groups for h in (g or {}).get("hooks") or [] if is_agent_flow_command(h.get("command"))]
        if len(mine) == 1 and mine[0].get("command") == command:
            removed[ev] = 0
            continue
        cleaned, n = remove_agent_flow({"hooks": {ev: groups}})
        rest = (cleaned.get("hooks") or {}).get(ev, [])
        rest.append({"hooks": [{"type": "command", "command": command, "timeout": HOOK_TIMEOUT_S}]})
        hooks[ev] = rest
        removed[ev] = n
    return data, removed


def duplicate_report(settings: dict) -> dict:
    """{event: {command: copies}} for every command registered more than once."""
    out = {}
    for ev, groups in (settings.get("hooks") or {}).items():
        seen: dict[str, int] = {}
        for group in groups or []:
            for h in (group or {}).get("hooks") or []:
                key = norm_command(h.get("command") or h.get("url") or json.dumps(h, sort_keys=True))
                seen[key] = seen.get(key, 0) + 1
        dups = {k: v for k, v in seen.items() if v > 1}
        if dups:
            out[ev] = dups
    return out


# ---------------------------------------------------------------- processes
def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if IS_WIN:
        import ctypes

        k32 = ctypes.windll.kernel32
        handle = k32.OpenProcess(0x1000, False, int(pid))  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        code = ctypes.c_ulong()
        ok = k32.GetExitCodeProcess(handle, ctypes.byref(code))
        k32.CloseHandle(handle)
        return bool(ok) and code.value == 259  # STILL_ACTIVE
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def port_answers(port: int, timeout: float = 0.4) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def kill_tree(pid: int) -> None:
    if IS_WIN:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)], capture_output=True, creationflags=NO_WINDOW)
    else:
        import signal

        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass


def norm_path(p) -> str:
    try:
        r = os.path.realpath(str(p))
    except OSError:
        r = os.path.abspath(str(p))
    return os.path.normcase(r)


def discovery_files() -> list[dict]:
    """Every server registration agent-flow has left behind, with a live/stale verdict."""
    out = []
    d = discovery_dir()
    if not d.is_dir():
        return out
    for f in sorted(d.glob("*.json")):
        if f.name == "workspaces.json":
            continue
        info = {"file": f, "pid": None, "port": None, "workspace": None, "live": False, "reason": ""}
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            info.update(pid=int(data["pid"]), port=int(data["port"]), workspace=str(data["workspace"]))
        except Exception:
            info["reason"] = "unreadable"
            out.append(info)
            continue
        if not pid_alive(info["pid"]):
            info["reason"] = "process has ended"
        elif not port_answers(info["port"]):
            info["reason"] = "process number reused, nothing listening"
        else:
            info["live"] = True
            info["reason"] = "running"
        out.append(info)
    return out


def node_version() -> tuple[int, int, int] | None:
    node = shutil.which("node")
    if not node:
        return None
    try:
        out = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=20, creationflags=NO_WINDOW)
    except (OSError, subprocess.TimeoutExpired):
        return None
    txt = (out.stdout or "").strip().lstrip("v")
    try:
        parts = [int(x) for x in txt.split(".")[:3]]
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts)  # type: ignore[return-value]
    except ValueError:
        return None


def npx_command(package: str) -> list[str]:
    """The command that starts the server. AGENT_FLOW_NPX_CMD (a JSON list) replaces it in tests."""
    override = os.environ.get("AGENT_FLOW_NPX_CMD")
    if override:
        return list(json.loads(override))
    npx = shutil.which("npx")
    if not npx:
        raise FileNotFoundError("npx was not found. It comes with Node.js.")
    return [npx, "-y", package]
