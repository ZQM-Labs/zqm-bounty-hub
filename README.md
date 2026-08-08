# ZQM Bounty Hub

[![CI](https://github.com/ZQM-Labs/zqm-bounty-hub/actions/workflows/ci.yml/badge.svg)](https://github.com/ZQM-Labs/zqm-bounty-hub/actions/workflows/ci.yml) [![Tests](https://github.com/ZQM-Labs/zqm-bounty-hub/actions/workflows/tests.yml/badge.svg)](https://github.com/ZQM-Labs/zqm-bounty-hub/actions/workflows/tests.yml) [![Ruff](https://github.com/ZQM-Labs/zqm-bounty-hub/actions/workflows/ci.yml/badge.svg)](https://github.com/ZQM-Labs/zqm-bounty-hub/actions/workflows/ci.yml) [![mypy](https://github.com/ZQM-Labs/zqm-bounty-hub/actions/workflows/ci.yml/badge.svg)](https://github.com/ZQM-Labs/zqm-bounty-hub/actions/workflows/ci.yml)


Automation workflows for platform verification, claim processing, bounty tracking, and GitHub automation.

## What is this?

ZQM Bounty Hub is a structured, auditable framework for managing bug bounty research across multiple platforms. It provides:
- Standardized target registry for HackerOne, Bugcrowd, and Intigriti
- Review gates and quality checks before any execution
- Idempotent evidence and manifest output contracts
- Platform adapter wiring for orchestrated runs
- Windows-specific guidance and safety patterns

## Quick Start

### 1. Prerequisites

- Python 3.9+
- Windows 10/11 (tested) or Linux/macOS
- Git Bash or PowerShell with Python access
- Optional: `zqm-parallel-runner` and `zqm-gpu-accelerator` runtime packages

### 2. Authorize Scope

Before any adapter run, confirm authorized scope for the target program:
```powershell
$env:HACKERONE_API_TOKEN = "your_token"
$env:BUGCROWD_API_KEY = "your_key"
$env:INTIGRITI_API_KEY = "your_key"
```

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
- Reivew policies and constraints per platform
- Output root configuration

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

## Platform Review Policies

- **HackerOne**: No public disclosure before patch. Respect rate limits. Do not disrupt service.
- **Bugcrowd**: Managed programs require adherence to CrowdMatch/reporting rules. Do not disrupt service.
- **Intigriti**: EU/GDPR constraints apply. Do not exfiltrate personal data. Scope by DNS names only.

## Windows Handling

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

## Legal / Safe Harbor

All runs must comply with:
- Program-specific Terms of Service
- Coordinated Vulnerability Disclosure expectations
- Do-not-disrupt / do-not-exfiltrate principles
- No public disclosure before vendor patch/fix

This skill does not provide legal advice. Consult each program's governing docs for enforceable terms.

## Documentation References

- `references/integration-patterns.md` — orchestrator wiring and parallel execution patterns
- `references/review-checklist.md` — pre/during/post flight checklist
- `references/process-review.md` — change review criteria
- `references/review-clarity.md` — review-worthy finding/suggestion criteria
- `references/multi-checker-notes.md` — ethics for multiple checker workflows
- `references/network-notes.md` — boundary and DNS scoping notes
- `references/windows-handling.md` — Windows-specific path, caching, AV, and locking notes

## Files Created / Modified

See the canonical skill tree:
`C:\Users\zqmco\.hermes\shared\skills\zqm-bounty-hub\`

## Related Repositories

- [ZQM-Labs/zqm-auth](https://github.com/ZQM-Labs/zqm-auth) — bug-bounty auth toolkit: token lifecycle and platform integration
- [ZQM-Labs/bounty-tools](https://github.com/ZQM-Labs/bounty-tools) — HackerOne, GitLab, Shopify target intelligence utilities
- [ZQM-Labs/zqm-sword](https://github.com/ZQM-Labs/zqm-sword) — endpoint defense and offensive security tooling for Windows
- [ZQM-Labs/zqm-localhost-findings](https://github.com/ZQM-Labs/zqm-localhost-findings) — service discovery and Windows endpoint security assessment
- [ZQM-Computing/mesh-forensics](https://github.com/ZQM-Computing/mesh-forensics) — ZQM LAN evidence collection and incident response
- [ZQM-Labs/zqm-local-tools](https://github.com/ZQM-Labs/zqm-local-tools) — local-first security and assessment utilities
