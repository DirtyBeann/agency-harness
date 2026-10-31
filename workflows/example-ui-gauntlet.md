# example-ui-gauntlet

Generic nested UI builder/critic example. Child of example-feature-branch.

## Rules
- Taste-risk Frontend only.
- WIN is not ship. Parent REVIEW and SKEPTIC still required.
- OFF for auth / RLS / payments / webhooks / sensitive_data / secrets_rotation.
- Same subscription pool may not serve builder and critic.
- flags/PAUSE leads to PAUSED soft stop.

## Attribution note
Builder/critic loop idea is common. Do not bundle third-party CC-BY skill text as proprietary Core.
If referencing such a skill later, attribute or omit.

## How to run
python scripts/run_state.py --workflow example-ui-gauntlet --from HOLD --to BAR_GATED --flags-dir flags --dry-run

## VI preview (browser-use)

Before critic rounds that need rendered evidence, and on **re-VI** after WIN:

```powershell
cd agency-harness-universal
powershell -File scripts\vi_preview.ps1 -Url "<preview-url>"
```

- Isolated CDP on 127.0.0.1:9222 only.
- Never attach to the operator daily browser without explicit confirm.
- Full notes: docs/vi-preview-browser-use.md.
- Playwright stays the deterministic a11y/e2e fallback if CDP is down.