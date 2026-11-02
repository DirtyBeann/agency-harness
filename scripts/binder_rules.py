#!/usr/bin/env python3
"""Shared binder rules: skeptic PASS evidence rule and secret-shape detection.

Single source of truth used by run_state.py, write_verdict.py and
run_failure_replay.py so the scripts and the contract schemas cannot drift.
The contract schemas embed the same two patterns as JSON `not.pattern` blocks;
keep them byte-identical with SECRET_PATTERN_I and SECRET_PATTERN_CS here.
"""
from __future__ import annotations

import re

# Case-insensitive secret markers (legacy set; unchanged behavior).
SECRET_PATTERN_I = (
    r"(sk_live_|sk_test_|rk_live_|whsec_|ghp_|github_pat_|gho_|xox[baprs]-|"
    r"BEGIN [A-Z ]*PRIVATE KEY|eyJ[A-Za-z0-9_-]{20,}|"
    r"SENTRY_ACCESS_TOKEN|API_KEY\s*=|password\s*=|Bearer\s+[A-Za-z0-9._\-]{20,})"
)

# Case-sensitive provider key shapes:
#   OpenAI sk- keys (covers sk-proj- and sk-svcacct- because '-' is in the class),
#   Anthropic sk-ant- keys (explicit, also covered by sk-),
#   AWS access key ids (AKIA/ASIA + 16 uppercase alphanumerics),
#   AWS secret access key assignments (40 char base64-ish value),
#   Google API keys (AIza + 35 chars).
# sk- must sit at a word boundary so benign words like "task-runner" or
# "risk-assessment" (which contain "sk-" mid-word) are not flagged.
SECRET_PATTERN_CS = (
    r"(\bsk-ant-[A-Za-z0-9_-]{10,}|\bsk-[A-Za-z0-9_-]{20,}|"
    r"(AKIA|ASIA)[A-Z0-9]{16}|"
    r"\bAIza[0-9A-Za-z_-]{35}|"
    r"(aws_secret_access_key|secret_access_key|AWS_SECRET_ACCESS_KEY|SECRET_ACCESS_KEY)\s*[=:]\s*['\"]?[A-Za-z0-9/+=]{35,})"
)

SECRET_RE_I = re.compile(r"(?i)" + SECRET_PATTERN_I)
SECRET_RE_CS = re.compile(SECRET_PATTERN_CS)


def looks_secret(text: str) -> bool:
    """True if the text contains any known secret-shaped marker."""
    if not isinstance(text, str):
        return False
    return bool(SECRET_RE_I.search(text) or SECRET_RE_CS.search(text))


def skeptic_pass_ok(payload: dict) -> tuple[bool, str]:
    """SkepticVerdict PASS evidence rule (failure fixture 01).

    A PASS verdict requires non-empty evidence_index or artifact_paths AND
    empty unverified / incomplete / failures / violations lists. Anything else
    is a false pass. Non-PASS verdicts are out of scope for this rule.
    """
    if payload.get("verdict") != "PASS":
        return True, "verdict is not PASS; evidence rule not applicable"
    evidence = payload.get("evidence_index") or []
    artifacts = payload.get("artifact_paths") or []
    if not evidence and not artifacts:
        return False, "PASS without evidence_index/artifact_paths (false pass; PASS requires evidence)"
    for key in ("unverified", "incomplete", "failures", "violations"):
        if payload.get(key):
            return False, f"PASS with open {key} (PASS requires empty unverified/incomplete/failures/violations)"
    return True, "PASS with evidence and no open items"
