# ZQM Bounty Hub — Process Review Reference

Run this review when changes land or when a second opinion is needed.

## Review trigger conditions
- New target program added
- Adapter contract changes
- Output directory structure changes
- New auth method or env variable introduced

## Review questions
1. Does this change preserve idempotency?
2. Does this change preserve audit trail completeness?
3. Are credentials still only in environment variables?
4. Are evidence/manifest paths still constrained to OUTPUT_ROOT?
5. Are new target_ids non-colliding across platforms?
6. Are error records emitted for partial failures instead of hard aborts?

## Review acceptance criteria
- All listed constraints in SKILL.md still hold
- No new hardcoded values that break portability
- No outputs written outside OUTPUT_ROOT
- No credentials written to any file/log/response field

## Review report
Record review outcome in `outputs/` with filename `review_<run_id>_<timestamp>.json`:
- reviewer
- trigger
- acceptance: pass/fail/conditional
- findings
- remediation required

