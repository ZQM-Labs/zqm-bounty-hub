# Research Library References

This directory contains reference guidance for the active research tooling domains required by `zqm-bounty-hub`. Each file lists recommended libraries, canonical tools, safe defaults, and evidence-capture requirements for that domain.

Files:
- `web-app-fuzzing.md` — web app scanning/fuzzing libs and tooling
- `mobile-app-testing.md` — mobile app testing libs and workflow notes
- `api-security-testing.md` — REST/GraphQL/API security testing libs
- `source-code-auditing.md` — SAST/source review libs and semgrep/pattern notes
- `recon-osint.md` — recon and OSINT libs/commands
- `poc-validation.md` — safe PoC generation and exploit validation libs/process

Tooling status summary:
- Installed and verified on Windows: httpx, bs4, requests_html, mitmproxy, schemathesis, graphql-core, openapi-spec-validator, bandit, scapy, waybackpy, truffleHog, detect-secrets, aiohttp, aiodns, aiofiles, PyJWT, jwcrypto, pwn, tree-sitter, python-nmap, selenium, shodan, censys, xsstrike, sqlmap, photon, frida, frida-tools, objection
- Portable Windows binaries: nuclei v3.10.0, ffuf v2.1.0, subfinder v2.6.4, amass v4.2.0, katana v1.6.1, naabu v2.6.1
- Android toolchain: adb v1.0.41, jadx v1.5.1 with JRE 21, apktool v2.9.3 at `C:\Users\zqmco\Documents\bounty-tools\_android\`
- Known blockers: semgrep unavailable on Windows; pocsuite3 import blocked on Windows; WSL not enabled/admins unavailable; Npcap not installed

## Portable Windows Binary Path

Verified portable scanner directory:
- `C:\Users\zqmco\Documents\bounty-tools\`

Verified binaries:
- `nuclei.exe`
- `ffuf.exe`
- `subfinder.exe`
- `amass.exe`
- `katana.exe`

Usage rule:
- Add `C:\Users\zqmco\Documents\bounty-tools\` to PATH for these tools.
- Run from cmd.exe if git-bash execution permission issues occur.
- For naabu and other ProjectDiscovery tools, if bash reports permission denied, extract via Python zipfile and run via cmd.exe/PowerShell.
