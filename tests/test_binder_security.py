"""Security regression tests for the binder CLI (review fixes 2026-11-02).

Stdlib unittest only. Every case uses temp dirs for flags, verdicts and
ledger state, and cleans up. Secret-shaped probe values are always built at
runtime by concatenation so this repo never contains a literal key-shaped
string.

Run with:
  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import binder_rules  # noqa: E402  (shared rules under test)

CANONICAL_FLAGS = ROOT / "flags"
WORKFLOW = "example-feature-branch"


def run_binder(args, flags_dir, state_dir, verdicts_dir=None, dry_run=True):
    cmd = [
        sys.executable, str(SCRIPTS / "run_state.py"),
        "--workflow", WORKFLOW,
        "--flags-dir", str(flags_dir),
        "--ledger-state-dir", str(state_dir),
    ] + list(args)
    if verdicts_dir is not None:
        cmd += ["--verdicts-dir", str(verdicts_dir)]
    if dry_run:
        cmd.append("--dry-run")
    return subprocess.run(cmd, capture_output=True, text=True)


def out_of(proc):
    return ((proc.stdout or "") + (proc.stderr or "")).strip()


def write_json(path: Path, obj) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
    return path


def review_pass() -> dict:
    return {
        "schema": "ReviewVerdict/v1",
        "decision": "pass",
        "summary": "unit test review pass",
        "requirementsChecked": [{"id": "ac-1", "status": "pass"}],
        "issues": [],
        "failureModes": [],
        "evidence_refs": ["docs/unit"],
    }


def security_allow() -> dict:
    return {
        "schema": "SecurityVerdict/v1",
        "decision": "allow",
        "risk_level": "low",
        "reason": "unit test security allow",
        "findings": [],
        "failureModes": [],
        "evidence_refs": ["docs/unit"],
    }


def skeptic_pass(evidence=True) -> dict:
    payload = {
        "schema": "SkepticVerdict/v1",
        "verdict": "PASS",
        "rounds_used": 1,
        "failures": [],
        "evidence_index": ["docs/unit"] if evidence else [],
    }
    return payload


class TempEnv(unittest.TestCase):
    """Base: temp flags/verdicts/state dirs per test."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory(prefix="binder_sec_")
        td = Path(self._td.name)
        self.flags = td / "flags"
        self.flags.mkdir(parents=True)
        self.verdicts = td / "verdicts"
        self.verdicts.mkdir(parents=True)
        self.state = td / "state"
        self.state.mkdir(parents=True)

    def tearDown(self):
        self._td.cleanup()


class Fix1NoStrictGatedTransitions(TempEnv):
    def test_no_strict_refused_on_review_to_skeptic(self):
        p = run_binder(
            ["--from", "REVIEW", "--to", "SKEPTIC", "--no-strict", "--run-id", "unit-nostri-01"],
            self.flags, self.state, self.verdicts,
        )
        self.assertEqual(p.returncode, 1, out_of(p))
        self.assertIn("--no-strict is not allowed on gated transitions", out_of(p))

    def test_no_strict_refused_on_skeptic_to_dev_candidate(self):
        p = run_binder(
            ["--from", "SKEPTIC", "--to", "DEV_CANDIDATE", "--no-strict", "--run-id", "unit-nostri-02"],
            self.flags, self.state, self.verdicts,
        )
        self.assertEqual(p.returncode, 1, out_of(p))
        self.assertIn("--no-strict is not allowed on gated transitions", out_of(p))

    def test_gates_still_run_without_the_flag(self):
        # --no-strict absent but verdicts missing: gate must still refuse.
        p = run_binder(
            ["--from", "REVIEW", "--to", "SKEPTIC", "--run-id", "unit-nostri-03"],
            self.flags, self.state, self.verdicts,
        )
        self.assertEqual(p.returncode, 1, out_of(p))

    def test_legit_gated_transition_still_allowed(self):
        write_json(self.verdicts / "latest-review.json", review_pass())
        write_json(self.verdicts / "latest-security.json", security_allow())
        p = run_binder(
            ["--from", "REVIEW", "--to", "SKEPTIC", "--run-id", "unit-nostri-04"],
            self.flags, self.state, self.verdicts,
        )
        self.assertEqual(p.returncode, 0, out_of(p))
        self.assertIn('"allowed": true', out_of(p))


class Fix2SkepticFalsePass(TempEnv):
    def test_binder_rejects_pass_without_evidence(self):
        write_json(self.verdicts / "latest-skeptic.json", skeptic_pass(evidence=False))
        p = run_binder(
            ["--from", "SKEPTIC", "--to", "DEV_CANDIDATE", "--run-id", "unit-skepfx-01"],
            self.flags, self.state, self.verdicts,
        )
        self.assertEqual(p.returncode, 1, out_of(p))
        self.assertIn("PASS", out_of(p))
        self.assertIn("evidence", out_of(p))

    def test_binder_rejects_pass_with_open_unverified(self):
        payload = skeptic_pass(evidence=True)
        payload["unverified"] = ["claim:feature_complete_without_proof"]
        write_json(self.verdicts / "latest-skeptic.json", payload)
        p = run_binder(
            ["--from", "SKEPTIC", "--to", "DEV_CANDIDATE", "--run-id", "unit-skepfx-02"],
            self.flags, self.state, self.verdicts,
        )
        self.assertEqual(p.returncode, 1, out_of(p))
        self.assertIn("unverified", out_of(p))

    def test_binder_allows_pass_with_evidence(self):
        write_json(self.verdicts / "latest-skeptic.json", skeptic_pass(evidence=True))
        p = run_binder(
            ["--from", "SKEPTIC", "--to", "DEV_CANDIDATE", "--run-id", "unit-skepfx-03"],
            self.flags, self.state, self.verdicts,
        )
        self.assertEqual(p.returncode, 0, out_of(p))

    def test_schema_rejects_false_pass(self):
        # validate_verdict.py must refuse a PASS with no evidence (schema if/then).
        from jsonschema import Draft202012Validator

        schema = json.loads(
            (ROOT / "contracts" / "skeptic_verdict.schema.json").read_text(encoding="utf-8")
        )
        errors = list(Draft202012Validator(schema).iter_errors(skeptic_pass(evidence=False)))
        self.assertTrue(errors, "schema must reject PASS without evidence")

    def test_shared_rule_matches_replay_semantics(self):
        ok, _ = binder_rules.skeptic_pass_ok({"verdict": "NOT_READY"})
        self.assertTrue(ok)
        ok, _ = binder_rules.skeptic_pass_ok(skeptic_pass(evidence=True))
        self.assertTrue(ok)
        ok, why = binder_rules.skeptic_pass_ok(skeptic_pass(evidence=False))
        self.assertFalse(ok)
        self.assertIn("PASS", why)
        self.assertIn("evidence", why)


class Fix3OwnerGate(TempEnv):
    RUN = "unit-owner-0001"

    def test_self_claimed_owner_test_refused_even_dry_run(self):
        p = run_binder(
            ["--from", "OWNER_TEST", "--to", "LIVE_GO", "--run-id", self.RUN],
            self.flags, self.state, self.verdicts,
        )
        self.assertEqual(p.returncode, 1, out_of(p))
        self.assertIn("OWNER_TEST", out_of(p))
        self.assertIn("recorded", out_of(p))

    def test_missing_run_id_refused(self):
        p = run_binder(["--from", "OWNER_TEST", "--to", "LIVE_GO"], self.flags, self.state, self.verdicts)
        self.assertEqual(p.returncode, 1, out_of(p))
        self.assertIn("requires --run-id", out_of(p))

    def test_recorded_state_mismatch_refused(self):
        write_json(self.state / f"{self.RUN}.json", {
            "schema": "RunState/v1", "run_id": self.RUN, "workflow": WORKFLOW,
            "from": "REVIEW", "state": "SKEPTIC", "ts": "2026-11-02T00:00:00Z",
        })
        p = run_binder(
            ["--from", "OWNER_TEST", "--to", "LIVE_GO", "--run-id", self.RUN],
            self.flags, self.state, self.verdicts,
        )
        self.assertEqual(p.returncode, 1, out_of(p))
        self.assertIn("recorded run state", out_of(p))

    def test_owner_gate_requires_matching_decision(self):
        write_json(self.state / f"{self.RUN}.json", {
            "schema": "RunState/v1", "run_id": self.RUN, "workflow": WORKFLOW,
            "from": "DEV_CANDIDATE", "state": "OWNER_TEST", "ts": "2026-11-02T00:00:00Z",
        })
        write_json(self.verdicts / f"owner-approval-{self.RUN}.json", {
            "schema": "OwnerApproval/v1", "run_id": self.RUN,
            "decision": "GO", "ts": "2026-11-02T00:00:00Z",
        })
        p = run_binder(
            ["--from", "OWNER_TEST", "--to", "LIVE_NOGO", "--run-id", self.RUN],
            self.flags, self.state, self.verdicts,
        )
        self.assertEqual(p.returncode, 1, out_of(p))
        self.assertIn("decision must be NOGO", out_of(p))

    def test_recorded_owner_test_plus_go_approval_allows_live_go(self):
        write_json(self.state / f"{self.RUN}.json", {
            "schema": "RunState/v1", "run_id": self.RUN, "workflow": WORKFLOW,
            "from": "DEV_CANDIDATE", "state": "OWNER_TEST", "ts": "2026-11-02T00:00:00Z",
        })
        write_json(self.verdicts / f"owner-approval-{self.RUN}.json", {
            "schema": "OwnerApproval/v1", "run_id": self.RUN,
            "decision": "GO", "ts": "2026-11-02T00:00:00Z",
        })
        p = run_binder(
            ["--from", "OWNER_TEST", "--to", "LIVE_GO", "--run-id", self.RUN],
            self.flags, self.state, self.verdicts,
        )
        self.assertEqual(p.returncode, 0, out_of(p))

    def test_non_dry_run_records_state_and_enforces_it(self):
        run_id = "unit-owner-0002"
        p = run_binder(
            ["--from", "HOLD", "--to", "SCOPE_LOCKED", "--run-id", run_id],
            self.flags, self.state, self.verdicts, dry_run=False,
        )
        self.assertEqual(p.returncode, 0, out_of(p))
        rec = json.loads((self.state / f"{run_id}.json").read_text(encoding="utf-8"))
        self.assertEqual(rec["state"], "SCOPE_LOCKED")
        # A contradictory --from must now be refused.
        p2 = run_binder(
            ["--from", "VERIFY", "--to", "REVIEW", "--run-id", run_id],
            self.flags, self.state, self.verdicts,
        )
        self.assertEqual(p2.returncode, 1, out_of(p2))
        self.assertIn("recorded run state", out_of(p2))

    def test_dry_run_does_not_write_state(self):
        run_id = "unit-owner-0003"
        p = run_binder(
            ["--from", "HOLD", "--to", "SCOPE_LOCKED", "--run-id", run_id],
            self.flags, self.state, self.verdicts, dry_run=True,
        )
        self.assertEqual(p.returncode, 0, out_of(p))
        self.assertFalse((self.state / f"{run_id}.json").exists())

    def test_unsafe_run_id_refused(self):
        p = run_binder(
            ["--from", "HOLD", "--to", "SCOPE_LOCKED", "--run-id", "../evil-run-1"],
            self.flags, self.state, self.verdicts,
        )
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("--run-id", out_of(p))


class Fix4CanonicalPause(TempEnv):
    def test_flags_dir_redirect_cannot_mask_canonical_pause(self):
        pause = CANONICAL_FLAGS / "PAUSE"
        existed = pause.exists()
        created = False
        try:
            if not existed:
                pause.write_text("unit test canonical pause\n", encoding="utf-8")
                created = True
            # --flags-dir points at an empty dir; canonical PAUSE must still refuse.
            p = run_binder(
                ["--from", "APPLYING", "--to", "VERIFY", "--run-id", "unit-pause-01"],
                self.flags, self.state, self.verdicts,
            )
            self.assertEqual(p.returncode, 10, out_of(p))
            self.assertIn("PAUSE", out_of(p))
        finally:
            if created and pause.exists():
                pause.unlink()

    def test_pause_in_custom_flags_dir_still_refuses(self):
        (self.flags / "PAUSE").write_text("pause via custom dir\n", encoding="utf-8")
        p = run_binder(
            ["--from", "APPLYING", "--to", "VERIFY", "--run-id", "unit-pause-02"],
            self.flags, self.state, self.verdicts,
        )
        self.assertEqual(p.returncode, 10, out_of(p))

    def test_no_pause_allows_transition(self):
        p = run_binder(
            ["--from", "APPLYING", "--to", "VERIFY", "--run-id", "unit-pause-03"],
            self.flags, self.state, self.verdicts,
        )
        self.assertEqual(p.returncode, 0, out_of(p))


class Fix5SecretPatterns(TempEnv):
    def _write_review_with_summary(self, summary):
        payload = review_pass()
        payload["summary"] = summary
        src = write_json(Path(self._td.name) / "probe.json", payload)
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "write_verdict.py"),
             "--kind", "review", "--json-file", str(src),
             "--out-dir", str(self.verdicts)],
            capture_output=True, text=True,
        )

    def test_openai_sk_proj_key_refused(self):
        secret = "sk-" + "proj-" + "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8"
        p = self._write_review_with_summary("leaked " + secret + " in summary")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("refused", out_of(p))
        self.assertIn("secret", out_of(p))

    def test_aws_access_key_id_refused(self):
        secret = "AK" + "IA" + "Q0W9E8R7T6Y5U4I3"
        p = self._write_review_with_summary("found " + secret + " in logs")
        self.assertNotEqual(p.returncode, 0)

    def test_google_api_key_refused(self):
        secret = "AIza" + "Sy9BvLm2QwRtZxNkJdHfUcXePlGaNbVoTrDz" + "M"
        p = self._write_review_with_summary("found " + secret + " in config")
        self.assertNotEqual(p.returncode, 0)

    def test_aws_secret_assignment_refused(self):
        secret = "aws_secret_access_key = " + "Zq2w" * 10
        p = self._write_review_with_summary("env had " + secret)
        self.assertNotEqual(p.returncode, 0)

    def test_aws_secret_env_style_refused(self):
        secret = "AWS_SECRET_" + "ACCESS_KEY=" + "Zq2w" * 10
        p = self._write_review_with_summary("env had " + secret)
        self.assertNotEqual(p.returncode, 0)

    def test_benign_words_not_flagged(self):
        for text in (
            "task-runner",
            "risk-assessment-of-the-release-candidate",
            "the task-runner handles retries",
            "aws_secret_access_key rotation completed",
            "sk-update-needed",
        ):
            self.assertFalse(binder_rules.looks_secret(text), text)
        p = self._write_review_with_summary("the task-runner handles retries on risk- surfaces")
        self.assertEqual(p.returncode, 0, out_of(p))

    def test_clean_verdict_still_written(self):
        src = write_json(Path(self._td.name) / "clean.json", review_pass())
        p = subprocess.run(
            [sys.executable, str(SCRIPTS / "write_verdict.py"),
             "--kind", "review", "--json-file", str(src),
             "--out-dir", str(self.verdicts)],
            capture_output=True, text=True,
        )
        self.assertEqual(p.returncode, 0, out_of(p))
        self.assertTrue((self.verdicts / "latest-review.json").exists())


if __name__ == "__main__":
    unittest.main()
