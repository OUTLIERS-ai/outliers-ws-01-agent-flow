"""Install agent-flow for your Claude Code workspace, safely.

What it does, in order:
  1. Checks Node.js 18 or newer is installed (explains how to get it if not).
  2. Asks where your second brain vault and CRM vault are, and which folder to
     watch (the folder that contains both). Saves that in config.json.
  3. Runs agent-flow once, hidden, with a throwaway home folder, so it writes
     its own hook script without touching your settings; copies that script in.
  4. Backs up your Claude Code settings.json, then makes sure each of the 9
     agent-flow events has EXACTLY 1 copy of the hook. Extra copies are removed.
  5. Adds a hidden logon launcher (Windows: a .vbs in your Startup folder;
     Mac: a launchd job), with usage tracking switched off.

Run it twice and the second run changes nothing.

    python install.py                      # interview
    python install.py --yes                # accept the defaults it finds
    python install.py --uninstall          # remove the hook and the launcher
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import common
import start as starter

LAUNCHER_NAME_WIN = "outliers-agent-flow.vbs"
LAUNCHER_LABEL_MAC = "com.outliers.agent-flow"


# ---------------------------------------------------------------- interview
def _pointer(name: str) -> str | None:
    p = common.home() / name
    try:
        line = p.read_text(encoding="utf-8").strip().splitlines()[0].strip()
    except (OSError, IndexError):
        return None
    return line if line and Path(line).is_dir() else None


def find_vaults() -> list[Path]:
    """Folders with an .obsidian folder inside, up to 2 levels under home and Documents."""
    found: list[Path] = []
    roots = [common.home(), common.home() / "Documents"]
    for root in roots:
        if not root.is_dir():
            continue
        try:
            level1 = [p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")]
        except OSError:
            continue
        for p in level1:
            if (p / ".obsidian").is_dir():
                found.append(p)
                continue
            try:
                for q in p.iterdir():
                    if q.is_dir() and (q / ".obsidian").is_dir():
                        found.append(q)
            except OSError:
                pass
    uniq = []
    for p in found:
        if p not in uniq:
            uniq.append(p)
    return uniq


def guess_paths() -> tuple[str | None, str | None]:
    sb = _pointer(".outliers-sb")
    crm = _pointer(".outliers-crm")
    vaults = find_vaults()
    if not crm:
        for v in vaults:
            if any(w in v.name.lower() for w in ("crm", "pipeline", "sales", "clients")):
                crm = str(v)
                break
        if not crm and (common.home() / "CRM").is_dir():
            crm = str(common.home() / "CRM")
    if not sb:
        for v in vaults:
            if str(v) != crm:
                sb = str(v)
                break
        if not sb and (common.home() / "Documents" / "Second Brain").is_dir():
            sb = str(common.home() / "Documents" / "Second Brain")
    return sb, crm


def common_parent(paths: list[str]) -> str | None:
    real = [os.path.abspath(p) for p in paths if p]
    if not real:
        return None
    if len(real) == 1:
        return str(Path(real[0]).parent)
    try:
        return os.path.commonpath(real)
    except ValueError:  # different drives on Windows
        return None


def ask(prompt: str, default: str | None, assume_yes: bool) -> str | None:
    if assume_yes:
        return default
    shown = f" [{default}]" if default else ""
    try:
        ans = input(f"{prompt}{shown}: ").strip().strip('"')
    except EOFError:
        ans = ""
    return ans or default


# ---------------------------------------------------------------- launcher
def pythonw() -> str:
    exe = Path(sys.executable)
    cand = exe.with_name("pythonw.exe")
    return str(cand if cand.exists() else exe)


def vbs_text() -> str:
    start_py = common.KIT_DIR / "start.py"
    return (
        "' Starts agent-flow at logon with no window. Written by outliers-ws-01-agent-flow install.py.\n"
        "' The 0 below hides the window. Remove this file (or run install.py --uninstall) to stop it.\n"
        'Set sh = CreateObject("WScript.Shell")\n'
        'Set env = sh.Environment("PROCESS")\n'
        'env("AGENT_FLOW_TELEMETRY") = "false"\n'
        'env("DO_NOT_TRACK") = "1"\n'
        f'sh.Run """{pythonw()}"" ""{start_py}"" --quiet", 0, False\n'
    )


def plist_text() -> str:
    from xml.sax.saxutils import escape

    node = shutil.which("node")
    path_dirs = [str(Path(node).parent)] if node else []
    path_dirs += ["/usr/local/bin", "/opt/homebrew/bin", "/usr/bin", "/bin"]
    seen = []
    for d in path_dirs:
        if d not in seen:
            seen.append(d)
    args = [sys.executable, str(common.KIT_DIR / "start.py"), "--foreground", "--quiet"]
    arg_xml = "".join(f"    <string>{escape(a)}</string>\n" for a in args)
    log = escape(str(common.logs_dir() / "launchd.log"))
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n<dict>\n'
        f"  <key>Label</key><string>{LAUNCHER_LABEL_MAC}</string>\n"
        "  <key>ProgramArguments</key>\n  <array>\n" + arg_xml + "  </array>\n"
        "  <key>EnvironmentVariables</key>\n  <dict>\n"
        f"    <key>PATH</key><string>{escape(':'.join(seen))}</string>\n"
        "    <key>AGENT_FLOW_TELEMETRY</key><string>false</string>\n"
        "    <key>DO_NOT_TRACK</key><string>1</string>\n"
        "  </dict>\n"
        "  <key>RunAtLoad</key><true/>\n"
        f"  <key>StandardOutPath</key><string>{log}</string>\n"
        f"  <key>StandardErrorPath</key><string>{log}</string>\n"
        "</dict>\n</plist>\n"
    )


def launcher_path(startup_dir: str | None = None) -> Path:
    if common.IS_MAC:
        return common.launch_agents_dir() / f"{LAUNCHER_LABEL_MAC}.plist"
    return (Path(startup_dir) if startup_dir else common.startup_dir()) / LAUNCHER_NAME_WIN


def launcher_text() -> str:
    return plist_text() if common.IS_MAC else vbs_text()


# ---------------------------------------------------------------- prime
def prime_hook_script(package: str, wait_s: float) -> bool:
    """Get agent-flow's own hook.js without letting it touch your settings.

    agent-flow writes hook.js on its first start, but it also rewrites
    settings.json at the same moment (not atomically, and with the Windows
    backslash path that later piles up). So we start it once with a throwaway
    home folder, copy the hook.js it wrote into your real one, and stop it.
    Your settings.json is only ever changed by this installer, after a backup."""
    target = common.hook_script()
    if target.exists():
        return True
    scratch = Path(tempfile.mkdtemp(prefix="agent-flow-prime-"))
    fake_home = scratch / "home"
    work = scratch / "work"
    (fake_home / ".claude").mkdir(parents=True)
    work.mkdir()
    made = fake_home / ".claude" / "agent-flow" / "hook.js"
    print(f"First run: downloading {package} and letting it write its hook script "
          f"(can take up to {int(wait_s)} seconds)...")
    env_extra = {"HOME": str(fake_home), "USERPROFILE": str(fake_home)}
    try:
        proc = starter.launch(str(work), package, 3099, env_extra=env_extra)
        deadline = time.time() + wait_s
        while time.time() < deadline and not made.exists():
            if proc.poll() is not None:
                break
            time.sleep(0.5)
        time.sleep(1.0)
        common.kill_tree(proc.pid)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass
        if made.exists():
            common.atomic_write_text(target, made.read_text(encoding="utf-8"))
    finally:
        try:
            starter.pid_file().unlink()
        except OSError:
            pass
        time.sleep(0.5)
        shutil.rmtree(scratch, ignore_errors=True)
    return target.exists()


# ---------------------------------------------------------------- settings
def apply_hooks(node_path: str | None) -> dict:
    path = common.settings_path()
    before_text = path.read_text(encoding="utf-8-sig") if path.exists() else None
    settings = common.read_settings(path)
    before = common.count_agent_flow(settings)
    new, removed = common.install_agent_flow(settings, common.hook_command(node_path))
    changed = new != settings
    bak = None
    if changed:
        bak = common.backup(path, "agent-flow")
        common.atomic_write_text(path, common.dump_settings(new), common.detect_eol(path))
    return {"path": path, "before": before, "after": common.count_agent_flow(new),
            "removed": removed, "changed": changed, "backup": bak, "existed": before_text is not None}


def remove_hooks() -> dict:
    path = common.settings_path()
    if not path.exists():
        return {"path": path, "removed": 0, "backup": None}
    settings = common.read_settings(path)
    new, removed = common.remove_agent_flow(settings)
    bak = None
    if removed:
        bak = common.backup(path, "agent-flow-uninstall")
        common.atomic_write_text(path, common.dump_settings(new), common.detect_eol(path))
    return {"path": path, "removed": removed, "backup": bak}


# ---------------------------------------------------------------- main
def refuse(msg: str) -> int:
    print("\nSTOPPED - nothing was changed.\n" + msg)
    return 2


def node_help() -> str:
    if common.IS_WIN:
        how = ("Install the LTS version from https://nodejs.org (the green button), or run:\n"
               "    winget install OpenJS.NodeJS.LTS\n")
    elif common.IS_MAC:
        how = "Install the LTS version from https://nodejs.org, or run:\n    brew install node\n"
    else:
        how = "Install Node.js 20 or newer from https://nodejs.org or your package manager.\n"
    return ("agent-flow needs Node.js 18 or newer (20 recommended).\n" + how +
            "Then close this terminal, open a new one, check with:  node --version\n"
            "and run install.py again.")


def do_install(args) -> int:
    print("agent-flow installer (Outliers workspace, piece 1)\n")
    ver = common.node_version() if not os.environ.get("AGENT_FLOW_NPX_CMD") else (99, 0, 0)
    if ver is None:
        return refuse("Node.js was not found.\n" + node_help())
    if ver[0] < 18:
        return refuse(f"Node.js {'.'.join(map(str, ver))} is too old.\n" + node_help())
    print(f"Node.js {'.'.join(map(str, ver))} found.")

    cfg = common.load_config()
    sb_guess, crm_guess = guess_paths()
    sb = args.second_brain or cfg.get("second_brain") or sb_guess
    crm = args.crm or cfg.get("crm") or crm_guess
    if not args.watch_folder:
        sb = ask("Where is your second brain vault?", sb, args.yes)
        crm = ask("Where is your CRM vault?", crm, args.yes)
    default_watch = args.watch_folder or cfg.get("watch_folder") or common_parent([sb, crm]) \
        or str(common.home() / "Documents")
    watch = ask("Which folder should agent-flow watch? It must CONTAIN every vault you run Claude Code in",
                default_watch, args.yes or bool(args.watch_folder))
    if not watch or not Path(watch).is_dir():
        return refuse(f"The watch folder does not exist: {watch}\nCreate it or pass --watch-folder.")
    watch = str(Path(watch).resolve())
    for label, p in (("second brain", sb), ("CRM", crm)):
        if p and Path(p).is_dir() and not common.norm_path(p).startswith(common.norm_path(watch)):
            print(f"Warning: your {label} vault ({p}) is NOT inside {watch}; its sessions will not show.")

    new_cfg = {
        "second_brain": sb,
        "crm": crm,
        "watch_folder": watch,
        "package": args.package or cfg.get("package") or common.DEFAULT_PACKAGE,
        "port": args.port or cfg.get("port") or common.UI_PORT,
        "autostart": not args.no_autostart,
    }
    if new_cfg != cfg:
        common.atomic_write_text(common.config_path(), json.dumps(new_cfg, indent=2) + "\n")
        print(f"Saved settings to {common.config_path()}")

    if not prime_hook_script(new_cfg["package"], args.wait):
        return refuse("agent-flow did not write its hook script "
                      f"({common.hook_script()}). Read {common.logs_dir() / 'agent-flow.log'}.\n"
                      "Your Claude Code settings were not touched.")
    print(f"Hook script present: {common.hook_script()}")

    try:
        res = apply_hooks(args.node_path)
    except (ValueError, json.JSONDecodeError) as exc:
        return refuse(f"Could not read {common.settings_path()}: {exc}\nFix the file, then run again.")
    print(f"\nClaude Code settings: {res['path']}")
    print(f"{'Event':<22}{'before':>8}{'after':>8}")
    for ev in common.EVENTS:
        print(f"{ev:<22}{res['before'][ev]:>8}{res['after'][ev]:>8}")
    extra = sum(max(0, n - 1) for n in res["before"].values())
    if res["changed"]:
        if res["backup"]:
            print(f"Backup taken first: {res['backup']}")
        print(f"Removed {extra} extra copies; each event now has exactly 1.")
        print("The hook line now uses forward slashes, so agent-flow recognises it and will not add "
              "another copy each time it starts.")
    else:
        print("Already correct: 1 copy per event. Nothing changed.")

    if args.no_autostart:
        print("\nNo logon launcher (you chose --no-autostart). Start it by hand with: python start.py")
    else:
        lp = launcher_path(args.startup_dir)
        text = launcher_text()
        if lp.exists() and lp.read_text(encoding="utf-8") == text:
            print(f"\nLogon launcher already in place: {lp}")
        else:
            common.atomic_write_text(lp, text)
            print(f"\nLogon launcher written: {lp}")
            if common.IS_MAC:
                print(f"It runs at your next login. To start it now: launchctl load \"{lp}\"")
    print("Usage tracking: off (AGENT_FLOW_TELEMETRY=false and DO_NOT_TRACK=1 are set by the launcher).")

    if args.start_now:
        print()
        starter.start(watch, new_cfg["package"], int(new_cfg["port"]), args.wait, False, False)
    print(f"\nDone. Open http://127.0.0.1:{new_cfg['port']} once it is running, then start a NEW "
          "Claude Code session inside the watch folder.")
    print("Check your hooks any time with:  python check_hooks.py")
    return 0


def do_uninstall(args) -> int:
    print("agent-flow uninstall\n")
    cfg = common.load_config()
    watch = args.watch_folder or cfg.get("watch_folder")
    if watch:
        starter.stop(watch, quiet=False)
    res = remove_hooks()
    print(f"Removed {res['removed']} agent-flow hook entries from {res['path']}")
    if res["backup"]:
        print(f"Backup taken first: {res['backup']}")
    lp = launcher_path(args.startup_dir)
    if lp.exists():
        if common.IS_MAC:
            subprocess.run(["launchctl", "unload", str(lp)], capture_output=True)
        lp.unlink()
        print(f"Removed logon launcher: {lp}")
    else:
        print("No logon launcher found.")
    print(f"Left in place (upstream's own files, safe to delete by hand): {common.discovery_dir()} "
          f"and {common.home() / '.agent-flow'}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Install agent-flow safely for your Claude Code workspace.")
    ap.add_argument("--yes", action="store_true", help="accept the defaults without asking")
    ap.add_argument("--second-brain", help="path to your second brain vault")
    ap.add_argument("--crm", help="path to your CRM vault")
    ap.add_argument("--watch-folder", help="the folder that contains your vaults")
    ap.add_argument("--package", help=f"npm package to run (default {common.DEFAULT_PACKAGE})")
    ap.add_argument("--port", type=int, help=f"web page port (default {common.UI_PORT})")
    ap.add_argument("--node-path", help="node program to put in the hook (default: the one on PATH)")
    ap.add_argument("--startup-dir", help="Windows Startup folder override (for testing)")
    ap.add_argument("--no-autostart", action="store_true", help="do not add the logon launcher")
    ap.add_argument("--start-now", action="store_true", help="start the server when done")
    ap.add_argument("--wait", type=float, default=180.0, help="seconds to wait for the first download")
    ap.add_argument("--uninstall", action="store_true", help="remove the hook and the launcher")
    args = ap.parse_args(argv)
    return do_uninstall(args) if args.uninstall else do_install(args)


if __name__ == "__main__":
    sys.exit(main())
