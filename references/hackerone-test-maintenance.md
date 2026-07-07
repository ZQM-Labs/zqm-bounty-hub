# HackerOne Client/Test Maintenance Notes

## Stale test signatures after refactor

When `scripts/test_h1_api_client.py` fails after editing `scripts/h1_api_client.py`, usual fixes:

- Missing `_cached_token` → replace with `_load_persisted_token`
- `test_bearer_for_generic_token` failure → current client requires Basic auth; replace with `test_basic_for_generic_token`
- Canonical command on this host: `python scripts/test_h1_api_client.py`

## Verified auth contract

Current live behavior: `_auth_headers_for()` always returns `Basic base64("zqm-computing:<token>")`. Keep tests aligned; do not re-add Bearer expectations unless auth logic changes.
