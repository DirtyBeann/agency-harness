#!/usr/bin/env python3
"""Validate + write an on-disk harness verdict. Refuse secrets / invalid schema.

Usage:
  write_verdict.py --kind review|security|skeptic|governor --json-file PATH
                   [--out-dir DIR]

Writes {kind}-{UTC timestamp}.json and updates latest-{kind}.json (copy).
Exit 0 on write; 1 on refuse. Mirrors validate_verdict.py + append_ledger.py posture.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
DEFAULT_OUT = ROOT / "ledger" / "verdicts"
sys.path.insert(0, str(SCRIPTS))
import binder_rules  # shared secret-shape patterns (kept in sync with contracts)

KIND_TO_SCHEMA = {
    "review": ROOT / "contracts" / "review_verdict.schema.json",
    "security": ROOT / "contracts" / "security_verdict.schema.json",
    "skeptic": ROOT / "contracts" / "skeptic_verdict.schema.json",
    "governor": ROOT / "contracts" / "governor_verdict.schema.json",
}
KIND_TO_CONST = {
    "review": "ReviewVerdict/v1",
    "security": "SecurityVerdict/v1",
    "skeptic": "SkepticVerdict/v1",
    "governor": "GovernorVerdict/v1",
}

FORBIDDEN_KEY = re.compile(
    r"(secret|token|password|authorization|api[_-]?key|cookie|webhook.?body|private.?key|raw_tool|transcript|phi)",
    re.I,
)


def refuse(msg: str) -> None:
    raise SystemExit(f"refused: {msg}")


def walk_forbid(obj, path: str = "") -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if FORBIDDEN_KEY.search(str(k)):
                refuse(f"forbidden key: {k}")
            walk_forbid(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk_forbid(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        if binder_rules.looks_secret(obj):
            refuse(f"secret-shaped value at {path or '<root>'}")


def validate(kind: str, data: dict) -> None:
    schema_path = KIND_TO_SCHEMA[kind]
    if not schema_path.is_file():
        refuse(f"schema missing: {schema_path}")
    if not isinstance(data, dict):
        refuse("root must be object")
    expected = KIND_TO_CONST[kind]
    if data.get("schema") != expected:
        refuse(f"schema must be {expected} (got {data.get('schema')!r})")
    walk_forbid(data)
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if errors:
        e0 = errors[0]
        p = ".".join(str(x) for x in e0.path) or "<root>"
        refuse(f"schema {p}: {e0.message}")


def write_latest(src: Path, latest: Path) -> None:
    """Prefer symlink; fall back to copy on platforms without symlink privilege."""
    if latest.exists() or latest.is_symlink():
        latest.unlink()
    try:
        os.symlink(src.name, latest)
    except OSError:
        shutil.copy2(src, latest)


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate and write on-disk harness verdict")
    ap.add_argument("--kind", required=True, choices=sorted(KIND_TO_SCHEMA.keys()))
    ap.add_argument("--json-file", required=True, help="Path to verdict JSON to validate+write")
    ap.add_argument(
        "--out-dir",
        default=str(DEFAULT_OUT),
        help=f"Verdict output directory (default: {DEFAULT_OUT})",
    )
    args = ap.parse_args()

    try:
        data = json.loads(Path(args.json_file).read_text(encoding="utf-8-sig"))
    except Exception as e:
        refuse(f"json parse: {e}")

    validate(args.kind, data)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stamped = out_dir / f"{args.kind}-{ts}.json"
    latest = out_dir / f"latest-{args.kind}.json"
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    stamped.write_text(payload, encoding="utf-8", newline="\n")
    write_latest(stamped, latest)
    print(stamped)
    print(latest)


if __name__ == "__main__":
    main()
