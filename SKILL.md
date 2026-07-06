---
name: zqm-bounty-hub
description: "Automation workflows for platform verification, claim processing, bounty tracking, and GitHub automation. Use when executing repeatable security/verification runs, parsing platform responses, or managing claim evidence chains. Core constraints: authorized scope only, verified findings only, no destructive testing, no fabricated reports."
version: 1.2.1
author: ZQM Computing
license: MIT
category: zqm-bounty-hub
metadata:
  hermes:
    tags: [bounty, verification, github, automation, claims, evidence, audit, security, platform-adapters, compliance, legal]
required_commands: []
required_environment_variables: []
missing_required_environment_variables: []
missing_required_commands: []
setup_needed: false
setup_skipped: false
readiness_status: available
linked_files: {}
---

# ZQM Bounty Hub

Automation workflows for platform verification, claim processing, bounty tracking, and GitHub automation.

## Core Compliance Layer

This skill binds platform adapters to explicit findings-based constraints. These rules are not optional guidance:

- No fabricated or synthetic reports.
- No speculative PoC narratives.
- No speculative title / weakness / scope mapping without verified evidence.
- Only real identified findings, real identified scope, and real identified weakness IDs may be used for reporting.
- Submission is allowed only after reproduction, impact statement, remediation, and explicit user approval.

## Compliance and Conduct

Yes, absolutely. Here are the critical "Do Nots" that will get you banned or create legal exposure. These are binding constraints, not advice:

### Technical Violations
- Do NOT access data you're not authorized to access — even if you find an open database, accessing it beyond proof of concept is illegal.
- Do NOT modify, delete, or exfiltrate data — demonstration only; destruction/theft is not permitted.
- Do NOT disrupt services or cause denial of service — testing impact is different from taking down production.
- Do NOT move laterally into unscoped systems — stay within the defined program scope only.
- Do NOT brute-force credentials — unless explicitly authorized in scope.

### Submission and Disclosure
- Do NOT submit duplicate reports — check existing reports before submission.
- Do NOT publicly disclose before the program authorizes it — responsible disclosure is mandatory.
- Do NOT submit false or inflated severity claims — accurate impact reporting is required.
- Do NOT spam low-quality reports — programs blacklist repeat offenders.
- No public disclosure before vendor patch/fix per program policy.
- Respect coordinated disclosure timelines and program-specific Terms of Service.

### Behavioral
- Do NOT harass or threaten the program — professional communication only.
- Do NOT use found vulnerabilities for personal gain outside the bug bounty — that is criminal exploitation.
- Do NOT sell or share the vulnerability with third parties — it is exclusive to the program until disclosure.
- No automated unlimited scans or mass credential stuffing.

### Scope and Authorization
- Do NOT test subdomains or systems not explicitly listed — inclusion of a root domain does not imply subdomains, internal systems, or third-party vendor systems are in scope.
- Do NOT assume older or forgotten domains/systems are in scope — ask first.
- Do NOT test social engineering or phishing — unless specifically authorized in writing.
- Do NOT target employee systems or internal infrastructure — even if you discover them.

### Reporting Integrity
- Do NOT embellish or exaggerate technical details — truthfulness is required.
- Do NOT submit the same vulnerability under different names/angles — programs track this as gaming.
- Do NOT ignore the program's preferred disclosure timeline — if they say 90 days, do not go public at 89.

### Interaction
- Do NOT demand bounties or threaten disclosure — coercion is extortion.
- Do NOT bypass the official program and contact executives directly — use official channels only.
- Do NOT use vulnerability information for leverage in salary/job negotiations — misuse is prohibited.

### Post-Disclosure
- Do NOT continue testing after disclosure is coordinated — authorization ends upon coordinated disclosure.
- Do NOT publish exploit code before patches are deployed — increases attack surface for others.
- Do NOT use the vulnerability as a portfolio piece before public acknowledgment — wait for formal disclosure.

### Quality and Consistency
- Do NOT submit reports that read like copy-pasted vulnerability scanner output — programs track this as low-quality.
- Do NOT go silent after submitting high-value findings — prompt, clear communication is required.
- Do NOT submit reports with internally inconsistent technical claims — ensure understanding matches evidence.

### General Rule
If you are asking "is this okay?" — you should not do it. When in doubt, reading and testing only is permitted; no data access, modification, or service disruption. Programs explicitly define scope; stay within it.

## Adapter Enforcement

Platform adapters implement these rules as code-level checks:
- Scope validation before execution
- Rate-limit discipline with explicit backoff on 429
- Evidence hashing for deterministic deduplication
- Manifest schema validation
- Unverified platforms emit `unsupported_platform` rather than attempting operations

Violations detected in adapters cause immediate failure with clear diagnostic output, not silent acceptance.

## What is this?

ZQM Bounty Hub is a structured, auditable framework for managing bug bounty research across multiple platforms. It provides:
- Standardized target registry for HackerOne, Bugcrowd, and Intigriti
- **Hardcoded compliance enforcement at adapter and orchestrator level**
- Review gates and quality checks before any execution
- Idempotent evidence and manifest output contracts
- Platform adapter wiring for orchestrated runs
- Windows-specific guidance and safety patterns

## Quick Start

### 1. Prerequisites

- Python 3.9+
- Windows 10/11 or Linux/macOS
- Git Bash/PowerShell with Python access
- Optional: `zqm-parallel-runner` and `zqm-gpu-accelerator` runtime packages
- Research tooling venv: `C:\\Users\\zqmco\\.hermes\\venvs\\bounty-hub-research`

### 2. Authorize Scope

Before any adapter run, confirm authorized scope for the target program and persist credentials at Windows user scope:
```powershell
[System.Environment]::SetEnvironmentVariable('HACKERONE_API_TOKEN', '<value>', 'User')
[System.Environment]::SetEnvironmentVariable('INTIGRITI_API_KEY', '<value>', 'User')
```

HackerOne adapter auth contract:
- Identifier checked in Artemis shell; on this account use `zqm-computing`.
- Adapter reads required secrets from `adapter-routing.json` `required_secrets`.
- Optional secure fallback files are recorded in `optional_secret_files`.
- No plaintext secrets are stored in `zqm-bounty-hub` skill manifests.

Never embed credentials in adapters, configs, or logs. Rotate any token that appears in artifacts.

### 3. Review Targets

Inspect target files before execution:
- `targets/hackerone_targets.json`
- `targets/bugcrowd_targets.json`
- `targets/intigriti_targets.json`

Each target includes `program_slug`, `scope_url`, `check_types`, `severity_focus`, and `review_tags`. Verify:
- Targets are within authorized scope
- `program_slug` maps to an actual program
- `check_types` are supported by the platform adapter
- No placeholder targets remain unless explicitly approved

### 4. Review Routing

Check `adapter-routing.json` for:
- Platform-to-auth-env mapping
- Review policies and constraints per platform
- Output root configuration

### 4b. Research Tooling

This skill includes reference plans for web/app/API/recon/source/PoC testing. On this Windows host, use the dedicated research venv unless otherwise noted:

`C:\Users\zqmco\.hermes\venvs\bounty-hub-research`

Activate with:
```bash
C:\Users\zqmco\.hermes\venvs\bounty-hub-research\Scripts\activate
```

Verified research tooling repertoire

Verified research venv:
- Path: `C:\Users\zqmco\.hermes\venvs\bounty-hub-research`
- Activate: `C:\Users\zqmco\.hermes\venvs\bounty-hub-research\Scripts\activate`

Python libs verified working:
- HTTP/HTML/recon/API: `httpx`, `bs4`, `requests_html`, `aiohttp`, `aiodns`, `aiofiles`, `waybackpy`
- API security: `schemathesis`, `graphql-core`, `openapi-spec-validator`, `mitmproxy`
- Auth/token tests: `PyJWT`, `jwcrypto`, `cryptography`
- Source/secrets: `bandit`, `truffleHog`, `detect-secrets`
- Network/crawl: `scapy`, `python-nmap`, `selenium`
- Recon intel: `shodan`, `censys`
- Web app: `xsstrike`, `sqlmap`, `photon`
- Mobile/runtime: `frida`, `frida-tools`, `objection`
- Binary/desktop: `pwn`, `pwntools`, `tree-sitter`, `pyelftools`

Portable Windows binaries verified:
- `C:\Users\zqmco\Documents\bounty-tools\nuclei.exe`
- `C:\Users\zqmco\Documents\bounty-tools\ffuf.exe`
- `C:\Users\zqmco\Documents\bounty-tools\subfinder.exe`
- `C:\Users\zqmco\Documents\bounty-tools\amass.exe`
- `C:\Users\zqmco\Documents\bounty-tools\katana.exe`
- Naabu v2.6.1 extracted via Python; executable launch from bash is unreliable on this host; use PowerShell/cmd execution if needed

Android/mobile host tooling:
- `adb`, `jadx`, `apktool`, and Temurin JRE 21 installed under `C:\Users\zqmco\Documents\bounty-tools\_android\`

Known blockers / boundary conditions:
- `semgrep`: not available on Windows via pip; use WSL or manual pattern review with `bandit`+stdlib
- `pocsuite3`: Windows import failure due missing `shellcodes.dotnet`; use WSL or manual harnesses
- WSL is not installed on this host, so Semgrep/PoCWSL paths are blocked until WSL is enabled
- `scapy` live send needs Npcap on Windows
- Burp/ZAP absent; `mitmproxy` available for capture/replay only
- `naabu` requires non-bash execution on this host
### 5. Run Execution

Invoke via orchestrator:
```bash
python orchestrator.py --payload payload.json --engine thread --workers 2
```

Or run a single adapter directly:
```python
from adapters.hackerone_adapter import run as h1_run
result = h1_run("h1_shopify", "web_app", {})
print(result["status"], result["result_hash"])
```

### 5b. Compliance Checks

Before and after runs, use the compliance checker:
```bash
python scripts/compliance_check.py --payload payload.json
python scripts/compliance_check.py --payload payload.json --json
python scripts/compliance_check.py --output-root outputs
python scripts/compliance_check.py --output-root outputs --json
```

Review the output before any submission or release.

## Output Structure

```
outputs/
  evidence/
    <run_id>_<task_id>_raw.json
  manifests/
    <run_id>_<platform_id>_manifest.json
```

### Evidence file format
JSON only. Must include:
- `platform`
- `target_id`
- `check_type`
- `status`
- `result_hash` (SHA-256[:16])
- `timestamp` (ISO-8601 with timezone)
- `requires_auth`
- `body`
- `headers` (masked)

### Manifest file format
JSON only. Appended; never overwritten. Must include:
- `run_id`
- `platform`
- `result_count`
- `result_hash`
- `provider`
- `device_name`
- `fallback_used`
- `timestamp`

## Target Registry Schema

Each `targets/*_targets.json` file:
```json
{
  "platform_id": "hackerone",
  "auth_env": "HACKERONE_API_TOKEN",
  "default_output_root": "...",
  "review_policy": {},
  "targets": [
    {
      "target_id": "h1_shopify",
      "program_name": "Shopify",
      "program_slug": "shopify",
      "asset_type": "web_platform",
      "scope_summary": "Shopify merchant and admin web surfaces",
      "scope_url": "https://hackerone.com/shopify",
      "check_types": ["web_app", "api"],
      "severity_focus": ["critical", "high", "medium", "low", "informative"],
      "reported_bounty_examples": [],
      "review_tags": ["ecommerce", "merchant", "admin"],
      "notes": "Informative-class findings often disclosed; cash bounty scales with impact"
    }
  ]
}
```

## Adapter Contract

Every platform adapter must expose:
- `run(target_id, check_type, parameters) -> Dict[str, Any]`
- `supports(check_type) -> bool` (optional)
- `validate(parameters) -> None` (optional)

Return envelope fields:
- `platform`
- `target_id`
- `check_type`
- `status`
- `body`
- `headers`
- `timestamp`
- `requires_auth` (bool)
- `result_hash` (SHA-256[:16], deterministic)

On unsupported `check_type`, return:
```json
{
  "status": "unsupported",
  "body": {"supported": ["web_app", "api"]}
}
```

## Review Checklist

Before every run:
- [ ] Loaded target payload from `targets/*_targets.json`
- [ ] Target IDs are distinct per platform/check
- [ ] No credential leakage in logs/artifacts
- [ ] Auth env vars present and non-empty
- [ ] `output_root/evidence/` and `output_root/manifests/` writable
- [ ] No prior evidence for identical `run_id` + `task_id` without explicit overwrite policy
- [ ] Platform rate limits respected
- [ ] Windows path/pathlib/locking/antivirus mitigations in place if on Windows
- [ ] **FINDINGS VERIFIED: any proposed report payload is based on actual reproduction, not speculation**
- [ ] **AUTHORIZED SCOPE: target asset is within verified `structured_scope_id` for the program**
- [ ] **SEVERITY CONSISTENT: reported severity matches actual impact, not inflated**
- [ ] **NO DUPLICATES: similar issues not already reported or disclosed in hacktivity**
- [ ] **EVIDENCE INTEGRITY: PoC is minimal-impact, non-destructive, no data exfiltration**
- [ ] **LEGAL COMPLIANCE: no unauthorized access, no lateral movement, no service disruption**

## Platform Review Policies

- **HackerOne**: No public disclosure before patch. Respect rate limits. Do not disrupt service.
- **Bugcrowd**: Managed programs require adherence to CrowdMatch/reporting rules. Do not disrupt service.
- **Intigriti**: EU/GDPR constraints apply. Do not exfiltrate personal data. Scope by DNS names only.

## Execution Preferences

- Operate in verified-only mode unless explicit scope or authorization is confirmed.
- Rank targets first, then execute only after scope/platform policy review.
- Do not proceed with assumed auth, assumed scopes, or assumed tool coverage.
- Use git-bash syntax on Windows. No pwsh/WMIC/no shell job control.
- Long operations: use background execution with notification/audit trail, not blind waits.
- Prefer zero-cost fixes first; only add packages/tools when they close an actual gap.
- Keep secrets in Windows user env/registry only; never embed in manifests or logs.

## Verified Research Tooling Repertoire

Verified research venv:
- Path: `C:\Users\zqmco\.hermes\venvs\bounty-hub-research`
- Activate: `C:\Users\zqmco\.hermes\venvs\bounty-hub-research\Scripts\activate`

Python libs verified working:
- HTTP/HTML/recon/API: `httpx`, `bs4`, `requests_html`, `aiohttp`, `aiodns`, `aiofiles`, `waybackpy`
- API security: `schemathesis`, `graphql-core`, `openapi-spec-validator`, `mitmproxy`
- Auth/token tests: `PyJWT`, `jwcrypto`, `cryptography`
- Source/secrets: `bandit`, `truffleHog`, `detect-secrets`
- Web app: `xsstrike`, `sqlmap`, `photon`
- Mobile/runtime: `frida`, `frida-tools`, `objection`
- Binary/desktop: `pwn`, `pwntools`, `tree-sitter`, `pyelftools`

Portable Windows binaries verified:
- `C:\Users\zqmco\Documents\bounty-tools\nuclei.exe`
- `C:\Users\zqmco\Documents\bounty-tools\ffuf.exe`
- `C:\Users\zqmco\Documents\bounty-tools\subfinder.exe`
- `C:\Users\zqmco\Documents\bounty-tools\amass.exe`
- `C:\Users\zqmco\Documents\bounty-tools\katana.exe`
- Naabu v2.6.1 extracted via Python; executable launch from bash is unreliable on this host; use PowerShell/cmd execution if needed

Android/mobile host tooling:
- `adb`, `jadx`, `apktool`, and Temurin JRE 21 installed under `C:\Users\zqmco\Documents\bounty-tools\_android\`

Known blockers / boundary conditions:
- `semgrep`: not available on Windows via pip; use WSL or manual pattern review with `bandit`+stdlib
- `pocsuite3`: Windows import failure due missing `shellcodes.dotnet`; use WSL or manual harnesses
- WSL is not installed on this host, so Semgrep/PoCWSL paths are blocked until WSL is enabled
- `scapy` live send needs Npcap on Windows
- Burp/ZAP absent; `mitmproxy` available for capture/replay only
- `naabu` requires non-bash execution on this host
- Use `pathlib.Path` for all path operations.
- Write evidence to `.tmp` then atomically rename to avoid AV corruption.
- Lock manifest appends with retry/backoff or advisory lock file.
- Keep `OUTPUT_ROOT` inside user-writable paths; avoid system temp directories.

## Multi-Checker Ethics

- Run one checker at a time unless parallel authorized.
- Deduplicate findings using deterministic hashes.
- Record checker identity in evidence filenames.
- No automated unlimited scans or mass credential stuffing.

## Network Notes

- Scope by DNS name, not IP history.
- Avoid mass DNS enumeration unless explicitly scoped.
- Multi-region endpoints need cache/TTL handling.

## Troubleshooting

### Adapter returns `unsupported`
Verify `check_type` exists in the target's `check_types[]` and the platform adapter supports it.

### Credential in logs
Mask all `api_key`, `token`, `secret`, `password` fields. Rotate exposed token immediately.

### Manifest append fails on Windows
Use retry with backoff or advisory lock file within `OUTPUT_ROOT`.

### Evidence file empty/corrupt
Real-time AV may interfere. Use atomic rename from `.tmp`.

## Documentation References

- `references/hackerone-auth-real.md` — Windows token-source precedence and fallback chain notes
- `references/hackerone-auth.md` — canonical HackerOne auth contract notes
- `references/hackerone-code-of-conduct.md` — full Code of Conduct fetched 2026-07-06
- `references/hackerone-community-terms.md` — Community Member Terms and Conditions fetched 2026-07-06
- `references/hackerone-general-terms.md` — General Terms and Conditions fetched 2026-07-06
- `references/testing_and_verification_patterns.md` — host verification notes and pytest quirks

## Legal / Safe Harbor

All runs must comply with:
- Program-specific Terms of Service
- Coordinated Vulnerability Disclosure expectations
- Do-not-disrupt / do-not-exfiltrate principles
- No public disclosure before vendor patch/fix

This skill does not provide legal advice. Consult each program's governing docs for enforceable terms.

## Files Created / Modified

See the canonical skill tree:
`C:\\Users\\zqmco\\.hermes\\shared\\skills\\zqm-bounty-hub\\`
