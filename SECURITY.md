# Security

- Never commit `config/models.yaml`, `.env`, ledgers, or API keys.
- Secret-shaped patterns in schemas and `scripts/binder_rules.py` are **deny/redact regexes**, not credentials.
- Binder and schema validation are fail-closed; treat escalate as owner interrupt, not allow.
- Report vulnerabilities privately by email to jason@madebyesco.com. Please do not open public issues for vulnerabilities.
- Isolated browser debugging (if used) must bind to localhost only.
