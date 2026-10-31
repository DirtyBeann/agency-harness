# Sync with a private live farm

This pack is a **sanitized extract**. If you also keep a private, customized harness elsewhere:

1. Improve the private farm first.
2. **Ask the owner** before copying those improvements into this universal tree.
3. When syncing, re-run sanitization: strip personal names, absolute paths, real models/providers, IPs, keys, product-specific policy, and live ledgers.
4. Keep placeholders such as `[ADD_MODEL_HERE]`, `[ADD_PROVIDER]`, and `${HARNESS_HOME}`.
5. Re-run `scripts/validate_setup.py`, binder smoke, failure replay, and a personal-data scan.
6. Update `SANITIZATION-REPORT.md` / `SOURCE-INTEGRITY-REPORT.md` on the private side only if you maintain those proofs.

Do not auto-mirror a private farm into a shareable pack.
