"""Runs agent-flow behind 2 safety checks. start.py starts this; you never run it by hand.

1. Your settings.json. agent-flow 0.9.1 runs its own setup each time it starts and,
   if it cannot read settings.json, writes a new one holding only its hooks. start.py
   refuses to start it when the file is not safe; this file also keeps a copy of the
   exact bytes before agent-flow starts, watches the file for the first 60 seconds,
   and if agent-flow rewrote it, keeps the rewritten version as
   settings.json.bak-agent-flow-undo-<date> and puts yours back.

2. The page address. agent-flow's page streams your live Claude Code conversation and
   answers any request, whatever web address the browser thinks it is talking to. A
   website can use that to read the stream (the trick is called DNS rebinding: a web
   address that first points at the website, then at your own computer). So agent-flow
   runs on a private port, and this file serves the page on your port (3001), passing
   on only requests addressed to 127.0.0.1, localhost or [::1]. Anything else gets 403.

    python guard.py --workspace <folder> --package agent-flow-app@0.9.1 --port 3001
"""
from __future__ import annotations

import argparse
import datetime as _dt
import http.client
import os
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import common

WATCH_SETTINGS_S = 60


def log(msg: str) -> None:
    common.logs_dir().mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(common.logs_dir() / "start.log", "a", encoding="utf-8") as fh:
        fh.write(f"[{stamp}] [guard] {msg}\n")


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def allowed_hosts(port: int) -> set[str]:
    return {f"127.0.0.1:{port}", f"localhost:{port}", f"[::1]:{port}"}


def make_handler(public_port: int, private_port: int):
    ok_hosts = allowed_hosts(public_port)

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"  # each answer ends by closing, which suits the live stream

        def log_message(self, *a):
            pass

        def refuse(self, code: int, text: str) -> None:
            body = text.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            host = (self.headers.get("Host") or "").strip().lower()
            if host not in ok_hosts:
                return self.refuse(403, f"agent-flow only answers at http://127.0.0.1:{public_port}\n")
            try:
                up = http.client.HTTPConnection("127.0.0.1", private_port, timeout=30)
                up.connect()
                sock = up.sock  # kept: http.client lets go of it once a reply is read to the end
                up.request("GET", self.path, headers={"Host": f"127.0.0.1:{private_port}",
                                                      "Accept": self.headers.get("Accept", "*/*")})
                resp = up.getresponse()
            except OSError:
                return self.refuse(502, "agent-flow is still starting. Refresh in a few seconds.\n")
            ctype = resp.getheader("Content-Type", "")
            try:
                self.send_response(resp.status)
                for k in ("Content-Type", "Cache-Control"):
                    v = resp.getheader(k)
                    if v:
                        self.send_header(k, v)
                if "text/event-stream" in ctype:
                    self.end_headers()
                    self.wfile.flush()
                    sock.settimeout(None)  # the stream can be quiet for minutes
                    while True:
                        chunk = resp.read1(65536)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        self.wfile.flush()
                else:
                    body = resp.read()
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
            except OSError:
                pass  # the browser tab closed
            finally:
                up.close()

        def do_POST(self):
            self.refuse(405, "Not allowed\n")

        do_PUT = do_DELETE = do_PATCH = do_POST

    return Handler


def run(workspace: str, package: str, port: int, wait_s: float) -> int:
    settings = common.agent_flow_settings_path()
    before = settings.read_bytes() if settings.exists() else None
    private = free_port()
    cmd = common.npx_command(package) + ["--no-open", "--port", str(private)]
    env = dict(os.environ, **common.QUIET_ENV)
    out = open(common.logs_dir() / "agent-flow.log", "ab")
    kwargs = dict(cwd=workspace, env=env, stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT)
    if common.IS_WIN:
        kwargs["creationflags"] = common.NO_WINDOW
    log(f"starting agent-flow for {workspace} (private port {private}, page on {port})")
    child = subprocess.Popen(cmd, **kwargs)
    started = time.time()

    def check_settings():
        nonlocal before
        if before is None or not settings.exists():
            return
        now = settings.read_bytes()
        if now == before:
            return
        if common.settings_changed_by_agent_flow(before, now):
            kept = common.put_settings_back(before, settings)
            log(f"agent-flow rewrote {settings}; put back your version. Its version is kept as {kept}")
        else:
            before = now  # a normal edit by you or Claude Code: accept it

    server = None
    try:
        while time.time() - started < wait_s and child.poll() is None:
            check_settings()
            if common.port_answers(private):
                break
            time.sleep(0.3)
        if child.poll() is not None:
            check_settings()
            log(f"agent-flow stopped straight away (exit code {child.returncode})")
            return 4
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(port, private))
        except OSError as exc:
            log(f"could not serve the page on port {port}: {exc}")
            return 3
        server.daemon_threads = True
        threading.Thread(target=server.serve_forever, daemon=True).start()
        log(f"page ready at http://127.0.0.1:{port}")
        while child.poll() is None:
            if time.time() - started < WATCH_SETTINGS_S:
                check_settings()
            time.sleep(0.5)
        log(f"agent-flow ended (exit code {child.returncode})")
        return child.returncode or 0
    finally:
        if server is not None:
            server.shutdown()
        if child.poll() is None:
            common.kill_tree(child.pid)
        out.close()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run agent-flow behind the settings and address checks.")
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--package", default=common.DEFAULT_PACKAGE)
    ap.add_argument("--port", type=int, default=common.UI_PORT)
    ap.add_argument("--wait", type=float, default=180.0)
    ap.add_argument("--kit-dir", help="where config.json and logs/ live (default: this folder)")
    a = ap.parse_args(argv)
    if a.kit_dir:
        from pathlib import Path

        common.KIT_DIR = Path(a.kit_dir)
    return run(a.workspace, a.package, a.port, a.wait)


if __name__ == "__main__":
    sys.exit(main())
