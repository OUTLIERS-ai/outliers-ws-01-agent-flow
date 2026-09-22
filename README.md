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
| `start.py` | Starts agent-flow with no window and usage tracking off, from the folder that contains your vaults. `--stop`, `--status`. |
| `check_hooks.py` | Counts every hook on every Claude Code event and flags any command registered twice. `--fix` keeps 1 of each after a backup. |
| `cleanup.py` | Deletes stale server registration files, the Windows fault that silently stops events arriving. |
| `common.py` | Shared code for the 4 scripts above. |
| `tests/` | `python -m pytest -q`. They use a temporary home folder and a stand-in for agent-flow; they never touch your real setup. |
| `guide/GUIDE.md` | The full guide: how it was built, what went wrong, how to fit it to your own system. |

## What you need

- Claude Code, Python 3.8 or newer, Git.
- Node.js 18 or newer (20 recommended). Check with `node --version`. If it is missing, the installer stops, changes nothing, and tells you how to get it.

## Useful commands

```
python install.py --yes                 # accept the defaults it finds
python install.py --watch-folder "C:\Users\<you>\Documents" --yes
python install.py --start-now           # start it straight away instead of at next logon
python install.py --no-autostart        # no logon launcher; start by hand with start.py
python install.py --uninstall           # remove the hook and the launcher
python start.py --status
python check_hooks.py
python cleanup.py --dry-run
```

After installing, open http://127.0.0.1:3001 and start a NEW Claude Code session inside the watch folder. Sessions that were already open show nothing, because Claude Code reads hooks when a session starts.

## Two faults this fixes

1. **Hook copies pile up on Windows.** agent-flow 0.9.1 checks whether it is already set up by looking for the text `agent-flow/hook.js` in your settings. On Windows the path it writes uses backslashes (`agent-flow\hook.js`), so it never finds its own entry and adds another copy every time it starts. We write the same hook with forward slashes, which Windows accepts and agent-flow recognises. Tested 2026-09-22: 3 stock starts gave 3 copies per event; with our line in place, 2 more starts changed nothing.
2. **Stale registration files.** Each start writes `<home>/.claude/agent-flow/<code>-<process number>.json`. On Windows the hook never removes files for servers that have ended. `start.py` runs `cleanup.py` before every start.

## Usage tracking

agent-flow 0.9.1 sends anonymous usage events (an install code, version, operating system, session length) to its author's server unless `AGENT_FLOW_TELEMETRY=false` or `DO_NOT_TRACK=1` is set. Both are set by `start.py` and by the launcher. If you ever run `npx agent-flow-app` by hand, set them yourself first.

## Licence

Our files: MIT (see `LICENSE`). agent-flow itself: Apache 2.0, downloaded by you from npm, not included here. See `WHAT-I-STOLE.md`.
