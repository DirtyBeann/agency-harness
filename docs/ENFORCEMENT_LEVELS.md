# Enforcement levels

| Layer | Level |
|---|---|
| Binder CLI / advance | Hard fail (non-zero exit) |
| Verdict schema validation | Hard fail |
| Failure replay / L1 checks | Hard in CI or local smoke |
| Host skill ACL (Kilo deny-default) | Partial if applied |
| SKILL.md text | Advisory |
| Human operator | Final |

Do not claim skills alone enforce policy.
