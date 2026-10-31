#!/usr/bin/env python3
"""Gate REVIEW->SKEPTIC using on-disk latest Review + Security verdicts.

Exit codes:
  0 - ReviewVerdict.decision==pass AND SecurityVerdict.decision==allow (both valid)
  2 - SecurityVerdict.decision==escalate (owner interrupt; escalate != allow)
  1 - deny / fail / revise / missing / invalid / other refuse

Prints one-line reason to stdout.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VERDICTS = ROOT / "ledger" / "verdicts"
KIND_TO_SCHEMA = {
    "review": ROOT / "contracts" / "review_verdict.schema.json",
    "security": ROOT / "contracts" / "security_verdict.schema.json",
}
KIND_TO_CONST = {
    "review": "ReviewVerdict/v1",
    "security": "SecurityVerdict/v1",
}

FORBIDDEN_KEY = re.compile(
    r"(secret|token|password|authorization|api[_-]?key|cookie|webhook.?body|private.?key|raw_tool|transcript|phi)",
    re.I,
)


def say(code: int, reason: str) -> None:
    print(reason)
    raise SystemExit(code)


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as e:
        say(1, f"missing_or_invalid: cannot read {path.name}: {e}")
    if not isinstance(data, dict):
        say(1, f"missing_or_invalid: {path.name} root must be object")
    return data


def validate(kind: str, data: dict, label: str) -> None:
    schema_path = KIND_TO_SCHEMA[kind]
    if not schema_path.is_file():
        say(1, f"missing_or_invalid: schema missing for {kind}")
    expected = KIND_TO_CONST[kind]
    if data.get("schema") != expected:
        say(1, f"missing_or_invalid: {label} schema must be {expected}")
    for k in data:
        if FORBIDDEN_KEY.search(str(k)):
            say(1, f"missing_or_invalid: {label} forbidden key {k}")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: list(e.path))
    if errors:
        e0 = errors[0]
        p = ".".join(str(x) for x in e0.path) or "<root>"
        say(1, f"missing_or_invalid: {label} {p}: {e0.message}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Fail-closed REVIEW+SECURITY gate helper")
    ap.add_argument(
        "--verdicts-dir",
        default=str(DEFAULT_VERDICTS),
        help="Directory containing latest-review.json + latest-security.json",
    )
    ap.add_argument("--review-path", default="", help="Override path to ReviewVerdict JSON")
    ap.add_argument("--security-path", default="", help="Override path to SecurityVerdict JSON")
    args = ap.parse_args()

    vdir = Path(args.verdicts_dir)
    review_path = Path(args.review_path) if args.review_path else vdir / "latest-review.json"
    security_path = Path(args.security_path) if args.security_path else vdir / "latest-security.json"

    if not review_path.is_file():
        say(1, "missing_or_invalid: latest-review.json missing")
    if not security_path.is_file():
        say(1, "missing_or_invalid: latest-security.json missing")

    review = load_json(review_path)
    security = load_json(security_path)
    validate("review", review, "ReviewVerdict")
    validate("security", security, "SecurityVerdict")

    rdec = review.get("decision")
    sdec = security.get("decision")

    if sdec == "escalate":
        say(2, "escalate: SecurityVerdict.decision==escalate (owner interrupt; escalate != allow)")
    if sdec == "deny":
        say(1, "deny: SecurityVerdict.decision==deny")
    if rdec in ("fail", "revise"):
        say(1, f"fail: ReviewVerdict.decision=={rdec}")
    if rdec != "pass" or sdec != "allow":
        say(1, f"fail: unexpected decisions review={rdec!r} security={sdec!r}")

    say(0, "ok: ReviewVerdict.decision==pass && SecurityVerdict.decision==allow")


if __name__ == "__main__":
    main()
