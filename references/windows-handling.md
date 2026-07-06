# ZQM Bounty Hub — Windows Handling Reference

Windows-specific guidance for running evidence/manifests workflows.

## Path handling
- Use `pathlib.Path` instead of manual `os.path.join` to avoid mixed separator bugs
- Prefer POSIX-style forward slashes in JSON config files; Python tools accept them on Windows

## Caching
- Keep OUTPUT_ROOT inside user writable paths
- Avoid global temp dirs unless intentionally ephemeral

## Antivirus
- Real-time scanning can corrupt partially written evidence files during rapid adapter runs
- Mitigation: write to `.tmp` file then atomically rename; do not leave partial evidence files in queue state after crash

## File locking
- Manifest append operations may fail under concurrent writer; wrap writes in retry with backoff or use advisory lock file within OUTPUT_ROOT
