# Sharing this pack

## Safe to share

Friend-share or private GitHub is fine when the archive **excludes**:

- `docs/private/` (local integrity proofs; may contain private farm paths)
- `tmp/`
- `config/models.yaml`
- `.env`
- venvs / `__pycache__`

Use:

```powershell
powershell -File scripts/make_share_zip.ps1
```

That script stages a zip without `docs/private` and `tmp`.

## Public GitHub

1. The `LICENSE` copyright holder is Jason Escobar; forks should add their own name for their changes.
2. Confirm Security/Repo Audit clear.
3. Push only the share zip contents (or a git init that never adds `docs/private/`).

Do not publish `docs/private/`.