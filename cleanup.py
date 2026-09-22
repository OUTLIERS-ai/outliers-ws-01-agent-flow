"""Clear agent-flow's stale server registrations.

Each time the agent-flow server starts it writes a small file into
<home>/.claude/agent-flow/ named <code>-<process number>.json, saying which
folder it watches and which port it listens on. The Claude Code hook reads
these files to find the server.

On Windows the hook never removes files for servers that have ended (its
"is it alive?" check always answers yes). It also sends each event only to the
server with the NARROWEST matching folder. So an old file for a narrower
folder can swallow every event while the real server sits idle.

This script keeps a file only if its process is running AND its port answers.

    python cleanup.py            # remove stale files, report what was kept
    python cleanup.py --dry-run  # only report
"""
from __future__ import annotations

import argparse
import sys

import common


def run(dry_run: bool = False, quiet: bool = False) -> dict:
    files = common.discovery_files()
    removed, kept = [], []
    for info in files:
        if info["live"]:
            kept.append(info)
            continue
        if not dry_run:
            try:
                info["file"].unlink()
            except OSError as exc:
                info["reason"] += f" (could not remove: {exc})"
        removed.append(info)
    if not quiet:
        where = common.discovery_dir()
        print(f"Registration folder: {where}")
        print(f"Found {len(files)} registration file(s): {len(kept)} running, {len(removed)} stale.")
        for info in kept:
            print(f"  KEEP    {info['file'].name}  port {info['port']}  watching {info['workspace']}")
        verb = "WOULD REMOVE" if dry_run else "REMOVED"
        for info in removed:
            print(f"  {verb}  {info['file'].name}  ({info['reason']})")
        live_ws = sorted({i["workspace"] for i in kept if i["workspace"]}, key=len)
        if len(live_ws) > 1:
            print("Note: more than 1 server is running. A session only reports to the one "
                  "watching the narrowest folder that contains it.")
    return {"kept": len(kept), "removed": len(removed), "dry_run": dry_run}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="report only, remove nothing")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    run(dry_run=args.dry_run, quiet=args.quiet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
