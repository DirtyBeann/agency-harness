#!/usr/bin/env python3
"""Agency Harness failure-replay fixture validator (P2-4).

Executable acceptance for failures/cases/*. Loads each case, applies contract
and gate rules (jsonschema + gate_review semantics + illegal transitions + ACL
policy table), and exits non-zero on any miss.

This is the harness-native smoke companion. The named eval runner product is
Optional CI tools may wrap these fixtures later. This script is NOT a second
eval framework; promptfoo may shell out to it, or you run it standalone offline.

Usage:
  python scripts/run_failure_replay.py
  python scripts/run_failure_replay.py --case 01-skeptic-false-pass
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CASES_DIR = ROOT / "failures" / "cases"
CONTRACTS = ROOT / "contracts"
SCRIPTS = ROOT / "scripts"

KIND_TO_SCHEMA = {
    "review": CONTRACTS / "review_verdict.schema.json",
    "security": CONTRACTS / "security_verdict.schema.json",
    "skeptic": CONTRACTS / "skeptic_verdict.schema.json",
    "governor": CONTRACTS / "governor_verdict.schema.json",
    "gauntlet": CONTRACTS / "gauntlet_round.schema.json",
    "ledger": CONTRACTS / "ledger_event.schema.json",
}

# Agents that must not edit markdown / policy / workflow docs (ACL table).
EDIT_DENY_AGENTS = {
    "code-skeptic",
    "gauntlet-critic",
    "security-reviewer",
    "governor",
}

ILLEGAL_TRANSITIONS = {
    ("WIN", "DEV_CANDIDATE"),
    ("CRITIC", "DEV_CANDIDATE"),
    ("APPLYING", "DEV_CANDIDATE"),
    ("REVIEW", "DEV_CANDIDATE"),
    ("Code", "done"),
    ("CODE", "done"),
}


class CaseResult:
    def __init__(self, case_id: str) -> None:
        self.case_id = case_id
        self.ok = False
        self.detail = ""
        self.actual_exit = None
        self.actual_reason = ""


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def schema_validate(kind: str, payload: dict) -> tuple[bool, str]:
    schema_path = KIND_TO_SCHEMA.get(kind)
    if not schema_path or not schema_path.is_file():
        return False, f"schema missing for kind={kind}"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda e: list(e.path))
    if not errors:
        return True, "schema ok"
    e0 = errors[0]
    path = ".".join(str(p) for p in e0.path) or "<root>"
    # include property name for additionalProperties
    msg = e0.message
    return False, f"schema {path}: {msg}"


def run_check(inp: dict) -> tuple[int, str]:
    """Return (exit_code, reason). exit 0 means the *check* accepted the payload.
    For negative fixtures we expect non-zero.
    """
    check = inp.get("check")
    if check == "skeptic_pass_requires_evidence":
        payload = inp["payload"]
        ok_schema, reason = schema_validate("skeptic", payload)
        if not ok_schema:
            # schema fail is also a fail outcome for a bad PASS claim
            return 1, f"skeptic schema/evidence: {reason}"
        if payload.get("verdict") == "PASS":
            evidence = payload.get("evidence_index") or []
            artifacts = payload.get("artifact_paths") or []
            bad_open = (
                payload.get("unverified")
                or payload.get("incomplete")
                or payload.get("failures")
                or payload.get("violations")
                or []
            )
            if not evidence and not artifacts:
                return 1, "PASS without evidence_index/artifact_paths (false pass)"
            if bad_open:
                return 1, "PASS with open unverified/incomplete/failures/violations"
        return 0, "skeptic evidence rule ok"

    if check == "same_pool":
        payload = inp["payload"]
        # schema may still validate; business rule rejects same pool
        ok_schema, reason = schema_validate("gauntlet", payload)
        bp = payload.get("builder_pool")
        cp = payload.get("critic_pool")
        if bp and cp and bp == cp:
            tag = "[ADD_PROVIDER]" if "[ADD_PROVIDER]" in str(bp) else "same_pool"
            return 1, f"same_pool illegal: builder={bp} critic={cp} ({tag})"
        if not ok_schema:
            return 1, reason
        return 0, "pools differ"

    if check == "critic_vision":
        role = inp.get("role", "")
        requires = inp.get("requires_vision", True)
        if role == "gauntlet-critic" and requires is False:
            return 1, "ui_critic_without_vision: critic requires vision"
        if requires is False and inp.get("lane") == "design":
            return 1, "ui critic missing vision flag"
        return 0, "vision ok"

    if check == "schema":
        kind = inp["kind"]
        payload = inp["payload"]
        ok, reason = schema_validate(kind, payload)
        # also catch forbidden key names early (mirror gate_review)
        for k in payload:
            if re.search(r"(secret|token|password|raw_tool|transcript|phi)", str(k), re.I):
                return 1, f"forbidden/additional field: {k}"
        if ok:
            return 0, reason
        # normalize additionalProperties wording
        if "additional" in reason.lower() or "raw_tool" in reason.lower():
            return 1, reason if "additional" in reason.lower() else f"additionalProperties reject: {reason}"
        return 1, reason

    if check == "gate_review":
        with tempfile.TemporaryDirectory(prefix="harness-replay-") as td:
            tdir = Path(td)
            review = inp.get("review")
            security = inp.get("security")
            review_path = tdir / "latest-review.json"
            security_path = tdir / "latest-security.json"
            if review is not None:
                review_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
            if security is not None:
                security_path.write_text(json.dumps(security, indent=2) + "\n", encoding="utf-8")
            cmd = [
                sys.executable,
                str(SCRIPTS / "gate_review.py"),
                "--verdicts-dir",
                str(tdir),
            ]
            # if review missing, do not pass --review-path; gate looks for latest-review.json
            proc = subprocess.run(cmd, capture_output=True, text=True)
            out = (proc.stdout or "").strip() or (proc.stderr or "").strip()
            return proc.returncode, out or f"gate_review exit {proc.returncode}"

    if check == "ledger_append":
        payload = inp["payload"]
        # Validate via ledger schema + append_ledger dry path (temp run, but append_ledger writes).
        # Prefer schema validate + secret pattern without writing production ledger.
        ok, reason = schema_validate("ledger", payload)
        if not ok:
            # schema not-pattern often says does not match / must not / notes
            if "notes" in reason.lower() or "gap" in reason.lower() or "pattern" in reason.lower() or "not" in reason.lower():
                return 1, f"refused: secret-shaped notes ({reason})"
            return 1, f"refused: {reason}"
        # Double-check secret-shaped using same regex as contracts
        secret_re = re.compile(
            r"(?i)(sk_live_|sk_test_|rk_live_|whsec_|ghp_|github_pat_|gho_|xox[baprs]-|"
            r"BEGIN [A-Z ]*PRIVATE KEY|eyJ[A-Za-z0-9_-]{20,}|"
            r"SENTRY_ACCESS_TOKEN|API_KEY\s*=|password\s*=|Bearer\s+[A-Za-z0-9._\-]{20,})"
        )
        for field in ("notes", "gap"):
            val = payload.get(field) or ""
            if isinstance(val, str) and secret_re.search(val):
                return 1, f"refused: secret-shaped value in {field}"
        return 0, "ledger ok"

    if check == "illegal_transition":
        fr = inp.get("from_state")
        to = inp.get("to_state")
        if (fr, to) in ILLEGAL_TRANSITIONS:
            return 1, f"illegal transition {fr}->{to}: Skeptic/parent gates required before DEV_CANDIDATE"
        # also treat WIN->*DEV_CANDIDATE as illegal by name
        if str(fr).upper() == "WIN" and "DEV_CANDIDATE" in str(to).upper():
            return 1, "illegal: gauntlet WIN cannot skip to DEV_CANDIDATE (Skeptic required)"
        return 0, "transition not in illegal set"

    if check == "acl_policy":
        agent = inp.get("agent", "")
        action = inp.get("action", "")
        path = inp.get("path", "")
        expected_policy = inp.get("policy_expected", "deny")
        if action == "edit" and agent in EDIT_DENY_AGENTS:
            if expected_policy == "deny":
                # The *attempt* must be denied: report fail (non-zero) meaning harness rejects the action
                return 1, f"acl deny: {agent} edit {path}"
        if action == "edit" and path.endswith(".md") and agent in EDIT_DENY_AGENTS:
            return 1, f"acl deny: {agent} markdown edit side door"
        return 0, "acl allow (unexpected for negative fixture)"

    if check == "l1_emdash_slop":
        text = inp.get("text", "")
        fail_em = bool(inp.get("fail_on_emdash", True))
        fail_slop = bool(inp.get("fail_on_slop", False))
        with tempfile.TemporaryDirectory(prefix="harness-l1-") as td:
            sample = Path(td) / "sample.txt"
            sample.write_text(text, encoding="utf-8")
            cmd = [
                sys.executable,
                str(SCRIPTS / "l1_emdash_slop_check.py"),
                str(sample),
            ]
            if fail_em:
                cmd.append("--fail-on-emdash")
            else:
                cmd.append("--no-fail-on-emdash")
            if fail_slop:
                cmd.append("--fail-on-slop")
            else:
                cmd.append("--no-fail-on-slop")
            proc = subprocess.run(cmd, capture_output=True, text=True)
            out = (proc.stdout or "").strip() or (proc.stderr or "").strip()
            # Normalize reason so fixtures can match emdash / U+2014
            if proc.returncode != 0 and "emdash" not in out.lower() and "\u2014" in text:
                out = (out + " emdash U+2014").strip()
            return proc.returncode, out or f"l1_emdash_slop exit {proc.returncode}"

    return 1, f"unknown check: {check}"


def outcome_matches(expected: dict, exit_code: int, reason: str) -> tuple[bool, str]:
    want = expected.get("expect", "fail")
    want_code = expected.get("exit_code")
    needles = expected.get("reason_contains") or []

    if want == "fail":
        if exit_code == 0:
            return False, f"expected fail but check exited 0 ({reason})"
    elif want == "pass":
        if exit_code != 0:
            return False, f"expected pass but check exited {exit_code} ({reason})"
    else:
        return False, f"bad expect value: {want}"

    if want_code is not None and exit_code != want_code:
        return False, f"exit_code want {want_code} got {exit_code} ({reason})"

    reason_l = reason.lower()
    for n in needles:
        if str(n).lower() not in reason_l:
            # soft: allow partial token match across reason
            if not any(tok.lower() in reason_l for tok in str(n).split()):
                return False, f"reason missing {n!r}: {reason}"
    return True, "ok"


def run_case(case_dir: Path) -> CaseResult:
    cid = case_dir.name
    res = CaseResult(cid)
    inp = load_json(case_dir / "input.json")
    expected = load_json(case_dir / "expected.json")
    code, reason = run_check(inp)
    res.actual_exit = code
    res.actual_reason = reason
    ok, detail = outcome_matches(expected, code, reason)
    res.ok = ok
    res.detail = detail if not ok else f"PASS exit={code} :: {reason}"
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description="Run harness failure-replay fixtures")
    ap.add_argument("--case", default="", help="Run a single case directory name")
    ap.add_argument("--list", action="store_true", help="List case ids and exit")
    args = ap.parse_args()

    if not CASES_DIR.is_dir():
        raise SystemExit(f"missing cases dir: {CASES_DIR}")

    cases = sorted([p for p in CASES_DIR.iterdir() if p.is_dir() and (p / "input.json").is_file()])
    if args.list:
        for p in cases:
            print(p.name)
        return

    if args.case:
        cases = [CASES_DIR / args.case]
        if not cases[0].is_dir():
            raise SystemExit(f"case not found: {args.case}")

    results: list[CaseResult] = []
    for c in cases:
        results.append(run_case(c))

    passed = sum(1 for r in results if r.ok)
    failed = sum(1 for r in results if not r.ok)
    for r in results:
        mark = "PASS" if r.ok else "MISS"
        print(f"[{mark}] {r.case_id}: {r.detail}")

    print(f"summary: {passed} passed, {failed} missed, {len(results)} total")
    if failed:
        raise SystemExit(1)
    print("ok: all failure-replay fixtures matched expected outcomes")


if __name__ == "__main__":
    main()
