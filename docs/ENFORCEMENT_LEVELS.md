# Enforcement levels

| Layer | Level |
|---|---|
| Binder CLI / advance | Hard fail (non-zero exit) |
| Verdict schema validation | Hard fail |
| Failure replay / unit tests / binder smoke | Hard: enforced in GitHub Actions (`.github/workflows/tests.yml`) and local smoke |
| L1 checks (em-dash, axe wrapper) | Hard in local smoke runs; wire into CI as needed |
| Host skill ACL (Kilo deny-default) | Partial if applied |
| SKILL.md text | Advisory |
| Human operator | Final |

Do not claim skills alone enforce policy.

## Owner gate and recorded run state

Two binder mechanisms keep a caller from self-claiming its way to live:

1. **Recorded run state.** When a transition is allowed with `--run-id` and
   without `--dry-run`, `scripts/run_state.py` writes the new state to
   `ledger/state/<run_id>.json` (`RunState/v1`, gitignored). On every later
   transition with the same `--run-id`, a recorded state that disagrees with
   `--from` is refused. Run ids are validated (`^[A-Za-z0-9][A-Za-z0-9_.:-]{7,63}$`)
   before they are used in any path.
2. **Owner approval artifact.** The owner-gated targets `LIVE_GO`, `LIVE_NOGO`
   (and any workflow state marked `"owner_only": true`) require all of:
   - an explicit `--run-id`,
   - a recorded run state equal to `OWNER_TEST` for that run id (a bare
     `--from OWNER_TEST` claim is refused, even in `--dry-run`),
   - an owner approval artifact `ledger/verdicts/owner-approval-<run_id>.json`
     with `"schema": "OwnerApproval/v1"`, a matching `run_id`, and a `decision`
     of `GO` for `LIVE_GO` or `NOGO` for `LIVE_NOGO`.

Example artifact:

```json
{
  "schema": "OwnerApproval/v1",
  "run_id": "feature-x-20261102",
  "decision": "GO",
  "ts": "2026-11-02T12:00:00Z"
}
```

Also enforced by the binder: `--no-strict` is refused on the gated transitions
`REVIEW->SKEPTIC` and `SKEPTIC->DEV_CANDIDATE` (verdict gates always run), and
the canonical `flags/PAUSE` kill switch is checked even when `--flags-dir`
points somewhere else.
