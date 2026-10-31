#!/usr/bin/env python3
"""Fail-closed JSON Schema validation for harness verdict contracts.

Usage:
  validate_verdict.py --kind review|security|skeptic|governor --file path.json
Exit 0 on pass, 1 on refuse. Mirrors append_ledger.py Draft202012Validator style.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
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


def refuse(msg: str) -> None:
    raise SystemExit(f"refused: {msg}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate a harness verdict JSON file (fail-closed)")
    ap.add_argument("--kind", required=True, choices=sorted(KIND_TO_SCHEMA.keys()))
    ap.add_argument("--file", required=True, help="Path to verdict JSON")
    args = ap.parse_args()

    schema_path = KIND_TO_SCHEMA[args.kind]
    if not schema_path.is_file():
        refuse(f"schema missing: {schema_path}")

    try:
        data = json.loads(Path(args.file).read_text(encoding="utf-8-sig"))
    except Exception as e:
        refuse(f"json parse: {e}")

    if not isinstance(data, dict):
        refuse("root must be object")

    expected = KIND_TO_CONST[args.kind]
    if data.get("schema") != expected:
        refuse(f"schema must be {expected} (got {data.get('schema')!r})")

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if errors:
        e0 = errors[0]
        path = ".".join(str(p) for p in e0.path) or "<root>"
        refuse(f"schema {path}: {e0.message}")

    print(f"ok: {args.kind} {expected}")


if __name__ == "__main__":
    main()
