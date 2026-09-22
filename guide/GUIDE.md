---
title: "agent-flow: Watch Your Agents Hand Work to Each Other, Live"
subtitle: A free screen that draws every Claude Code session and subagent as it works, installed with our fixes so it cannot wipe your Claude Code settings
repo: https://github.com/OUTLIERS-ai/outliers-ws-01-agent-flow
piece: 1
---

## What it is

agent-flow is a free web page that runs on your own computer. Open it in your browser at http://127.0.0.1:3001 (an address that only your own computer can open; 3001 is the number the page answers on) while Claude Code is working, and you see a dark screen with a glowing hexagon. That hexagon is your Claude Code session. When the session hands a job to a subagent (a second Claude that does 1 task and reports back), a second hexagon appears and a line is drawn between them. Every tool call, such as reading a file or running a command, pops up as a small card beside the agent that made it.

![A Claude Code session (top) has just handed a job to a subagent (bottom right). Made-up demo vault, taken 2026-09-22: the names in it, such as Sam the bookkeeper, are invented.](img/agentflow-2-agents.png)

Along the top of the page are tabs, 1 per Claude Code session running on your computer. Each tab is titled with the first words of that session's opening message. Top right shows how many agents are running, an estimate of tokens used (tokens are the units Claude's usage is counted and billed in) and an estimated cost. Along the bottom is a timeline with a LIVE marker and a Review button that replays what happened. There is also a sound button in the top right corner, which mutes the page's small sound effects.

agent-flow was written by another developer and published free, with its code open for anyone to read and change (the Apache 2.0 licence; code at github.com/patoles/agent-flow). It is listed as `agent-flow-app` on npm, the public store of Node.js programs, version 0.9.1 checked on 2026-09-22. It also comes as an add-on for the VS Code code editor. Our download does not contain agent-flow. It contains 5 small Python scripts: an installer (`install.py`), a start-and-stop script (`start.py`), 2 checking scripts (`check_hooks.py` and `cleanup.py`) and `guard.py`, a small program that sits between agent-flow and your browser. Together they set agent-flow up safely, because agent-flow installed on its own, unchanged, has faults on Windows that kept coming back from 2026-06-12 to 2026-09-16, and 1 fault on every computer that can wipe your Claude Code settings.

This is piece 1 of 4 in the agent workspace. Install them in order: 1 agent-flow, 2 FleetView, 3 ProjectForge, 4 Jeeves. Each one also works on its own.

### Words used in this guide

| Word | What it means here |
|---|---|
| Session | 1 conversation with Claude Code, running in 1 terminal window. |
| Subagent | A second Claude that your session starts to do 1 job and report back. |
| Tool call | 1 action Claude takes, such as reading a file or running a command. |
| Token | The unit Claude's usage is counted in. 1 token is roughly 3 quarters of a word. |
| Hook | A command Claude Code runs by itself every time a given event happens, such as a tool about to run. Hooks are listed in `settings.json`. |
| Terminal | The text window where you type commands: PowerShell on Windows, Terminal on a Mac. |
| Server | The agent-flow program running in the background on your computer, which draws the page. |
| 127.0.0.1 and localhost | 2 ways of writing "this computer". An address that starts with either of them opens only on your own computer. |
| Port | The number after the colon in an address such as http://127.0.0.1:3001. It picks out which program on your computer answers. In this set of 4: agent-flow 3001, FleetView 3010, ProjectForge 3020, Jeeves 4040. |
| Node.js, npm, npx | Node.js runs programs written in JavaScript; npm is its public store of programs; npx downloads a program from npm and runs it. |
| settings.json | Claude Code's settings file, in the `.claude` folder inside your home folder. |
| Repo | A project's folder of code, kept on GitHub. `git clone` copies it to your computer. |
| Watch folder | The folder agent-flow listens to; only sessions started inside it appear. |
| Exit code | The number a program hands back when it finishes; 0 means all went well. |

## Why you would want it

When you run agents, most of the work is invisible. You type a request and later an answer arrives. You do not see which subagents were called, in what order, or which files they opened. That matters in 3 situations:

- **Building an agent.** Its instructions say it calls 3 specialists. Does it? On this screen you see every subagent it really starts and every file it really reads.
- **Something is slow or expensive.** You see the moment a session starts 5 subagents at once, or reads the same file 4 times.
- **Showing your work.** A client or a video viewer understands "the agents handed the job along" in 5 seconds when they watch it happen.

![What you can read off the screen. The yellow numbers are ours, drawn on a made-up demo run.](img/page-labelled.png)

agent-flow only reads what your agents do; it cannot change it.

## How we built it

This is how Ashley set agent-flow up on his own Windows PC, what broke, and what we kept. Every date and count below was read from his files, settings backups and logs on 2026-09-22.

![Ashley's own agent-flow, run once with no window on 2026-09-22 for this guide. The 3 tabs along the top are his real Claude Code sessions, titled with the first words of each prompt.](img/original-agentflow-live.png)

agent-flow is 1 of 4 screens Ashley built around his agents. The other 3 each have their own guide in this set of 4: FleetView, ProjectForge and Jeeves.

![Ashley's real screens side by side, 2026-09-22: Jeeves (a personal-assistant screen over his second brain), ProjectForge (a board of work cards his agents pick up), FleetView (every running Claude Code session and its cost on 1 page) and agent-flow (bottom right).](img/original-full-cockpit.png)

Claude Code lets you register a **hook**: a command it runs by itself every time a given event happens, such as "a tool is about to be used" or "a subagent has started". agent-flow registers a small script, `hook.js`, on 9 kinds of event. Each time 1 of them happens, Claude Code runs `hook.js` and hands it a description of the event. The script looks in the folder `<your home>/.claude/agent-flow/` for small files that say where the agent-flow server (the agent-flow program running in the background, which draws the page) is listening, and sends the event there. The server updates its picture and your browser redraws.

![How 1 event travels. Step 4, guard.py (our program between agent-flow and your browser), is our addition from 2026-09-22: it refuses requests from other websites. The security section below explains why.](img/event-path.png)

### 2026-06-12: install day

- Installed with `npx -y agent-flow-app` (the `-y` answers yes to the download question). `npx` comes with Node.js; it downloads a Node.js program and runs it in 1 go. On its first run the package wrote `hook.js` and added it to 9 kinds of event in Claude Code's `settings.json` file: SessionStart (a session opens), PreToolUse and PostToolUse (before and after each tool call), PostToolUseFailure (a tool call fails), SubagentStart and SubagentStop, Notification (Claude Code shows a message), Stop (Claude finishes a reply) and SessionEnd (a session closes).
- **Windows fix 1, the launch folder.** The server remembers the folder it was started from, and only accepts events from Claude Code sessions running inside that folder. Started from the wrong place, it shows nothing. So it was set to start from the Documents folder, the parent of every vault.
- **Start at logon, with no window.** A small Windows script file, `agent-flow.vbs`, went into the Windows Startup folder (Windows runs everything in that folder when you log in). It runs `npx -y agent-flow-app --no-open`, and `--no-open` stops it opening a browser tab.
- **Every session on 1 screen, tried and undone.** Ashley wanted every session on 1 screen instead of 1 tab each. We changed agent-flow's own code so it sent every session to the same screen. The data looked right, and it was reported as done without anyone looking at the screen. Ashley's reply: "that hasn't worked - It's not working at all." agent-flow's drawing code supports exactly 1 main hexagon per screen, so 6 main hexagons stacked on the same spot and their labels garbled. agent-flow was put back exactly as its author published it. Since then, every change to a screen is checked with a screenshot, never by reading the data behind it.
- The 1-screen wish went to a different tool, FleetView, which is piece 2 of 4.
- A backup of `settings.json` taken at 17:00 that day already had **5 copies** of the agent-flow hook on every event. The next day's backup had 4.

### Windows fix 2: old files pointing at servers that had stopped (date not recorded)

Each time the server starts it writes a file named `<code>-<process number>.json` (the process number is the number Windows gives each running program) into `<home>/.claude/agent-flow/`, saying which port it listens on and which folder it watches. The hook is meant to delete files for servers that have stopped. On Windows its "is this server still alive?" check is written to always answer yes. Worse, when several files match a session's folder, the hook sends only to the server watching the **smallest** folder that contains the session (Documents\Second Brain is smaller than Documents, because it sits inside it). So if an old file names a server for a smaller folder, and that server has stopped, every event goes to it and is lost, the real server gets nothing, and the screen stays empty. The fix was to delete the old files and keep the one whose server is running. 13 such files were still in that folder on 2026-09-22, dated 2026-06-12 to 2026-08-06.

### 2026-07-09 to 2026-09-16: the hook copies pile up

![Copies of the agent-flow hook on each kind of event, from settings backups and checks of the settings file.](img/hook-copies-over-time.png)

- **2026-07-09:** a check of the settings file found the hook registered about 10 times on every event.
- **2026-07-19:** `npx` downloaded the newer agent-flow, version 0.9.1.
- **2026-07-27:** Ashley: "Instances keep opening on my PC." The settings file had 112 hook entries in total; agent-flow's was on every event 12 times. Each tool call started about 27 small command-window programs, and each flashed a window on screen. Every hook was cut to 1 copy per event and command: 112 entries down to 13.
- **2026-08-18:** the copies had come back: 3 per event.
- **2026-09-16:** a backup shows 3 per event. On 2026-09-22 the file had 2 copies per event, and all of them were removed that day. No written record was found of the drop from 3 to 2.

At the time, why the copies piled up was not recorded. While building this kit on 2026-09-22 we read agent-flow 0.9.1's own set-up code and found a cause. Before adding its hook, agent-flow checks whether it is already there by searching your settings for the text `agent-flow/hook.js`, with a forward slash. On Windows the path it writes uses backslashes: `agent-flow\hook.js`. The search never matches its own entry, so **every time the server starts, it adds another copy to all 9 kinds of event**. We tested it in a test folder: 3 starts gave 3 copies per event. A server that starts at every logon, plus starts by hand during fixes, matches every rise in the chart. We cannot prove it was the only cause, because nobody logged each start.

Our fix changes only the direction of the slashes: the installer writes the same hook with forward slashes (`C:/Users/<you>/.claude/agent-flow/hook.js`). Windows accepts forward slashes, and agent-flow now recognises its own entry and leaves your settings alone. Tested the same day: with our line in place, 2 more starts changed nothing.

### The usage-tracking finding

agent-flow 0.9.1 sends anonymous usage events (an install code, its version, your operating system, session length) to a server run by its author, unless 1 of 2 switches is set before it starts: `AGENT_FLOW_TELEMETRY=false` or `DO_NOT_TRACK=1`. These are environment variables: settings a program reads from Windows or macOS when it starts. The GitHub page summary says tracking is off by default; the code switches it on. On Ashley's PC, 4 such events were logged between 2026-07-19 and 2026-08-06, because the file that started his agent-flow at logon set neither switch. Ours sets both.

### 2026-08-06: switched off

At 17:25 on 2026-08-06 the Startup entry for agent-flow was switched off in Windows' Startup apps list, in the same minute as the FleetView dashboard. Who did it and why was not written down. Ashley's own written record of what went wrong says, for 2026-09-22, that these screens were "stopped not deleted" when his work changed direction. The hooks were left in place, so every tool call still started Node.js (the program that runs agent-flow's scripts) once, found no server and quit. Our uninstall removes those hooks.

### 2026-09-22: what a security check of our own kit found

Before this guide went out, the kit was tested by someone trying to break it, using the real agent-flow package in a test home folder. 3 faults were found and all 3 are fixed in the version you download.

- **agent-flow could wipe your Claude Code settings at logon.** agent-flow runs its own set-up every time it starts. If it cannot read `settings.json`, it throws the whole file away and writes a new one containing only its 9 hooks: your permission rules, your blocked commands, your model choice and every other hook, gone, with no backup. 2 ordinary slips make the file unreadable to it: a comma after the last item (easy to leave after a hand edit), and an invisible marker at the very start of the file called a byte-order mark, which Windows PowerShell and some editors add when they save. With agent-flow starting by itself at logon, this happened without any message the next time you logged in. **Our fix:** `start.py` now checks the file before every start and does not start agent-flow if the file is unsafe; it says why on screen and in `logs/start.log`. As a second layer, a new file, `guard.py`, keeps an exact copy of your settings before agent-flow starts, watches the file for the first 60 seconds, and puts your copy back if agent-flow changed it. Tested with the real package: with a comma after the last item or a byte-order mark, the file stays byte-for-byte the same.
- **Stop could close an unrelated program.** `start.py --stop` used to stop whatever program had the process number saved when agent-flow last started. After a restart, Windows can give that number to any program, including Claude Code or your browser. **Our fix:** the saved record now includes the moment the program started, and stop only acts when both match.
- **Other websites could read the page.** agent-flow's page streams your live conversation: your prompts, Claude's replies, file names and commands. It answers every request that reaches it, whatever web address the browser thinks it is using. A website you visit can trick your browser into sending its requests to your own computer, and then read that stream while you browse. **Our fix:** agent-flow now answers on a second port that only `guard.py` talks to, and `guard.py` shows you the page on 3001. It answers only requests addressed to this computer (`127.0.0.1`, `localhost` and `[::1]` are 3 ways of writing "this computer"). Anything else is refused.

> **Warning:** 1 exposure remains, and it is agent-flow's, not ours to fix. The separate port that receives events from `hook.js` accepts them from any web page, so a website that guesses that port number (it changes at every start) could draw fake sessions and fake tool calls on your screen. It cannot read anything through that port. If you are not watching agent-flow, stop it with `python start.py --stop`. A real fix needs a change in agent-flow itself (github.com/patoles/agent-flow).

![The page as guard.py (our program between agent-flow and your browser) passes it to your browser, from a made-up session on 2026-09-22: 1 agent, 5,000 tokens. "orchestrator" is the name agent-flow gives the main session.](img/page-through-guard.png)

### What we kept for you

- agent-flow exactly as its author published it, downloaded by your own computer from npm. We changed none of its code.
- The hook entry in settings.json written with forward slashes (/), so agent-flow recognises it and never adds another copy.
- A small file in your Startup folder that starts agent-flow when you log in, with no window, from the folder that contains your vaults, with usage tracking off.
- `cleanup.py`, which deletes leftover registration files from servers that have stopped AND ends a second server left watching the same folder, run automatically before every start.
- `check_hooks.py`, a count of every hook on every event.
- `guard.py`, which puts settings.json back if agent-flow wipes it and refuses page requests from other websites (both found when we tried to break the kit on 2026-09-22).
- A start that fails telling you why in 1 sentence, instead of pointing at a log full of Node.js text (added 2026-09-23 after a reliability run of 34 starts found the 1 that failed was undecodable).

## Pros and cons

| | Pros | Cons |
|---|---|---|
| Cost | Free, with its code open to read. Uses no Claude tokens itself. | Every tool call starts Node.js once, to run `hook.js` (it ends within 1.5 seconds and never makes Claude wait). It does this even when the server is off, until you uninstall. |
| Setup | About 1 minute with our installer, plus the first download. | Needs Node.js, which most people do not have yet. |
| What you see | Subagents appear the moment they start; every tool call is a card; Review replays a run. | 1 session per tab. There is no single screen with every session: our 2026-06-12 attempt to add that screen failed. FleetView (piece 2 of 4) is that screen. |
| Accuracy | Tool calls and subagents come straight from Claude Code's own events. | Token counts and costs are estimates. On Ashley's PC they disagreed with FleetView (the session-and-cost screen in piece 2 of 4) for the same session. |
| Privacy | The page only listens on your own computer, and guard.py (our program between agent-flow and your browser) refuses requests addressed to anything but your own computer. | Tab titles show the first words of your prompts, so take care when screen-sharing. Usage tracking is on unless switched off (our start-at-logon file switches it off). A website that guesses a port number can still draw fake sessions on your screen. |
| Safety | Our kit will not start agent-flow on a settings file it would wipe, and puts the file back if it changes anyway. | agent-flow's own set-up still runs at every start; our checks run before and after it; they do not stop it running. |
| Windows | Our kit fixes the 2 known Windows faults: the start folder, and leftover registration files that swallow events. Closing agent-flow by force (from Task Manager, or a crash) used to leave a second server running and sending the same events twice; `cleanup.py` now counts servers rather than folders, ends the extra one, and says so. | agent-flow's own registration files are still written by agent-flow, so a server closed by force leaves its file behind until the next `python start.py` or `python cleanup.py`. |

![The cost of having the hook installed: 1 short-lived program per tool call, whether or not the page is open.](img/per-tool-call.png)

## Before you start

| You need | How to check | If it is missing |
|---|---|---|
| Claude Code | `claude --version` | You have it from earlier Outliers Accelerator sessions. |
| Python 3.11 or newer | `python --version` (Mac: `python3 --version`) | python.org. `install.py` tests this and stops if it is older, because Python 3.8 stopped getting security fixes on 2024-10-07 and 3.10 stops on 2026-10-31. |
| Git | `git --version` | git-scm.com |
| Node.js 22 or newer | `node --version` | Version 24 is the one to get. Node.js 18 stopped getting security fixes on 2025-04-30 and Node.js 20 on 2026-04-30, so `install.py` stops on anything below 22. Windows: the LTS installer (long-term support, the stable version) from nodejs.org, or `winget install OpenJS.NodeJS.LTS` (winget is Windows' built-in install command). Mac: nodejs.org or `brew install node` (if you have Homebrew, a Mac install tool). Then open a NEW terminal (the text window where you type commands), because a terminal opened before the install cannot find Node.js. |
| Port 3001 free (the number the page is served on) | Open http://127.0.0.1:3001 in a browser; it should fail to load | Install with `python install.py --port 3002` instead, then use 3002 wherever this guide says 3001. |

![The 4 checks as they printed on a test PC on 2026-09-22. Your version numbers can be higher.](img/version-checks.png)

You also need to know where your second brain vault and your CRM vault live. The installer finds them for you in 1 of these ways: small pointer files called `.outliers-sb` and `.outliers-crm` in your home folder (the installers from earlier Outliers Accelerator sessions left them there), a folder with an `.obsidian` folder inside it (that is what makes a folder an Obsidian vault) up to 2 levels under your home or Documents folder, or, for the CRM, a vault whose name contains crm, pipeline, sales or clients, or a folder at `C:\Users\<you>\CRM`.

## Install it

1. Open a terminal. Windows: press the Windows key, type `PowerShell`, press Enter. Mac: open Terminal. It opens in your home folder, which is where all 4 downloads in this set go.
2. Run the clone and install line:

```
git clone https://github.com/OUTLIERS-ai/outliers-ws-01-agent-flow; cd outliers-ws-01-agent-flow; python install.py
```

   On a Mac use `python3`. Keep the folder where it lands: the small file that starts agent-flow when you log in points at it.
3. Answer 3 questions. Press Enter to accept the suggestion in square brackets.
   - Where is your second brain vault?
   - Where is your CRM vault?
   - Which folder should agent-flow watch? It suggests the folder that contains both vaults. It must contain every folder you run Claude Code in, or those sessions will not show.

   If a question shows no suggestion, paste the full path of that vault (in File Explorer, click the address bar and copy it). No CRM vault yet? Press Enter to leave it blank.
4. Wait for the first run. The installer downloads agent-flow and starts it once, with no window, pointed at a temporary empty folder that stands in for your home folder, so it writes its own `hook.js` without touching your settings. It copies that script into your `.claude/agent-flow` folder and stops it. This can take up to 3 minutes on a slow connection. No login is needed.
5. Read the table the installer prints at the end: 1 row per kind of event. Every event should show `1` in the "after" column. If you had old copies, the "before" column shows how many, and a dated backup of your settings is named on screen. The file that starts agent-flow at logon is `outliers-agent-flow.vbs` in your Startup folder; that is the name you see in Windows' Startup apps list.

![What a successful install prints, retaken 2026-09-23 with the 2 version checks it now runs first. Paths shortened to C:\Users\<you>; the demo ran in a made-up home folder, and "Demo CRM" is an invented vault.](img/install-output.png)

6. Start it now: `python start.py`. From now on it also starts by itself, with no window, each time you log in.
7. Open http://127.0.0.1:3001. You see "Waiting for agent session".

![The page before any session has started.](img/agentflow-waiting.png)

8. Open a **new** Claude Code session inside one of your vaults. Sessions that were already open show nothing, because Claude Code reads hooks only when a session starts. Ask it for something that uses a subagent, for example: "Use a subagent to list the notes in my People folder, then summarise them in 2 lines." A hexagon appears, then a second hexagon with a line to it. Nothing after 30 seconds? Check the session was started AFTER step 6 and inside the watch folder shown by `python start.py --status`, then see the "When it goes wrong" table at the end of this guide.

![The main session (top left) starting a subagent. The orange label is the job it was given.](img/agentflow-subagent-starting.png)

9. Run `python check_hooks.py`. It should end with `RESULT: OK`.

> **Tip:** to remove everything later, run `python install.py --uninstall`. It stops the server, takes a backup, removes the 9 hook entries, and deletes the file that starts agent-flow at logon. Your settings go back to how they were (byte for byte, when the first install's backup is still there). If you had no settings file before, an empty settings file (containing only `{}`) is left. The folder `.claude\agent-flow` stays; you may delete it by hand.

## Using it day to day

Every command below runs inside the downloaded folder. In a new terminal, type `cd outliers-ws-01-agent-flow` first.

- **Leave the page open in a browser tab** while you work. Switch tabs at the top to follow a different session.
- **Press Review** on the bottom bar to replay a run that has finished.
- **The Files, Chat, Cost and Timeline buttons** top right open side panels: which files were touched, the conversation, the estimated cost, and a timeline of every call.
- **Check your hooks once a week:** `python check_hooks.py`. Anything other than 1 per event means something else has been writing to your settings.
- **If the page goes quiet:** run `python start.py --stop`, then `python start.py`, then open a new Claude Code session.
- **If a start fails,** it now tells you why in 1 sentence on screen: the port was taken, the internet is not reachable and agent-flow is not saved on this computer yet, Node.js is missing or too old, or the package name in `config.json` is wrong. `python start.py --status` repeats that sentence later.
- **Stopping:** `python start.py --stop` says "Stopped agent-flow." or "agent-flow was not running. Nothing to stop." Check any time with `python start.py --status`.
- **If you move your vaults**, run `python install.py` again and give the new watch folder. The suggestion in square brackets is your OLD watch folder, so type the new one. If the server was running, the installer stops it and starts it again for the new folder.
- **Screen-sharing:** close the tab or pick a demo session first. Tab titles show the start of your prompts.
- **When you are not watching,** stop it with `python start.py --stop`. While it is stopped, no website can reach the page.

![Checking, stopping, and stopping again, as it prints.](img/status-stop.png)

![A subagent at work: each card is 1 tool call it made, here reading notes and listing a folder.](img/agentflow-subagent-working.png)

## Fit it to your own AI system

Each idea below comes with a prompt you can paste into Claude Code, opened in the `outliers-ws-01-agent-flow` folder unless it says otherwise.

![Idea 1 in a picture: the watch folder must contain every vault whose sessions you want to see.](img/watch-folder.png)

1. **See your second brain AND your CRM in 1 place.** The server only hears sessions inside its watch folder. If your CRM lives at `C:\Users\<you>\CRM` and your second brain in `Documents`, the only folder containing both is your home folder.

```
Read config.json. Tell me whether my second brain vault and my CRM vault are both inside watch_folder. If not, run install.py again with --watch-folder set to the nearest folder that contains both, and show me the before and after.
```

2. **Watch your content system write a batch of posts.** Run whatever agents or scripts write your posts from a folder inside the watch folder, open agent-flow, and start a batch. You will see which steps call subagents and which run as plain code.

```
The agents or scripts that write my posts live at <path>. Check whether that folder is inside the watch_folder in config.json. If it is not, tell me the smallest change: move the folder, or widen the watch folder. Do not move anything without asking.
```

3. **Check an agent you are building really does what its instructions say.** Open the agent's file, list what it claims to call, run it with agent-flow open, and compare.

```
Read ~/.claude/agents/<agent-name>.md. List every subagent, tool and file it says it uses, as a checklist. I will run it now with agent-flow open and tell you what cards appeared. Then mark each checklist line as seen, not seen, or seen but not listed.
```

4. **Give every subagent a real name.** A subagent started without a name from your agents folder (`~/.claude/agents/`, where each agent has its own file) shows as a hexagon with no name. Named agents make the picture readable.

```
Search my second brain's CLAUDE.md and my agent files for places that start a subagent with a generic type such as general-purpose. List each one and suggest which named agent from ~/.claude/agents/ should be used instead. Change nothing yet.
```

5. **Keep a permanent log.** agent-flow keeps no history once the server stops. Add a second, separate hook that appends each event to a dated file, then summarise a day into your second brain.

```
Add ONE new hook to my Claude Code settings.json on SubagentStart and SubagentStop that appends the event as 1 JSON line to ~/.claude/agent-events/YYYY-MM-DD.jsonl. Use a Python script run with pythonw.exe so no window opens. Take a dated backup of settings.json first, write it with a temp file and os.replace, and run python check_hooks.py afterwards to prove every event still has 1 copy of each command.
```

6. **Stop the pointless program starts when the server is off.** If you only use agent-flow sometimes, every tool call still starts Node.js for nothing. Remove the hooks when you stop, and put them back when you start.

```
Write stop_all.py and start_all.py in this folder. stop_all.py runs start.py --stop and then removes the agent-flow hooks using common.remove_agent_flow, with a backup. start_all.py puts the hooks back with common.install_agent_flow and runs start.py. Add tests using a temporary home folder, like the ones in tests/, and run them with python -m pytest -q.
```

7. **Run it only when you want it.** Skip the file that starts agent-flow when you log in, and make a desktop shortcut instead. `--no-autostart` also removes that file if you already have it.

```
Run python install.py --no-autostart and check that outliers-agent-flow.vbs is no longer in my Startup folder. Then create a desktop shortcut called "Agent screen" that runs start.py with pythonw.exe (Windows) so no window appears, and a second one that runs start.py --stop.
```

8. **Capture footage for content.** Record the page during a real multi-agent run: it makes short video of "the agents working" for a post.

```
Write capture.py: open http://127.0.0.1:3001 in headless Playwright at 1600 by 900, take a screenshot every 2 seconds until I press Ctrl+C, and save them numbered into a folder called captures with today's date. No visible browser window.
```

9. **Weekly hook check without a window.** Run the duplicate check once a week, with no window, and write the result into your second brain's inbox only when something is wrong. `check_hooks.py` ends with exit code 1 when it finds a duplicate and 2 when settings.json cannot be read (an exit code is the number a program hands back when it finishes; 0 means all well).

```
Create a Windows scheduled task that runs check_hooks.py once a week on Monday at 09:00 through pythonw.exe, hidden. If the exit code is 1 or 2, write a short note into <second brain>/Inbox/ named YYYY-MM-DD hook check.md with the output. Do not run it more often than weekly.
```

## Every command and setting

![What is in the download, and what each file does.](img/download-folder.png)

**install.py** (every option can be combined with the others)

| Option | What it does |
|---|---|
| (none) | Asks you 3 questions, then installs. |
| `--yes` | Accepts every suggestion without asking. |
| `--second-brain <path>`, `--crm <path>` | Gives the vault paths instead of answering the questions. |
| `--watch-folder <path>` | Sets the watch folder and skips the 3 questions. The installer warns you if a vault is not inside it. |
| `--port <number>` | The page's port (default 3001). A running server is moved to the new port. |
| `--no-autostart` | Does not add the file that starts agent-flow at logon; also removes that file if you already have it. |
| `--start-now` | Starts the server at the end, so you can skip step 6. |
| `--uninstall` | Stops the server, removes the 9 hooks (backup first) and the file that starts agent-flow at logon. |
| `--package`, `--node-path`, `--wait`, `--startup-dir` | Advanced and for testing: which agent-flow version to run (default `agent-flow-app@0.9.1`), which Node.js program goes into the hook, how many seconds to wait for the first download (default 180), and a different Startup folder. |

**start.py**

| Option | What it does |
|---|---|
| (none) | Checks settings.json, deletes leftover registration files, starts agent-flow with no window, prints the address. |
| `--stop` | Stops the server this kit started. |
| `--status` | Says "Running" or "Not running", and if the last start was refused or failed, the 1-sentence reason. Exit code 0 when running, 1 when not. |
| `--port`, `--watch-folder`, `--package`, `--wait` | Override `config.json` for this run only. |
| `--foreground`, `--quiet` | Used by the files that start agent-flow at logon: wait instead of returning (the Mac login job), and print nothing (the Windows file). |


**check_hooks.py**: `--fix` keeps 1 copy of each repeated hook after a dated backup; `--settings <file>` checks a different settings file. Exit codes: 0 all well, 1 duplicates found, 2 the file cannot be read.

**cleanup.py**: `--dry-run` only reports what it would delete or end; `--quiet` prints nothing. It removes registration files for servers that have stopped, and when 2 servers are watching the same folder (what closing agent-flow by force leaves behind) it ends the older server and takes its file away.

**Files the kit makes while it runs**

- `config.json`: your 2 vault paths, the watch folder, the agent-flow version, the port and whether the start-at-logon file is on. `config.example.json` shows what the file looks like.
- `logs/start.log`: the kit's own notes, such as a refused start or a settings file put back.
- `logs/agent-flow.log`: agent-flow's own output. `start.py` reads its last 30 lines to work out the 1-sentence reason it prints when a start fails; open it yourself for the full text.
- `logs/agent-flow.pid` (PID stands for process ID, the number Windows gives the running program): that number and the server's start time, so `--stop` finds it and nothing else.
- Settings backups next to `settings.json`: `settings.json.bak-agent-flow-<date>` (before install), `.bak-agent-flow-uninstall-<date>`, `.bak-hookdedupe-<date>` (before `--fix`) and `.bak-agent-flow-undo-<date>` (agent-flow's rewritten version, kept when `guard.py` put yours back).
- The file that starts agent-flow at logon: on Windows `outliers-agent-flow.vbs` in your Startup folder; on a Mac a login job, `~/Library/LaunchAgents/com.outliers.agent-flow.plist`, which runs at your next login (to start it now: `launchctl load` followed by that path).

**Worth knowing**

- If you set `CLAUDE_CONFIG_DIR` (a setting that tells Claude Code to keep its settings in a different folder), the installer uses that folder. agent-flow itself always uses `<home>/.claude`.
- agent-flow also watches OpenAI Codex (OpenAI's coding assistant) unless the environment variable `AGENT_FLOW_RUNTIME=claude` is set. It does no harm if you do not use Codex.
- The kit's automatic self-checks run with `python -m pytest -q`. They use a made-up home folder and a fake agent-flow, so your real settings are never touched. 4 more run against the real agent-flow if you first set the environment variable `AGENT_FLOW_REAL=1`.

## When it goes wrong

| What you see | Why | Fix |
|---|---|---|
| The page says "Waiting for agent session" forever | The session was already open when the server started, or it runs outside the watch folder. | Open a NEW session inside the watch folder. Check the folder with `python start.py --status` and `config.json`. |
| Still nothing after a new session | A leftover file from an old agent-flow server, pointing at a folder deeper inside your watch folder, is taking the events (Windows only). | `python cleanup.py`, then `python start.py --stop` and `python start.py`, then a new session. |
| "agent-flow was NOT started, to protect your Claude Code settings" | settings.json has a typing error, or an invisible marker at its very start that some editors add (a byte-order mark); agent-flow would have replaced the whole file. | Error with a line number: open settings.json at that line, fix it (a comma after the last item is the usual cause), save. Byte-order mark: run `python install.py`, which removes it after a backup. Then `python start.py`. |
| The page never loads after logging in | The settings check refused to start agent-flow at logon, or the start failed, and nothing was on screen to tell you. | `python start.py --status` prints the 1-sentence reason; fix as it says, then `python start.py`. |
| "agent-flow did not start", then a sentence | The start failed. The sentence names the cause: the port was taken, the internet could not be reached and agent-flow is not saved on this computer yet, Node.js is missing or too old, or the package name in `config.json` is wrong. | Do what the sentence says. For a taken port, run `python start.py` again. `logs/agent-flow.log` has the full text if you want it. |
| "Ended 1 agent-flow server(s) left behind when the last one was closed by force" | agent-flow was closed from Task Manager, or the computer shut down without `python start.py --stop`, so agent-flow outlived the program that started it. | Nothing to do. It has already been ended. Use `python start.py --stop` rather than Task Manager and it will not happen again. |
| Command windows flash on screen on every tool call | Hook copies have piled up. Before this kit, agent-flow added 1 more copy each time it started on Windows. | `python check_hooks.py --fix`, then `python install.py` to rewrite the line with forward slashes. |
| "Port 3001 is already in use" | Another program uses that port. | `python install.py --port 3002`, then `python start.py`, then open http://127.0.0.1:3002. |
| The installer stops: Node.js not found | Node.js is not installed, or the terminal was opened before installing it. | Install it (see Before you start), open a NEW terminal, run again. Nothing was changed. |
| The installer stops: could not read settings.json | The file has a typing error in it. `check_hooks.py` shows the same fault with the line and column. | Open settings.json at that line, fix the error, run again. Your Claude Code settings were not changed. |
| `check_hooks.py` says settings.json is empty | The file is there but has nothing in it. agent-flow cannot read an empty file, so at its next start it would replace it with a file that has only its own 9 hooks in it. `start.py` refuses to start it for the same reason. | `python install.py`. It writes the 9 hooks into the file properly, after a backup. |
| A file called `settings.json.bak-agent-flow-undo-<date>` appeared | agent-flow rewrote your settings after starting and `guard.py` (our program between agent-flow and your browser) put your version back. The file is agent-flow's version, kept for you to look at. | Nothing to do. `logs/start.log` records when it happened. |
| Counts and costs differ from another dashboard | agent-flow's token and cost figures are estimates. | Treat them as a rough guide, not a bill. |
| A change you made to the screen "should work" but looks wrong | The change was checked by reading its data. On 2026-06-12 our attempt to show every session on 1 screen had the right data while the screen showed 6 hexagons stacked on 1 spot. | Take a screenshot and look at it before calling it done. |

![A settings file with a comma after its last item: the start is refused, `--status` repeats the reason, and `check_hooks.py` says the same words. The last block is an EMPTY settings.json, which the 2 used to disagree about until 2026-09-23. Made-up home folder, 2026-09-23.](img/start-refused.png)

![A start that failed, saying why in 1 sentence instead of pointing at a log. Staged on 2026-09-23 by taking the port agent-flow needed; the words are the ones the kit really prints.](img/start-failed-says-why.png)

![Closing agent-flow by force leaves a second server on the same folder. `cleanup.py` counts servers rather than folders, ends the older server, and the next start says so. Made-up home folder, 2026-09-23.](img/leftover-server-ended.png)

> **Warning:** do not run `npx agent-flow-app` by hand while this kit is installed. You get 2 servers, sessions report only to the one watching the smallest folder, and a hand-started copy runs without our settings check, so it can wipe settings.json. Use `python start.py` instead.

## Download

The repository: https://github.com/OUTLIERS-ai/outliers-ws-01-agent-flow

```
git clone https://github.com/OUTLIERS-ai/outliers-ws-01-agent-flow; cd outliers-ws-01-agent-flow; python install.py
```

Then `python start.py` and open http://127.0.0.1:3001.

![The 4 steps from download to a working screen.](img/download-steps.png)

agent-flow itself: github.com/patoles/agent-flow (Apache 2.0 licence). Our 5 scripts: MIT licence. Both are free licences: you may use and change the code.
