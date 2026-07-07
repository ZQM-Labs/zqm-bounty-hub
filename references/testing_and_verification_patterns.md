# Testing and Verification Patterns

Session note: this host does not ship a `scripts/run_tests.sh` for `zqm-bounty-hub`.

Preferred verification flow:
```bash
cd scripts
find . -name '__pycache__' -type d -exec rm -rf {} +
find . -name '*.pyc' -delete
python -m py_compile h1_api_client.py test_h1_api_client.py <other scripts...>
python test_h1_api_client.py
```

## Windows pyc caching pitfall

After editing `h1_api_client.py`, `test_h1_api_client.py` may still import stale symbols from `__pycache__` on Windows. Always clear `__pycache__` and `*.pyc` before re-running tests. If tests fail with `AttributeError: module 'h1_api_client' has no attribute '_auth_headers_for'` despite the source containing that symbol, likely cause is cached `.pyc`.

## Auth surface sanity check

Before assuming the client regressed, inspect the module surface directly:
- `_auth_headers_for(token)` builds Basic/Bearer per token shape
- `auth_headers()` reads current resolved token via `_token()`
- `_check_response(body)` raises on `401`/`403`
- `TOKEN_CACHE_PATH` may or may not be present depending on variant; do not hard-code tests around it
- `hacktivity_program("cloudflare")` may return `400` from server; verify via code-constant inspection, not live call

## CLI stability

- `python scripts/compliance_check.py --help` must print `--payload`, `--output-root`, and `--json`
- Ad hoc verification via throwaway script at skill root is supported, but cleanup that file afterward to avoid committing test stubs.

## Process preference

If the user asks for verification and `scripts/run_tests.sh` is missing, do not claim the work is fully verified.
Say the concrete blocker instead, then continue with available verification (CLI checks, compiles, or scratch script evidence).