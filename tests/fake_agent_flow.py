"""A stand-in for `npx agent-flow-app`, used only by the tests.

It copies the upstream start-up behaviour that matters to us:
- writes <home>/.claude/agent-flow/hook.js if missing;
- adds 1 hook entry per event when it cannot see its own marker text
  'agent-flow/hook.js' (upstream 0.9.1 checks with a forward slash, so a Windows
  path with backslashes is never seen and a new copy is added on every start);
- writes a discovery file <code>-<pid>.json and listens until it is killed.
"""
import hashlib
import json
import os
import socket
import sys
import threading
import time
from pathlib import Path

EVENTS = ["SessionStart", "PreToolUse", "PostToolUse", "PostToolUseFailure", "SubagentStart",
          "SubagentStop", "Notification", "Stop", "SessionEnd"]

home = Path.home()
d = home / ".claude" / "agent-flow"
d.mkdir(parents=True, exist_ok=True)
hook = d / "hook.js"
settings_p = home / ".claude" / "settings.json"


def already():
    if not hook.exists() or not settings_p.exists():
        return False
    s = json.loads(settings_p.read_text(encoding="utf-8"))
    return any("agent-flow/hook.js" in h.get("command", "")
               for groups in (s.get("hooks") or {}).values() for g in groups for h in g.get("hooks", []))


if not already():
    if not hook.exists():
        hook.write_text("// fake hook for tests\n", encoding="utf-8")
    s = json.loads(settings_p.read_text(encoding="utf-8")) if settings_p.exists() else {}
    hooks = s.setdefault("hooks", {})
    cmd = f'"node" "{hook}"'  # native separators, like upstream
    for ev in EVENTS:
        lst = [g for g in hooks.get(ev, []) if not any("agent-flow/hook.js" in h.get("command", "")
                                                       for h in g.get("hooks", []))]
        lst.append({"hooks": [{"type": "command", "command": cmd, "timeout": 2}]})
        hooks[ev] = lst
    settings_p.write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8")

port = 3001
if "--port" in sys.argv:
    port = int(sys.argv[sys.argv.index("--port") + 1])


def serve(sock):
    while True:
        try:
            c, _ = sock.accept()
            c.close()
        except OSError:
            return


ui = socket.socket()
ui.bind(("127.0.0.1", port))
ui.listen(5)
hk = socket.socket()
hk.bind(("127.0.0.1", 0))
hk.listen(5)
for s in (ui, hk):
    threading.Thread(target=serve, args=(s,), daemon=True).start()

ws = os.path.realpath(os.getcwd())
code = hashlib.sha256(ws.encode()).hexdigest()[:16]
(d / f"{code}-{os.getpid()}.json").write_text(
    json.dumps({"port": hk.getsockname()[1], "pid": os.getpid(), "workspace": ws}), encoding="utf-8")
while True:
    time.sleep(1)
