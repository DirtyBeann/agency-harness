#!/usr/bin/env python3
"""Smoke legal + illegal binder cases. Exit 0 only if all expectations hold.

Does not require network. Uses tmp verdicts under harness/tmp/binder_smoke_*/.
Leaves ledger refuse events under run_id binder-smoke-* (real append) unless --dry-run.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FLAGS = ROOT / "flags"
RUN_STATE = SCRIPTS / "run_state.py"

PASS = 0
FAIL = 0


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def expect(label: str, proc: subprocess.CompletedProcess, want_rc: int, want_allowed: bool | None) -> None:
    global PASS, FAIL
    body = (proc.stdout or "").strip()
    try:
        data = json.loads(body) if body else {}
    except json.JSONDecodeError:
        data = {}
    ok_rc = proc.returncode == want_rc
    ok_all = True
    if want_allowed is not None:
        ok_all = bool(data.get("allowed")) is want_allowed
    if ok_rc and ok_all:
        PASS += 1
        print(f"PASS  {label}  rc={proc.returncode}  allowed={data.get('allowed')}")
    else:
        FAIL += 1
        print(
            f"FAIL  {label}  got_rc={proc.returncode} want_rc={want_rc} "
            f"allowed={data.get('allowed')} want_allowed={want_allowed}"
        )
        if body:
            print(f"      stdout: {body[:400]}")
        if proc.stderr:
            print(f"      stderr: {proc.stderr[:400]}")


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def fixture_review_pass() -> dict:
    return {
        "schema": "ReviewVerdict/v1",
        "decision": "pass",
        "summary": "smoke review pass",
        "requirementsChecked": [{"id": "ac-1", "status": "pass"}],
        "issues": [],
        "failureModes": [],
        "evidence_refs": ["docs/smoke"],
    }


def fixture_security_allow() -> dict:
    return {
        "schema": "SecurityVerdict/v1",
        "decision": "allow",
        "risk_level": "low",
        "reason": "smoke security allow",
        "findings": [],
        "failureModes": [],
        "evidence_refs": ["docs/smoke"],
    }


def fixture_skeptic_pass() -> dict:
    return {
        "schema": "SkepticVerdict/v1",
        "verdict": "PASS",
        "rounds_used": 1,
        "failures": [],
        "evidence_index": ["docs/smoke"],
    }


def binder(extra: list[str], dry_run: bool) -> list[str]:
    cmd = [sys.executable, str(RUN_STATE)] + extra
    if dry_run:
        cmd.append("--dry-run")
    return cmd


def main() -> None:
    dry = "--dry-run" in sys.argv
    (ROOT / "tmp").mkdir(parents=True, exist_ok=True)  # tmp/ is gitignored, so a fresh clone has none
    tmp = Path(tempfile.mkdtemp(prefix="binder_smoke_", dir=str(ROOT / "tmp")))
    try:
        code = run_cases(tmp, dry)
    finally:
        # --dry-run writes nothing worth keeping: clean the scratch dir so
        # repeated runs do not litter tmp/binder_smoke_*. Non-dry runs keep
        # fixtures for docs reference.
        if dry:
            shutil.rmtree(tmp, ignore_errors=True)
            print(f"cleaned smoke tmp: {tmp} (--dry-run)")
    raise SystemExit(code)


def run_cases(tmp: Path, dry: bool) -> int:
    global PASS, FAIL
    verdicts = tmp / "verdicts"
    flags_tmp = tmp / "flags"
    flags_tmp.mkdir(parents=True, exist_ok=True)
    print(f"smoke tmp: {tmp}")

    # --- Legal: HOLD -> SCOPE_LOCKED ---
    expect(
        "legal HOLD->SCOPE_LOCKED",
        run(
            binder(
                [
                    "--workflow",
                    "example-feature-branch",
                    "--from",
                    "HOLD",
                    "--to",
                    "SCOPE_LOCKED",
                    "--flags-dir",
                    str(flags_tmp),
                    "--run-id",
                    "binder-smoke-legal01",
                ],
                dry,
            )
        ),
        0,
        True,
    )

    # --- Legal: APPLYING -> VERIFY ---
    expect(
        "legal APPLYING->VERIFY",
        run(
            binder(
                [
                    "--workflow",
                    "example-feature-branch",
                    "--from",
                    "APPLYING",
                    "--to",
                    "VERIFY",
                    "--flags-dir",
                    str(flags_tmp),
                    "--run-id",
                    "binder-smoke-legal02",
                ],
                dry,
            )
        ),
        0,
        True,
    )

    # --- Illegal: APPLYING -> DEV_CANDIDATE ---
    expect(
        "illegal APPLYING->DEV_CANDIDATE",
        run(
            binder(
                [
                    "--workflow",
                    "example-feature-branch",
                    "--from",
                    "APPLYING",
                    "--to",
                    "DEV_CANDIDATE",
                    "--flags-dir",
                    str(flags_tmp),
                    "--run-id",
                    "binder-smoke-ill01",
                ],
                dry,
            )
        ),
        1,
        False,
    )

    # --- Illegal: REVIEW -> SKEPTIC without verdicts (strict default) ---
    empty_v = tmp / "empty_verdicts"
    empty_v.mkdir(parents=True, exist_ok=True)
    expect(
        "illegal REVIEW->SKEPTIC missing verdicts",
        run(
            binder(
                [
                    "--workflow",
                    "example-feature-branch",
                    "--from",
                    "REVIEW",
                    "--to",
                    "SKEPTIC",
                    "--flags-dir",
                    str(flags_tmp),
                    "--verdicts-dir",
                    str(empty_v),
                    "--run-id",
                    "binder-smoke-ill02",
                ],
                dry,
            )
        ),
        1,
        False,
    )

    # --- Legal: REVIEW -> SKEPTIC with fake PASS path (documented) ---
    # Documented fake PASS path: write latest-review.json + latest-security.json
    # with ReviewVerdict.decision==pass and SecurityVerdict.decision==allow,
    # then binder --strict REVIEW->SKEPTIC exits 0.
    write_json(verdicts / "latest-review.json", fixture_review_pass())
    write_json(verdicts / "latest-security.json", fixture_security_allow())
    expect(
        "legal REVIEW->SKEPTIC with fixture pass/allow",
        run(
            binder(
                [
                    "--workflow",
                    "example-feature-branch",
                    "--from",
                    "REVIEW",
                    "--to",
                    "SKEPTIC",
                    "--flags-dir",
                    str(flags_tmp),
                    "--verdicts-dir",
                    str(verdicts),
                    "--run-id",
                    "binder-smoke-legal03",
                ],
                dry,
            )
        ),
        0,
        True,
    )

    # --- Legal documented: SKEPTIC -> DEV_CANDIDATE with fake PASS ---
    write_json(verdicts / "latest-skeptic.json", fixture_skeptic_pass())
    expect(
        "legal SKEPTIC->DEV_CANDIDATE with fixture PASS",
        run(
            binder(
                [
                    "--workflow",
                    "example-feature-branch",
                    "--from",
                    "SKEPTIC",
                    "--to",
                    "DEV_CANDIDATE",
                    "--flags-dir",
                    str(flags_tmp),
                    "--verdicts-dir",
                    str(verdicts),
                    "--skeptic-path",
                    str(verdicts / "latest-skeptic.json"),
                    "--run-id",
                    "binder-smoke-legal04",
                ],
                dry,
            )
        ),
        0,
        True,
    )

    # --- Illegal: SKEPTIC -> DEV_CANDIDATE without skeptic file ---
    expect(
        "illegal SKEPTIC->DEV_CANDIDATE missing verdict",
        run(
            binder(
                [
                    "--workflow",
                    "example-feature-branch",
                    "--from",
                    "SKEPTIC",
                    "--to",
                    "DEV_CANDIDATE",
                    "--flags-dir",
                    str(flags_tmp),
                    "--verdicts-dir",
                    str(empty_v),
                    "--run-id",
                    "binder-smoke-ill03",
                ],
                dry,
            )
        ),
        1,
        False,
    )

    # --- PAUSE refuse mutate ---
    pause_flags = tmp / "flags_pause"
    pause_flags.mkdir(parents=True, exist_ok=True)
    (pause_flags / "PAUSE").write_text("paused for smoke\n", encoding="utf-8")
    expect(
        "PAUSE refuse APPLYING->VERIFY",
        run(
            binder(
                [
                    "--workflow",
                    "example-feature-branch",
                    "--from",
                    "APPLYING",
                    "--to",
                    "VERIFY",
                    "--flags-dir",
                    str(pause_flags),
                    "--run-id",
                    "binder-smoke-pause01",
                ],
                dry,
            )
        ),
        10,
        False,
    )

    # --- example-ui-gauntlet legal HOLD -> BAR_GATED ---
    expect(
        "legal example-ui-gauntlet HOLD->BAR_GATED",
        run(
            binder(
                [
                    "--workflow",
                    "example-ui-gauntlet",
                    "--from",
                    "HOLD",
                    "--to",
                    "BAR_GATED",
                    "--flags-dir",
                    str(flags_tmp),
                    "--run-id",
                    "binder-smoke-ug01",
                ],
                dry,
            )
        ),
        0,
        True,
    )

    # --- example-ui-gauntlet illegal unknown skip ---
    expect(
        "illegal example-ui-gauntlet HOLD->WIN",
        run(
            binder(
                [
                    "--workflow",
                    "example-ui-gauntlet",
                    "--from",
                    "HOLD",
                    "--to",
                    "WIN",
                    "--flags-dir",
                    str(flags_tmp),
                    "--run-id",
                    "binder-smoke-ug02",
                ],
                dry,
            )
        ),
        1,
        False,
    )

    # --- --transition when ---
    expect(
        "legal --transition verify_pass",
        run(
            binder(
                [
                    "--workflow",
                    "example-feature-branch",
                    "--from",
                    "VERIFY",
                    "--transition",
                    "verify_pass",
                    "--flags-dir",
                    str(flags_tmp),
                    "--run-id",
                    "binder-smoke-when01",
                ],
                dry,
            )
        ),
        0,
        True,
    )

    # --- advance.py --list-next ---
    expect(
        "legal advance --list-next HOLD",
        run(
            [
                sys.executable,
                str(SCRIPTS / "advance.py"),
                "--workflow",
                "example-feature-branch",
                "--from",
                "HOLD",
                "--list-next",
                "--flags-dir",
                str(flags_tmp),
                "--run-id",
                "binder-smoke-list01",
                "--dry-run",
            ]
        ),
        0,
        None,
    )

    print(f"\nRESULT  pass={PASS}  fail={FAIL}  tmp={tmp}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    main()
