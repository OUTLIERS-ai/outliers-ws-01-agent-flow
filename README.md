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
| `install.py` | Checks Python 3.11+ and Node.js 22+, asks where your vaults are, runs agent-flow once with a throwaway home folder so it writes its hook script without touching your settings, copies that script in, backs up your Claude Code `settings.json` and makes sure each of the 9 agent-flow events has exactly 1 copy of the hook, then adds a hidden logon launcher. `--uninstall` takes it all out again. |
| `start.py` | Starts agent-flow with no window and usage tracking off, from the folder that contains your vaults. Refuses to start it if your `settings.json` would be wiped (see below). When a start fails it names the cause in 1 sentence. `--stop`, `--status`. |
| `guard.py` | Started by `start.py`. Runs agent-flow on a private port, serves the page on 3001 only to requests addressed to 127.0.0.1 / localhost, and puts `settings.json` back if agent-flow rewrites it in its first 60 seconds. |
| `check_hooks.py` | Counts every hook on every Claude Code event and flags any command registered twice. `--fix` keeps 1 of each after a backup. |
| `cleanup.py` | Deletes stale server registration files, the Windows fault that silently stops events arriving, and ends a second server left watching the same folder. |
| `common.py` | Shared code for the scripts above. |
| `tests/` | 45 checks, run with `python -m pytest -q`. They use a temporary home folder and a stand-in for agent-flow; they never touch your real setup. Set `AGENT_FLOW_REAL=1` to also run 4 checks against the real npm package; without it those 4 are skipped. Measured from a fresh copy on 2026-09-23: 45 passed, 4 skipped. |
| `guide/GUIDE.md` | The full guide: how it was built, what went wrong, how to fit it to your own system. |

## What you need

- Claude Code, Python 3.11 or newer, Git. Check with `python --version` (Mac: `python3 --version`).
- Node.js 22 or newer (24 recommended). Check with `node --version`.

`install.py` tests both version numbers before it touches anything. If either is missing or too old it stops, changes nothing, and tells you how to get it. The floors are dated: Python 3.8 stopped getting security fixes on 2024-10-07, Node.js 18 on 2025-04-30 and Node.js 20 on 2026-04-30 (checked 2026-09-22).

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
6. **A start that failed told you nothing you could use.** It printed "The server stopped straight away" and a path to 20 lines of Node.js text. `start.py` now reads the last 30 lines of `logs/agent-flow.log`, matches the known shapes (port taken, no internet with the package not saved yet, Node.js missing or too old, package name wrong) and prints 1 plain sentence. `python start.py --status` repeats it.
7. **The private port was picked, let go, then handed to agent-flow**, and Windows could give that number away in between. It failed 1 start in 34 on 2026-09-22. If agent-flow now dies within 12 seconds and the port is answering to something else, the guard picks another number and tries again, 3 times in all.
8. **Closing agent-flow by force left a second server running.** `cleanup.py` counted folders, so 2 servers watching 1 folder looked like 1. It now counts servers, ends the older server, and `start.py` ends a server left behind before it starts a new one.
9. **`check_hooks.py` called an empty `settings.json` "OK" while `start.py` refused it.** Both now use the same reader, so they cannot disagree.

## Usage tracking

agent-flow 0.9.1 sends anonymous usage events (an install code, version, operating system, session length) to its author's server unless `AGENT_FLOW_TELEMETRY=false` or `DO_NOT_TRACK=1` is set. Both are set by `start.py` and by the launcher. If you ever run `npx agent-flow-app` by hand, set them yourself first.

## Licence

Our files: MIT (see `LICENSE`). agent-flow itself: Apache 2.0, downloaded by you from npm, not included here. See `WHAT-I-STOLE.md`.
