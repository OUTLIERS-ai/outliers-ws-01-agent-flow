"""Start or stop the agent-flow server with no window and usage tracking off.

It runs from the folder saved in config.json (the folder that contains your
vaults), because the server only receives events from Claude Code sessions
running inside the folder it was started from.

    python start.py              # start it in the background, then print the address
    python start.py --stop       # stop the server this kit started
    python start.py --status     # say whether it is running
    python start.py --foreground # run and wait (used by the Mac logon job)
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

import cleanup
import common


def servers_for(workspace: str) -> list[dict]:
    want = common.norm_path(workspace)
    return [i for i in common.discovery_files()
            if i["live"] and i["workspace"] and common.norm_path(i["workspace"]) == want]


def pid_file() -> Path:
    return common.logs_dir() / "agent-flow.pid"


def launch(workspace: str, package: str, port: int, foreground: bool = False,
           env_extra: dict | None = None) -> subprocess.Popen:
    cmd = common.npx_command(package) + ["--no-open", "--port", str(port)]
    env = dict(os.environ, **common.QUIET_ENV, **(env_extra or {}))
    common.logs_dir().mkdir(parents=True, exist_ok=True)
    log = open(common.logs_dir() / "agent-flow.log", "ab")
    kwargs = dict(cwd=workspace, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
    if common.IS_WIN:
        kwargs["creationflags"] = common.NO_WINDOW | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        kwargs["start_new_session"] = not foreground
    proc = subprocess.Popen(cmd, **kwargs)
    common.atomic_write_text(pid_file(), str(proc.pid))
    return proc


def start(workspace: str, package: str, port: int, wait_s: float, foreground: bool, quiet: bool) -> int:
    def say(msg):
        if not quiet:
            print(msg)

    if not Path(workspace).is_dir():
        say(f"The watch folder does not exist: {workspace}")
        return 2
    cleanup.run(quiet=True)
    if servers_for(workspace):
        say(f"Already running for {workspace}. Open http://127.0.0.1:{port}")
        return 0
    if common.port_answers(port):
        say(f"Port {port} is already in use by another program. Pick another with --port.")
        return 3
    proc = launch(workspace, package, port, foreground)
    deadline = time.time() + wait_s
    while time.time() < deadline:
        if servers_for(workspace) and common.port_answers(port):
            say(f"agent-flow is running. Open http://127.0.0.1:{port}")
            say("Start a NEW Claude Code session inside the watch folder to see it draw.")
            if foreground:
                return proc.wait()
            return 0
        if proc.poll() is not None:
            say(f"The server stopped straight away. See {common.logs_dir() / 'agent-flow.log'}")
            return 4
        time.sleep(0.5)
    say(f"Still starting after {int(wait_s)} seconds (the first run downloads the package). "
        f"Check http://127.0.0.1:{port} in a minute, or read {common.logs_dir() / 'agent-flow.log'}")
    if foreground:
        return proc.wait()
    return 0


def stop(workspace: str | None, quiet: bool = False) -> int:
    stopped = 0
    targets = servers_for(workspace) if workspace else []
    for info in targets:
        common.kill_tree(info["pid"])
        stopped += 1
    pf = pid_file()
    if pf.exists():
        try:
            pid = int(pf.read_text().strip())
            if common.pid_alive(pid):
                common.kill_tree(pid)
        except ValueError:
            pass
        pf.unlink()
    time.sleep(0.5)
    for info in targets:
        try:
            info["file"].unlink()
        except OSError:
            pass
    if not quiet:
        print(f"Stopped {stopped} agent-flow server(s).")
    return 0


def main(argv=None) -> int:
    cfg = common.load_config()
    ap = argparse.ArgumentParser(description="Start or stop agent-flow quietly.")
    ap.add_argument("--watch-folder", default=cfg.get("watch_folder"))
    ap.add_argument("--package", default=cfg.get("package", common.DEFAULT_PACKAGE))
    ap.add_argument("--port", type=int, default=int(cfg.get("port", common.UI_PORT)))
    ap.add_argument("--wait", type=float, default=180.0, help="seconds to wait for the first start")
    ap.add_argument("--stop", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--foreground", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    if not args.watch_folder:
        print("No watch folder set. Run install.py first, or pass --watch-folder.")
        return 2
    if args.stop:
        return stop(args.watch_folder, args.quiet)
    if args.status:
        live = servers_for(args.watch_folder)
        print(f"{'Running' if live else 'Not running'} for {args.watch_folder}"
              + (f" - http://127.0.0.1:{args.port}" if live else ""))
        return 0 if live else 1
    return start(args.watch_folder, args.package, args.port, args.wait, args.foreground, args.quiet)


if __name__ == "__main__":
    sys.exit(main())
