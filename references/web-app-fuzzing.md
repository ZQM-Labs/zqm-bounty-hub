# Web App Scanning / Fuzzing

Recommended libraries and tools:
- `requests` / `httpx` — HTTP interaction and baseline request crafting
- `urllib` stdlib — fallback HTTP interactions
- `beautifulsoup4` / `lxml` — response parsing and DOM extraction
- `paramiko` / `socket` stdlib — low-level service interaction when needed
- `regex` stdlib — pattern-based response analysis
- `selenium` / `playwright` — browser-rendered interaction where JS-rendered pages differ
- `mitmproxy` / `requests` chains — proxy capture and replay for authenticated surfaces
- `ffuf` / `gobuster` / `dirsearch`-style dir brute only if explicitly scoped
- `arjun` / `x8` / `param-miner`-style parameter discovery only if explicitly scoped

Process defaults:
- Baseline crawl with `requests` + `BeautifulSoup` before any active fuzz.
- Deduplicate parameters and endpoints using deterministic hashes.
- Record exact request/response pairs in evidence outputs.
- Respect robots-equivalent scope boundaries; do not brute exclusions.

Tool availability on this Windows host:
- `httpx`, `bs4`: verified working
- `schemathesis`, `graphql-core`, `openapi-spec-validator`: installed and verified importable
- `mitmproxy`: installed and importable
- `aiohttp`/`aiodns`: installed for async crawling/probing where consent covers it
- `selenium`: installed; optional browser-rendered checks when needed
- `nuclei v3.10.0`, `ffuf v2.1.0`, `subfinder v2.6.4`, `amass v4.2.0`, `katana v1.6.1`: installed as portable Windows binaries at `C:\Users\zqmco\Documents\bounty-tools\`
- `naabu v2.6.1`: portable binary extracted; execution from bash shell blocked due Windows executable/permission behavior; use `cmd.exe /c naabu.exe` for execution
- `wfuzz`, `gobuster`, `dirsearch`, `dalfox`, `XStrike`, `photon`, `sqlmap`: available via Python or not installed in venv; use when explicitly scoped

Evidence requirements:
- Save request/response bodies or hashes for each finding candidate.
- Record exact URL, parameter, payload, and observed behavior.
- Do not store raw secrets; mask Authorization/Cookie values.

Windows notes:
- Install `httpx` / `beautifulsoup4` in the active venv before use.
- Prefer PowerShell/CLI tool installs outside venv only if isolated.
