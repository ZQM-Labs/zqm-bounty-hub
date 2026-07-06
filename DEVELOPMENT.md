# zqm-bounty-hub

Private ZQM Computing skill for bounty program recon, API intel capture, and compliance-aware reporting.

## Branch model

- `master` — protected, deployable/reviewable state
- feature/fix branches off `master`; PR required

## Commit convention

- `chore:` repo/setup/tooling changes
- `fix:` bug fix
- `feat:` new capability
- `refactor:` code shape change without behavioral change
- `docs:` README/process/provenance updates
- `test:` add/update verifier coverage
- `revert:` explicit rollback

## Verification expectation

- Run `scripts/test_h1_api_client.py` before pushing
- Run target scripts end-to-end when changing live API paths
- No secrets in commits; use env/registry for HackerOne token

## Live API boundary

- `/v1/hackers/me` auth state verified externally; code degrades on `401/403`
- Per-program `queryString=team:` may 400 upstream; fallback to global hacktivity
