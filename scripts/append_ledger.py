#!/usr/bin/env python3
"""Append a ledger event after JSON Schema validation. Refuse on failure. Rotate on size cap."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "contracts" / "ledger_event.schema.json"
LEDGER_DIR = ROOT / "ledger"
MAX_LEDGER_BYTES = 256 * 1024  # 256 KiB soft cap per active file
MAX_ROTATIONS = 50

FORBIDDEN_KEY = re.compile(
    r"(secret|token|password|authorization|api[_-]?key|cookie|webhook.?body|private.?key|raw_tool|transcript|phi)",
    re.I,
)

SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA)


def refuse(msg: str) -> None:
    raise SystemExit(f"refused: {msg}")


def precheck_keys(event: dict) -> None:
    for k in event:
        if FORBIDDEN_KEY.search(k):
            refuse(f"forbidden key: {k}")
        if k not in SCHEMA.get("properties", {}):
            # additionalProperties false will also catch; fail loud early
            refuse(f"unknown field (redact-by-default): {k}")


def validate(event: dict) -> None:
    precheck_keys(event)
    errors = sorted(VALIDATOR.iter_errors(event), key=lambda e: list(e.path))
    if errors:
        e0 = errors[0]
        path = ".".join(str(p) for p in e0.path) or "<root>"
        refuse(f"schema {path}: {e0.message}")


def active_path(run_id: str) -> Path:
    """Pick current shard for run_id, rotating when over size cap."""
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    base = LEDGER_DIR / f"{run_id}.jsonl"
    if not base.exists() or base.stat().st_size < MAX_LEDGER_BYTES:
        return base
    for i in range(1, MAX_ROTATIONS + 1):
        shard = LEDGER_DIR / f"{run_id}.{i}.jsonl"
        if not shard.exists() or shard.stat().st_size < MAX_LEDGER_BYTES:
            return shard
    refuse(f"ledger rotation exhausted for {run_id} (>{MAX_ROTATIONS} shards at {MAX_LEDGER_BYTES} bytes)")


def append(event: dict, run_id: str) -> Path:
    validate(event)
    line = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
    line_bytes = (line + "\n").encode("utf-8")
    if len(line_bytes) > MAX_LEDGER_BYTES:
        refuse(f"single event exceeds ledger cap ({len(line_bytes)} > {MAX_LEDGER_BYTES})")
    path = active_path(run_id)
    # If adding this line would exceed cap and file non-empty, rotate first
    if path.exists() and path.stat().st_size + len(line_bytes) > MAX_LEDGER_BYTES and path.stat().st_size > 0:
        # force next shard
        if path.name == f"{run_id}.jsonl":
            path = LEDGER_DIR / f"{run_id}.1.jsonl"
        else:
            # run_id.N.jsonl
            stem = path.name[len(run_id) + 1 : -6]  # between run_id. and .jsonl
            n = int(stem) + 1
            if n > MAX_ROTATIONS:
                refuse(f"ledger rotation exhausted for {run_id}")
            path = LEDGER_DIR / f"{run_id}.{n}.jsonl"
        if path.exists() and path.stat().st_size + len(line_bytes) > MAX_LEDGER_BYTES:
            refuse(f"rotated shard still full: {path.name}")
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate+append a redact-by-default ledger event")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--state", required=True)
    ap.add_argument("--event", required=True)
    ap.add_argument("--lane", default="platform")
    ap.add_argument("--role", default="")
    ap.add_argument("--pool-id", default="")
    ap.add_argument("--gateway", default="unknown")
    ap.add_argument("--model-id", default="")
    ap.add_argument("--verdict", default="")
    ap.add_argument("--gap", default="")
    ap.add_argument("--artifact", action="append", default=[])
    ap.add_argument("--bar-ref", default="")
    ap.add_argument("--notes", default="")
    ap.add_argument("--piece-id", default="")
    ap.add_argument("--round", type=int, default=None)
    ap.add_argument("--json", dest="json_file", default="", help="Optional path to full event JSON (overrides flags)")
    args = ap.parse_args()

    if args.json_file:
        event = json.loads(Path(args.json_file).read_text(encoding="utf-8-sig"))
        if "run_id" not in event:
            event["run_id"] = args.run_id
    else:
        event = {
            "schema": "LedgerEvent/v1",
            "run_id": args.run_id,
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "state": args.state,
            "event": args.event,
            "lane": args.lane,
        }
        if args.role:
            event["role"] = args.role
        if args.pool_id:
            event["pool_id"] = args.pool_id
        if args.gateway:
            event["gateway"] = args.gateway
        if args.model_id:
            event["model_id"] = args.model_id
        if args.verdict:
            event["verdict"] = args.verdict
        if args.gap:
            event["gap"] = args.gap
        if args.artifact:
            event["artifact_paths"] = args.artifact[:16]
        if args.bar_ref:
            event["bar_ref"] = args.bar_ref
        if args.notes:
            event["notes"] = args.notes
        if args.piece_id:
            event["piece_id"] = args.piece_id
        if args.round is not None:
            event["round"] = args.round

    if event.get("schema") != "LedgerEvent/v1":
        refuse("schema must be LedgerEvent/v1")

    path = append(event, event["run_id"])
    print(path)


if __name__ == "__main__":
    main()
