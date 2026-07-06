# ZQM Bounty Hub — Multi-Checker Ethics Reference

Guidance for using multiple vulnerability checkers against the same target/target_id.

## Ethics
- No automated unlimited-pass scanning outside authorized scope
- No aggressive retries against the same endpoint without rate-limit discipline
- No mass credential stuffing style checks
- Do not assume findings from one checker implies entitlement to another

## Workflow
- Run one checker at a time unless explicit parallel authorized
- Collate evidence into separate files per checker
- Deduplicate findings at claim assembly stage; use deterministic hashes
- Record checker identity in evidence filename
