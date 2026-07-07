# Verified HackerOne Auth and Live Review System

## Canonical auth for `zqm-computing`
- Username: `zqm-computing`
- Secret: `HACKERONE_API_TOKEN` value from Windows user env
- Header: `Authorization: Basic base64("zqm-computing:<token>")`

## Verified endpoint behavior
- `GET /v1/hackers/programs?page[number]=N&page[size]=100` -> 200
  - Pagination: full corpus is 593 programs on this account
  - Expected first-page attrs include `handle`, `name`, `state`, `policy`
  - Scope-aware attrs like `eligible_for_bounty`/`eligible_for_submission` may be null depending on account/program state
- `GET /v1/hackers/payments/earnings?page[number]=1` -> may return 0 items or 400 with invalid params
- `GET /v1/hackers/hacktivity?team=<slug>...` -> `team` filter is unreliable server-side on this account; do not trust it for per-program revenue mapping

## Scripts
- `scripts/rank_programs.py`:
  - canonical ranking runner
  - auth path uses `zqm-computing:<token>`
  - sorts by `local_actionability`, then `estimated_bounty_usd`
  - writes `outputs/ranked_programs.json` and `outputs/ranked_programs.md`
- `scripts/h1_api_client.py`:
  - referenced helper; if absent, use stdlib `urllib`/`base64` with the canonical auth form above

## Review workflow
1. Run ranker: `python scripts/rank_programs.py`
2. Run census if full scope triage is needed: `python <verifier> hermes-verify-h1-all.py` from `AppData\Local\Temp`
3. Use program handles from `/v1/hackers/programs` as the source of truth for slugs
4. Do not use `team=` query results as authoritative per-program amounts

## Troubleshooting
- 401 despite present token:
  - verify Basic auth uses `zqm-computing:<token>`
  - verify token has `hackers:read` scope
  - verify Windows env picked up: use `cmd /c "set HACKERONE_API_TOKEN=<token>&& python scripts/rank_programs.py"`
- Windows shell retains old env after `setx`:
  - restart shell/Hermes session
  - or use `cmd /c` wrapper
- Earnings endpoint returns 400 on invalid params:
  - omit `page[size]`
  - use `page[number]=1` or omit pagination entirely
