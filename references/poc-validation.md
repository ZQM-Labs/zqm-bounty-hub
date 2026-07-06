# Proof-of-Concept Generation / Safe Exploit Validation

Recommended libraries and tools:
- `pocsuite3` / `xray` / `nuclei` — structured PoC templates and safe validation runners
- `requests` / `httpx` — manual PoC harness construction
- `paramiko` / `socket` — network service validation where explicitly scoped
- `pwntools` — binary/desktop PoC harness construction
- `jwt` / `jwcrypto` — token manipulation without brute-force keys
- `hashlib` / `cryptography` — signing/verification tests
- `flask` / `starlette` / `fastapi` — local isolated target replica for PoC replay
- `mitmproxy` / `scapy` — intercept/packet crafting for network-layer PoCs

Safety rules:
- Validate PoC behavior against local/isolated targets first.
- Never run exploit logic against production systems without explicit consent.
- If the PoC touches sensitive data, use dummy/test accounts/data only.
- Record request IDs, timestamps, and exact state transitions in evidence.
- For authz issues, prefer showing request differences over replaying attack steps.

Windows host tool availability:
- `httpx`/`requests`, `flask`: available for manual PoC harness construction
- `mitmproxy`: installed for request/response replay
- `scapy`: installed, but raw-socket tools often require admin/Npcap on Windows
- `pocsuite3`: installed but broken on Windows due missing `pocsuite3.shellcodes.dotnet` module; use WSL or wait for upstream Windows support
- `jwcrypto`/`jwt`: installed for token inspection/debug
- `pwn`: installed for manual exploit harness construction
- `nuclei`: available for safe template-based validation instead of pocsuite3 where PoC is a known pattern

Evidence requirements:
- Save PoC harness, input, expected output, and actual output.
- Include step numbers and state transitions.
- Redact secrets and user data from all outputs.

Windows notes:
- `pocsuite3` install via `pip`; verify path in active venv.
- `scapy` requires Npcap/WinPcap on Windows for raw socket use.
- `nuclei` binary preferred over template memory limits in long runs.
