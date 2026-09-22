# outliers-ws-01-agent-flow

Watch your Claude Code agents hand work to each other, live, in your browser.

```
git clone https://github.com/OUTLIERS-ai/outliers-ws-01-agent-flow; cd outliers-ws-01-agent-flow; python install.py
```

On a Mac, type `python3` instead of `python`. Run the line from your home folder: the logon launcher points at this folder, so keep it where you cloned it.

## What this is

agent-flow is a free, open-source web page by another developer (github.com/patoles/agent-flow, Apache 2.0 licence). It runs on your own computer at http://127.0.0.1:3001 and draws each Claude Code session as a glowing hexagon. When the session starts a subagent, a second hexagon appears with a line between them, and every tool call pops up as a card.

This folder does not contain agent-flow. It contains the safe way to install and run it:

| File | What it does |
|---|---|
| `install.py` | Checks Node.js, asks where your vaults are, runs agent-flow once with a throwaway home folder so it writes its hook script without touching your settings, copies that script in, backs up your Claude Code `settings.json` and makes sure each of the 9 agent-flow events has exactly 1 copy of the hook, then adds a hidden logon launcher. `--uninstall` takes it all out again. |
| `start.py` | Starts agent-flow with no window and usage tracking off, from the folder that contains your vaults. Refuses to start it if your `settings.json` would be wiped (see below). `--stop`, `--status`. |
| `guard.py` | Started by `start.py`. Runs agent-flow on a private port, serves the page on 3001 only to requests addressed to 127.0.0.1 / localhost, and puts `settings.json` back if agent-flow rewrites it in its first 60 seconds. |
| `check_hooks.py` | Counts every hook on every Claude Code event and flags any command registered twice. `--fix` keeps 1 of each after a backup. |
| `cleanup.py` | Deletes stale server registration files, the Windows fault that silently stops events arriving. |
| `common.py` | Shared code for the scripts above. |
| `tests/` | `python -m pytest -q`. They use a temporary home folder and a stand-in for agent-flow; they never touch your real setup. Set `AGENT_FLOW_REAL=1` to also run 4 tests against the real npm package. |
| `guide/GUIDE.md` | The full guide: how it was built, what went wrong, how to fit it to your own system. |

## What you need

- Claude Code, Python 3.8 or newer, Git.
- Node.js 18 or newer (20 recommended). Check with `node --version`. If it is missing, the installer stops, changes nothing, and tells you how to get it.

## Useful commands

```
python install.py --yes                 # accept the defaults it finds
python install.py --watch-folder "C:\Users\<you>\Documents" --yes
python install.py --start-now           # start it straight away instead of at next logon
python install.py --no-autostart        # no logon launcher (removes an existing one); start by hand with start.py
python install.py --port 3002           # another port; a running server moves to it
python install.py --uninstall           # remove the hook and the launcher
python start.py --status
python check_hooks.py
python cleanup.py --dry-run
```

After installing, open http://127.0.0.1:3001 and start a NEW Claude Code session inside the watch folder. Sessions that were already open show nothing, because Claude Code reads hooks when a session starts.

## Faults this fixes

1. **Hook copies pile up on Windows.** agent-flow 0.9.1 checks whether it is already set up by looking for the text `agent-flow/hook.js` in your settings. On Windows the path it writes uses backslashes (`agent-flow\hook.js`), so it never finds its own entry and adds another copy every time it starts. We write the same hook with forward slashes, which Windows accepts and agent-flow recognises. Tested 2026-09-22: 3 stock starts gave 3 copies per event; with our line in place, 2 more starts changed nothing.
2. **Stale registration files.** Each start writes `<home>/.claude/agent-flow/<code>-<process number>.json`. On Windows the hook never removes files for servers that have ended. `start.py` runs `cleanup.py` before every start.
3. **agent-flow can wipe your whole `settings.json` at start.** It runs its own setup every time it starts; if it cannot read the file (a trailing comma, or an invisible byte-order mark that PowerShell and some editors add) it writes a new file containing only its hooks. With a logon launcher that happens silently at logon. `start.py` checks the file first and will not start agent-flow on an unsafe file (the reason goes to the screen and `logs/start.log`; `python start.py --status` repeats it). `guard.py` also keeps the exact bytes and puts them back if agent-flow changes the file anyway. `python install.py` removes a byte-order mark after a backup. Proven with the real package on 2026-09-22 (`tests/test_real_package.py`).
4. **Other websites could read the live page (DNS rebinding).** agent-flow's page ignores the web address a request was sent to. `guard.py` now answers only requests addressed to your own computer. agent-flow's separate event port still accepts events from any web page (a site that guesses the port could draw fake sessions, not read anything); that needs a fix upstream. Stop agent-flow with `python start.py --stop` when you are not watching.
5. **`--stop` could close an unrelated program** after a restart reused the saved process number. The saved record now includes the process start time and stop checks both.

## Usage tracking

agent-flow 0.9.1 sends anonymous usage events (an install code, version, operating system, session length) to its author's server unless `AGENT_FLOW_TELEMETRY=false` or `DO_NOT_TRACK=1` is set. Both are set by `start.py` and by the launcher. If you ever run `npx agent-flow-app` by hand, set them yourself first.

## Licence

Our files: MIT (see `LICENSE`). agent-flow itself: Apache 2.0, downloaded by you from npm, not included here. See `WHAT-I-STOLE.md`.
