# Excluded from this universal package

These stay in a private farm install and must not be copied into public/share zips:

## Secrets and host config
- Live subscription pool maps and SHA locks
- LLM gateway IPs/ports and API keys
- Host agent configs and credential stores
- Private vault paths and sync scripts

## Product-specific lore
- Named commercial products / repos beyond generic `dev`/`main` examples
- PHI / compliance runbooks tied to a single company
- Named operator roster as hard dependencies

## Non-portable ops surfaces
- Live ledger history and run transcripts
- Private workbench status tied to one machine
- Promptfoo configs pointing at private providers
- Third-party CC-BY skill text shipped as if proprietary

## Patterns documented, not farm bits
- Deny-default skill ACL
- Same-subscription-pool illegal hop
- Fail-closed verdict gates
- Redact-by-default ledger
