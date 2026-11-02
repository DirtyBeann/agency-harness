---
id: vi-preview-browser-use
updated: 2026-09-09
---

# VI preview via browser-use

One operator path for Visual-inspector / ui-gauntlet **re-VI** using isolated Chrome CDP.

**Not:** daily-browser attach, cloud Browser Use, Playwright replacement, or merge authority.

## Prerequisites

Install `browser-use` with isolated helpers (`bu-chrome`, `bu-doctor`, `browser-use`) under `%USERPROFILE%\.local\bin`. CDP must stay on `127.0.0.1` only.

## One command

```powershell
cd agency-harness
powershell -File scripts\vi_preview.ps1 -Url "http://127.0.0.1:3000"
```

Doctor / CDP only:

```powershell
powershell -File scripts\vi_preview.ps1 -DoctorOnly
```

## Security

| Rule | Detail |
|---|---|
| CDP bind | `127.0.0.1:9222` only |
| Profile | isolated `browser-use-chrome-profile` (not the daily browser profile) |
| Daily browser | Forbidden unless the operator explicitly confirms that session |
| Tunnel / `0.0.0.0` | Never |
| Cloud API key | Optional; not required for local VI |

## Where it fits example-ui-gauntlet

1. Critic needs **rendered** evidence, not builder prose.
2. On WIN or before parent hand-off: **re-VI** with this preview path.
3. Visual-inspector never merges; never lands live branches.
4. Gauntlet stays OFF for auth / RLS / payments / webhooks / sensitive_data / secrets_rotation.

## Agent checklist

1. `vi_preview.ps1 -DoctorOnly` (or start isolated Chrome).
2. Open the preview URL with `-Url`.
3. Store **paths only** in ledger / GauntletRound evidence fields.
4. Prefer your configured gateway/pools for any helper LLM - do not burn a shared IDE quota.
5. Playwright remains the deterministic FE/e2e fallback if CDP is down.