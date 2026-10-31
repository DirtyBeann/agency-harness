# Security

- Never commit `config/models.yaml`, `.env`, ledgers, or API keys.
- Secret-shaped patterns in schemas are **deny/redact regexes**, not credentials.
- Binder and schema validation are fail-closed; treat escalate as owner interrupt, not allow.
- Report issues privately to the copyright holder listed in LICENSE.
- Isolated browser debugging (if used) must bind to localhost only.
