# ZQM Bounty Hub — Review Checklist Reference

Use this checklist before, during, and after every adapter run.

## Pre-flight
- [ ] Target payload loaded from `targets/*_targets.json`
- [ ] Target IDs formatted per audit block
- [ ] Auth environment variables present and non-empty
- [ ] No credentials in logs/artifacts/output
- [ ] Privacy-redaction enabled

## Payload design
- [ ] Distinct target IDs across all platforms/checks
- [ ] No target_id reuse between HackerOne, Bugcrowd, Intigriti
- [ ] Checks list matches targets list deterministically

## Execution
- [ ] `output_root/evidence/` writable
- [ ] `output_root/manifests/` writable
- [ ] Adapter.run() exception caught per task
- [ ] Evidence written synchronously after each adapter call
- [ ] Result hash deterministic SHA-256[:16]
- [ ] Appending manifest records; no overwrites

## Post-run
- [ ] Review manifest: result_count, result_hash, fallback_used, provider
- [ ] Review evidence: per-task status, no credential leaks
- [ ] Review error records: did any platform fail entirely?
- [ ] Audit trail timestamped and complete

## Platform-specific checks
- [ ] HackerOne: rate limits respected, no public disclosure before patch
- [ ] Bugcrowd: CrowdMatch/reporting rules respected if enabled
- [ ] Intigriti: EU/GDPR constraints respected; no third-party data exposure
