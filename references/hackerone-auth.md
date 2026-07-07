# HackerOne Auth & API Notes — Local Verified Form

Source: this host, `zqm-computing`, token updated 2026-07-06.

## Auth contract
- Header: `Authorization: Basic base64(zqm-computing:<token>)`
- Username is `zqm-computing`
- Password is the raw API token value
- Do not send token as username or as both username and password

## Verified endpoint behavior
- `GET /v1/hackers/programs?page[number]=N&page[size]=100` -> 200
  - Pagination: full corpus is 593 programs on this account
  - Expected first-page attrs include `handle`, `name`, `state`, `policy`
  - Scope-aware attrs like `eligible_for_bounty`/`eligible_for_submission` may be null depending on account/program state
- `GET /v1/hackers/payments/earnings?page[number]=1` -> may return 0 items or 400 with invalid params
- `GET /v1/hackers/hacktivity?team=<slug>...` -> `team` filter is unreliable server-side on this account; do not trust it for per-program revenue mapping

## Verified caller bug to avoid
- `/v1/hackers/payments/earnings` rejects `page[size]=200` with HTTP 400: `Invalid Parameter`
- Prefer omitting `page[size]` or using the API’s default page size
- Pagination, if needed, should use only `page[number]`
- `/v1/hackers/hacktivity` may ignore `team=` filter; do not use it for per-program revenue mapping

## Fallback ranking behavior
- When earnings/hacktivity calls return 401/400/empty, use local target notes and disclosed bounty examples
- Ranked outputs should keep `data_source` explicit so callers know whether the amount is live or fallback
- Sort order: `local_actionability`, then `estimated_bounty_usd`, both descending

## Scripts
- `scripts/rank_programs.py`:
  - canonical ranking runner
  - auth path uses `zqm-computing:<token>`
  - writes `outputs/ranked_programs.json` and `outputs/ranked_programs.md`
- Census verifier: `C:\Users\zqmco\AppData\Local\Temp\hermes-verify-h1-all.py`
  - writes `C:\Users\zqmco\AppData\Local\Temp\outputs\h1_all_programs_summary.json`
  - use for full program census with live pagination

## Review workflow
1. Run ranker: `python scripts/rank_programs.py`
2. Run census if full scope triage is needed: `python hermes-verify-h1-all.py` from `AppData\Local\Temp`
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

## Environment quirk observed
- For platform API checks, prefer direct Python with headers built from env var rather than browser MCP
- This avoids local browser-stack failures caused by Node/npm path/config issues
