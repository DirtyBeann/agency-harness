#!/usr/bin/env python3
"""Exit codes for loop runners: 0=ok continue, 10=paused, 20=payg confirm required."""
from __future__ import annotations
import argparse, sys
from pathlib import Path

FLAGS = Path(__file__).resolve().parents[1] / "flags"

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entering-payg", action="store_true", help="Caller is about to use a pool-payg-* model")
    args = ap.parse_args()
    if (FLAGS / "PAUSE").exists():
        print("PAUSE: flags/PAUSE present - halt between rounds")
        sys.exit(10)
    if args.entering_payg and (FLAGS / "payg_confirm.on").exists():
        print("PAYG_CONFIRM: flags/payg_confirm.on present - ask owner once before pool-payg-*")
        sys.exit(20)
    print("OK")
    sys.exit(0)

if __name__ == "__main__":
    main()
