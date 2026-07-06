# Source Code Auditing

Recommended libraries and tools:
- `semgrep` — lightweight static analysis and pattern-based audits
- `bandit` — Python-focused static security analysis
- `eslint` / `semgrep rules` — JS/TS pattern audits
- `codeql` / `ql` packs — deeper taint-style auditing where authorized
- `regex`, `ast` stdlib — ad hoc pattern and structure scans
- `tree-sitter` — cross-language parsing for ad hoc AST queries
- `gitpython` / `libgit2` — repository history and commit-range analysis
- `trufflehog`, `gitleaks`, `detect-secrets` — secrets detection in scanned repos

Process defaults:
- Scope audit to in-scope repositories only; respect repository access boundaries.
- Prioritize sensitive handling: auth, session, payments, admin, webhooks, integrations.
- Taint-style queries first where supported; pattern scans as fallback.
- Cross-reference disclosed CVEs/weaknesses from program weakness list against code paths.

Windows host tool availability:
- `bandit`: installed and CLI-verifiable; Python-only audits
- `detect_secrets`/`trufflehog`: installed for repo history/secret scans
- `semgrep`: not available on Windows via pip; use WSL if needed
- `CodeQL`: not installed; use only when explicitly scoped and installed manually
- `tree-sitter`: not installed in this venv
- `regex`/`ast` stdlib: always available as fallback scan primitives

Evidence requirements:
- Record file path, line segment, pattern/rule matched, and impact inference.
- Do not extract secrets even when discovered; report existence and location only.
- Include reducer/heuristic confidence alongside finding.

Windows notes:
- `semgrep` install via `pip`; verify path in active venv.
- `CodeQL` requires manual install; use only when explicitly scoped.
- `gitpython` install via `pip` if repository history automation is needed.
