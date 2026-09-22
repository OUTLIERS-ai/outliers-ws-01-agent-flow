# What I stole

Everything this kit shows on screen is somebody else's work. Here is whose, and on what terms.

| Prior art | Licence | What we took | What we did NOT take |
|---|---|---|---|
| **agent-flow** by patoles, github.com/patoles/agent-flow, npm package `agent-flow-app` (version 0.9.1 checked 2026-09-22) | Apache License 2.0 | The whole visualiser. You download and run it yourself with `npx agent-flow-app`. We also read its code to learn: the 9 events it hooks, the discovery-file format, the `AGENT_FLOW_TELEMETRY` / `DO_NOT_TRACK` switches, the `AGENT_FLOW_RUNTIME` switch and the `--port` / `--no-open` options. | No code. Not its `hook.js` (it writes that itself on first run), not its web page, not a patched copy. |
| **Claude Code hooks** (docs.anthropic.com, Claude Code settings) | Anthropic's product documentation | The `settings.json` hook shape: `{"hooks": {"<Event>": [{"hooks": [{"type": "command", "command": "...", "timeout": 2}]}]}}` | Nothing else. |
| **Hidden Windows launch with `WScript.Shell.Run cmd, 0, False`** | Standard Windows scripting, no licence | The launcher pattern: the `0` hides the window. | - |
| **launchd** (Apple) | Standard macOS | The logon job format for Macs. | - |

Our own additions, MIT: the forward-slash hook line that stops agent-flow adding a new copy of its hook every time it starts on Windows; the de-duplicating installer with backup, temp-file writes and a clean uninstall; the hook counter; the stale-registration cleaner that checks the process AND the port; the tests.

If we ever ship any of agent-flow's code, even changed, Apache 2.0 requires its licence text to travel with it and our changes to be marked. Pointing you at `npx agent-flow-app` avoids that.
