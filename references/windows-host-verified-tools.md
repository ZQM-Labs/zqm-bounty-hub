# Windows Host Verified Research Tooling

## Dedicated research venv

`C:\Users\zqmco\.hermes\venvs\bounty-hub-research`

Activate:
`C:\Users\zqmco\.hermes\venvs\bounty-hub-research\Scripts\activate`

## Functional verify results

- `httpx`: `0.28.1`, HTTP fetch OK
- `bs4`: `4.15.0`, HTML parse OK
- `mitmproxy`: installed and importable
- `schemathesis`: `4.22.3` installed
- `graphql-core`: `3.2.11` installed
- `openapi-spec-validator` / `openapi-schema-validator`: installed
- `bandit`: `1.9.4`, basic scan needs API-correct invocation
- `scapy`: `2.7.0`, can build packets; live send needs Npcap/admin
- `waybackpy`: `3.0.6` installed
- `truffleHog`: installed; import name is `truffleHog`, not `trufflehog`
- `detect-secrets`: installed; functional scan warning: no plugins loaded unless configured
- `requests-html`: installed; dep bug fixed by `lxml-html-clean`
- `cryptography`: `48.0.1` installed

## Windows blockers / deferred

- `semgrep`: unsupported on Windows via pip; use WSL
- `pocsuite3`: installed but broken on Windows due missing `shellcodes.dotnet`; use WSL
- `gitleaks`: not on PyPI; download official release if needed
- Go-based recon tools: not in venv; install portable or use WSL
- Mobile toolchain (`adb`, `apktool`, `jadx`, `frida`, `objection`, `mobsf`): not installed

## Quick re-verify from activated research venv

```bash
python -c "import httpx, bs4, mitmproxy.http, schemathesis, graphql, openapi_spec_validator, bandit, scapy, waybackpy, truffleHog, detect_secrets, requests_html; print('verified')"
bandit --version
```
