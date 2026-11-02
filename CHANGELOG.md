# Changelog

## Unreleased

- Security hardening (review 2026-11-02), all enforced by new tests:
  - `--no-strict` is refused on the gated transitions `REVIEW->SKEPTIC` and `SKEPTIC->DEV_CANDIDATE`; verdict gates always run there. Flag marked dev-only in help text (`run_state.py`, `advance.py`).
  - The binder now natively rejects a `SkepticVerdict` `PASS` without evidence or with open items. The rule lives in one shared module `scripts/binder_rules.py` (used by the binder and the failure replay) and is mirrored by an if/then in `contracts/skeptic_verdict.schema.json`.
  - Recorded run state: allowed non-dry-run transitions with `--run-id` write `ledger/state/<run_id>.json`; a later `--from` that contradicts the record is refused. Run ids are validated before use in paths.
  - Owner gate: `LIVE_GO` / `LIVE_NOGO` (and any `"owner_only": true` state) require a run id, a recorded `OWNER_TEST` state, and an owner approval artifact `ledger/verdicts/owner-approval-<run_id>.json` (`OwnerApproval/v1`, decision `GO`/`NOGO` matching the target). A bare `--from OWNER_TEST` claim is refused, even in `--dry-run`. Documented in `docs/ENFORCEMENT_LEVELS.md`.
  - Canonical `flags/PAUSE` is always checked; `--flags-dir` only adds a location and can never mask the kill switch (`check_flags.py` had no such hole; it reads the canonical dir only).
  - Secret filters extended in one shared module plus every contract schema: OpenAI `sk-` keys (incl. `sk-proj-`, `sk-svcacct-`), Anthropic `sk-ant-`, AWS `AKIA`/`ASIA` ids and `aws_secret_access_key` style assignments, Google `AIza` keys. `sk-` must sit at a word boundary so words like `task-runner` or `risk-` are not flagged. Also fixed over-escaped `\\s` patterns in the review/security schemas so all six schemas carry identical patterns.
- Tests: new unittest suite `tests/test_binder_security.py` (27 tests covering each fix plus positive paths); failure replay grew from 13 to 18 cases (`14-no-strict-on-gated-edge`, `15-self-claimed-owner-test-live-go`, `16-flags-dir-redirect-pause`, `17-secret-aws-key-id-in-verdict`, `18-secret-openai-key-in-verdict`; secret values built at runtime, never literal). `binder_smoke.py --dry-run` now cleans its `tmp/binder_smoke_*` scratch dir.
- CI: new `.github/workflows/tests.yml` (push and pull_request, ubuntu-latest and windows-latest, Python 3.11) runs failure replay, binder smoke and the unittest suite.
- Repo hygiene: full verbatim Apache-2.0 `LICENSE`; new `NOTICE`; `SECURITY.md` contact (jason@madebyesco.com, no public issues for vulnerabilities); contract `$id` values changed from `https://[PRIVATE_WORKSPACE].local/...` to `https://github.com/DirtyBeann/agency-harness/contracts/<file>`; generic `conductor` naming in `docs/CODE-TIERS.md`; `.gitignore` deduped plus `ledger/state/` and `.agents/`; added the previously missing `adapters/pools.example.json`, `docs/pool-rules.example.md` and `docs/l1-deterministic-gates.md`.
- Add Codex CLI support: root `AGENTS.md`, `adapters/codex/` (skill installers, example `config.toml`), `docs/CODEX.md`, and a sample headless run in `docs/examples/codex-demo.md`.
- Rewrite README in plain language; fill LICENSE copyright holder.
- Fix: `binder_smoke.py` now creates `tmp/` (fresh clones crashed). `gate_review.py` output is ASCII only (cp1252 consoles crashed the escalate path). Both found by the Codex demo run.

## 0.1.2 - 2026-09-11

- Add `docs/CODE-TIERS.md` and `adapters/kilo/examples/code-tiers.example.jsonc`: implementer tiers `code-c` / `code-b` / `code-a` as **job titles with GUI-owned models** (no hard-coded `model`).
- Conductor examples updated: mandatory explicit model on APPLY spawn; no conductor-model inherit; plan agent demoted to optional helper.
- Sync rule unchanged: ask before mirroring private farm; keep placeholders for real model ids.

## 0.1.0 - 2026-09-09

- Initial sanitized universal pack: contracts, example workflows, binder CLI, failure replay, L1 checks.
- AI setup prompt + adapters for Kilo, Grok Build, OpenCode.
- Private integrity reports kept out of the published tree (`docs/private/`, gitignored).

## 0.1.1 - 2026-09-09

- Add portable scripts/vi_preview.ps1 + docs/vi-preview-browser-use.md for isolated CDP VI preview.
- Document PAYG priority (DeepSeek then Z.AI/GLM) without binder hard-refuse (docs/payg-priority.md).
- Hook notes on workflows/example-ui-gauntlet.md.

