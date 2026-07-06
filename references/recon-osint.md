# Recon / OSINT

Recommended libraries and tools:
- `requests` / `httpx` — HTTP-based asset discovery
- `shodan` / `censys` / `securitytrails` / `whois` / `dnsdumpster` — passive asset discovery
- `amass` / `subfinder` / `assetfinder` — active/passive subdomain enumeration
- `theHarvester` — email/subdomain/ASN intelligence
- `waybackpy` / `waybackurls` / ` gau` — historical URL recovery
- `katana` / `gospider` / `hakrawler` — endpoint/crawl discovery
- `trufflehog` / `gitLeaks` — secrets in public repo history
- `builtwith` / `wappalyzer` — technology fingerprinting
- `crtsh` / `crt.sh` / `certstream` — certificate transparency enumeration
- `dnsx` / `massdns` / `resolve` — DNS resolution and wildcard detection

Process defaults:
- Start with passive-only recon; move active only if in-scope and authorized.
- Scope by program-owned domains/IPs; do not enumerate unrelated assets.
- Deduplicate by normalized hostname and scheme.
- Timestamp all recon snapshots for reproducibility.

Windows host tool availability:
- `httpx`/`requests`, `aiohttp`/`aiodns`, `aiofiles`, `waybackpy`: installed and verified
- `waybackurls`/`gau`, `amass`, `subfinder`, `katana`, `hakrawler`, `dalfox`, `nuclei`: not in venv; install portable Go binaries or use WSL
- `shodan`/`censys`: installed; require separate platform API keys
- `trufflehog`/`detect_secrets`: installed for repo/history secret scans
- `theHarvester`, `dnsx`, `massdns`, `naabu`: not installed
- `sublist3r`/`knockpy`: PyPI attempts are unreliable on current toolchain; retry via WSL if needed
- `certstream`/`crtsh`: use passive web/API only unless explicitly scoped

Evidence requirements:
- Save source, query, and raw output for each recon item.
- Normalize hostnames and mark wildcard findings separately.
- Do not store third-party data beyond what is needed for finding provenance.

Windows notes:
- Go-based tools (`amass`, `subfinder`, `katana`) need portable binaries or WSL.
- `waybackpy` requires Python venv install.
- `shodan`/`censys` CLIs need API keys outside the hub per-platform auth scope.
