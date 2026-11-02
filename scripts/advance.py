#!/usr/bin/env python3
"""Thin wrapper: check_flags -> run_state (optional propose) -> list next legal edges.

Usage:
  advance.py --workflow example-feature-branch --from REVIEW [--list-next]
  advance.py --workflow example-feature-branch --from REVIEW --to SKEPTIC
    (--strict is the default; --no-strict is dev-only and the binder refuses it
     on gated transitions REVIEW->SKEPTIC and SKEPTIC->DEV_CANDIDATE)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Flags check + binder next edges / propose")
    ap.add_argument("--workflow", required=True, choices=["example-feature-branch", "example-ui-gauntlet"])
    ap.add_argument("--from", dest="from_state", required=True)
    ap.add_argument("--to", dest="to_state", default="")
    ap.add_argument("--transition", dest="when", default="")
    ap.add_argument("--strict", default=True, action=argparse.BooleanOptionalAction,
                    help="dev-only. Verdict gates on gated transitions always run in the "
                         "binder; --no-strict is refused on REVIEW->SKEPTIC and SKEPTIC->DEV_CANDIDATE")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--verdicts-dir", default="")
    ap.add_argument("--flags-dir", default="")
    ap.add_argument("--list-next", action="store_true", help="List next legal edges from the current state")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.list_next and (args.to_state or args.when):
        ap.error("--list-next cannot be combined with --to or --transition")

    flag_cmd = [sys.executable, str(SCRIPTS / "check_flags.py")]
    fp = run(flag_cmd)
    flags_out = (fp.stdout or fp.stderr or "").strip()
    if fp.returncode == 10:
        print(
            json.dumps(
                {
                    "ok": False,
                    "paused": True,
                    "flags": flags_out,
                    "hint": "Clear flags/PAUSE (resume_loop) before advancing",
                },
                ensure_ascii=False,
            )
        )
        raise SystemExit(10)
    if fp.returncode == 20:
        print(
            json.dumps(
                {
                    "ok": False,
                    "payg_confirm": True,
                    "flags": flags_out,
                },
                ensure_ascii=False,
            )
        )
        raise SystemExit(20)
    if fp.returncode != 0:
        print(json.dumps({"ok": False, "flags": flags_out, "rc": fp.returncode}, ensure_ascii=False))
        raise SystemExit(fp.returncode)

    binder = [
        sys.executable,
        str(SCRIPTS / "run_state.py"),
        "--workflow",
        args.workflow,
        "--from",
        args.from_state,
    ]
    if args.flags_dir:
        binder.extend(["--flags-dir", args.flags_dir])
    if args.verdicts_dir:
        binder.extend(["--verdicts-dir", args.verdicts_dir])
    if args.run_id:
        binder.extend(["--run-id", args.run_id])
    if args.dry_run:
        binder.append("--dry-run")
    if not args.strict:
        binder.append("--no-strict")

    if args.to_state or args.when:
        if args.to_state:
            binder.extend(["--to", args.to_state])
        if args.when:
            binder.extend(["--transition", args.when])
        bp = run(binder)
        body = (bp.stdout or "").strip()
        if body:
            print(body)
        if bp.returncode != 0 and bp.stderr:
            sys.stderr.write(bp.stderr)
        raise SystemExit(bp.returncode)

    # No propose: list next legal edges
    list_cmd = binder + ["--list-next"]
    lp = run(list_cmd)
    body = (lp.stdout or "").strip()
    if body:
        print(body)
    else:
        print(json.dumps({"ok": False, "error": (lp.stderr or "list-next failed").strip()}))
    raise SystemExit(lp.returncode)


if __name__ == "__main__":
    main()
