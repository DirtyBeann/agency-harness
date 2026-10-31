#!/usr/bin/env python3
"""Validate universal harness setup without printing secrets."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER = re.compile(r"\[ADD_[A-Z0-9_]+\]")


def main() -> int:
    models = ROOT / "config" / "models.yaml"
    example = ROOT / "config" / "models.example.yaml"
    errors: list[str] = []
    warnings: list[str] = []

    if not example.exists():
        errors.append("missing config/models.example.yaml")
    if not models.exists():
        errors.append("missing config/models.yaml - copy from models.example.yaml and fill placeholders")
    else:
        text = models.read_text(encoding="utf-8")
        # Never print file contents (may contain sensitive URLs). Only report placeholder keys.
        left = sorted(set(PLACEHOLDER.findall(text)))
        if left:
            warnings.append(
                "models.yaml still has placeholders: " + ", ".join(left) + " - setup incomplete"
            )
        # Check api_key_env names exist if set (values never printed)
        for line in text.splitlines():
            if "api_key_env:" not in line:
                continue
            name = line.split(":", 1)[1].strip().strip("\"'")
            if not name or name.startswith("[ADD_"):
                continue
            if os.environ.get(name):
                print(f"env {name}: set")
            else:
                warnings.append(f"env {name}: unset (set it outside chat; do not paste the key here)")

    for req in (
        ROOT / "scripts" / "run_state.py",
        ROOT / "scripts" / "binder_smoke.py",
        ROOT / "scripts" / "run_failure_replay.py",
        ROOT / "workflows" / "example-feature-branch.states.json",
    ):
        if not req.exists():
            errors.append(f"missing {req.relative_to(ROOT)}")

    tmp = ROOT / "tmp"
    tmp.mkdir(exist_ok=True)

    if errors:
        print("validate_setup: FAIL")
        for e in errors:
            print(" -", e)
        return 1
    if warnings:
        print("validate_setup: PARTIAL")
        for w in warnings:
            print(" -", w)
        return 2
    print("validate_setup: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
