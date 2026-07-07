"""zqm-bounty-hub compliance checker."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_ROOT = SKILL_DIR / "outputs"


def _normalize(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"```.*?```", " ", lowered, flags=re.DOTALL)
    lowered = re.sub(r"`[^`]*`", " ", lowered)
    lowered = re.sub(r"[#*_\-]{1,}", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered

# Prohibited content markers
PROHIBITED_PHRASES = [
    "fabricated",
    "synthetic",
    "speculative",
    "assumed",
    "hypothetical",
    "unverified",
    "example",
    "sample",
    "dummy",
    "placeholder",
    "test data only",
]

# Severity-inflation markers
INFLATED_PHRASES = [
    "remote code execution",
    "full account takeover",
    "complete compromise",
    "arbitrary code execution",
    "sql injection",
    "ssrf to metadata",
    "cloud metadata",
    "aws keys",
    "admin API access",
]

# Copy-pasted scanner output markers
SCANNER_PHRASES = [
    "nuclei template",
    "nessus",
    "qualys",
    "tenable",
    "nexpose",
    "rapid7",
    "netsparker",
    "insvm",
    "vulners",
    "nikto",
    "dirbuster",
    "gobuster",
    "wpscan",
    "owasp zap",
    "burp suite professional",
    "acunetix",
    "appscan",
    "openvas",
    "polarity",
    "vulnwhisperer",
    "spiderfoot",
]

# Inconsistent technical claim markers - claims without evidence patterns
UNSUPPORTED_CLAIM_PATTERNS = [
    "full database dump",
    "all user passwords",
    "all sessions hijacked",
    "bypassed authentication without interaction",
    "bypassed mfa completely",
]


def check_report_quality(text: str) -> List[str]:
    """Check for low-quality/scanner-copied report language."""
    issues = []
    lowered = text.lower()
    for phrase in SCANNER_PHRASES:
        if phrase in lowered:
            issues.append(f"Report appears to copy scanner output: {phrase}")
    return issues


def check_technical_consistency(text: str) -> List[str]:
    """Check for inconsistent technical claims without supporting evidence language."""
    issues = []
    lowered = text.lower()
    for phrase in UNSUPPORTED_CLAIM_PATTERNS:
        if phrase in lowered:
            issues.append(f"Unsupported technical claim without evidence: {phrase}")
    return issues


def check_report_payload(payload: Dict[str, Any]) -> List[str]:
    """Validate a draft report payload against compliance rules."""
    issues: List[str] = []
    attrs = payload.get("data", {}).get("attributes", {})
    text_blobs = [
        attrs.get("title", ""),
        attrs.get("vulnerability_information", ""),
        attrs.get("impact", ""),
    ]
    text = "\n".join(text_blobs)
    normalized = _normalize(text)

    issues.extend(_check_prohibited_content(normalized))
    issues.extend(_check_severity_inflation(normalized))
    issues.extend(_check_scope_boundary_violations(normalized))
    issues.extend(_check_disclosure_violations(normalized))
    issues.extend(_check_behavioral_violations(normalized))
    issues.extend(_check_interaction_violations(normalized))
    issues.extend(_check_post_disclosure_violations(normalized))
    issues.extend(_check_general_rule_violations(normalized))
    issues.extend(check_report_quality(normalized))
    issues.extend(check_technical_consistency(normalized))

    if not attrs.get("team_handle"):
        issues.append("Missing team_handle")

    if not attrs.get("structured_scope_id"):
        issues.append("Missing structured_scope_id")

    if not attrs.get("weakness_id"):
        issues.append("Missing weakness_id")

    severity = attrs.get("severity_rating")
    if severity not in {"none", "low", "medium", "high", "critical"}:
        issues.append(f"Invalid severity_rating: {severity}")

    return issues


def _check_prohibited_content(text: str) -> List[str]:
    issues: List[str] = []
    for phrase in PROHIBITED_PHRASES:
        if phrase in text:
            issues.append(f"Prohibited content detected: {phrase}")
    return issues


def _check_severity_inflation(text: str) -> List[str]:
    issues: List[str] = []
    for phrase in INFLATED_PHRASES:
        if phrase in text:
            issues.append(f"Possible severity inflation without evidence: {phrase}")
    return issues


def _check_scope_boundary_violations(text: str) -> List[str]:
    findings = [
        "test subdomains or systems not explicitly listed",
        "test social engineering",
        "older or forgotten domains are in scope",
        "target employee systems",
        "internal infrastructure",
        "move laterally into unscoped systems",
    ]
    return _match_block("Possible scope boundary violation", text, findings)


def _check_disclosure_violations(text: str) -> List[str]:
    findings = [
        "submit duplicate reports",
        "duplicate report",
        "publicly disclose before",
        "publicly disclose vulnerabilities before",
        "disclose vulnerabilities publicly before",
        "false or inflated severity claims",
        "inflated severity claims",
        "spam multiple low-quality reports",
        "program says you can",
        "preferred disclosure timeline",
    ]
    return _match_block("Possible disclosure policy violation", text, findings)


def _check_behavioral_violations(text: str) -> List[str]:
    findings = [
        "harass or threaten the program",
        "threaten the program",
        "personal gain outside the bug bounty",
        "sell or share the vulnerability",
        "sell the vulnerability",
        "share the vulnerability",
        "sell bugs",
        "sell reports",
        "vulnerability to third parties",
        "sell to third parties",
        "share with third parties",
        "mass credential stuffing",
        "criminal exploitation",
        "exploit for personal gain",
        "exploit for financial gain",
        "social engineering attack",
        "social engineering campaign",
        "phishing attack",
        "phishing campaign",
        "phishing attempt",
        "pretexting",
        "vishing",
        "smishing",
        "physical intrusion to obtain",
        "unauthorized physical access",
        "without authorization is illegal",
        "accessing beyond proof of concept is illegal",
    ]
    return _match_block("Possible behavioral violation", text, findings)


def _check_interaction_violations(text: str) -> List[str]:
    findings = [
        "demand bounties or threaten disclosure",
        "demand bounties",
        "threaten disclosure",
        "coercion is extortion",
        "constitutes extortion",
        "bypass the official program",
        "bypass official program",
        "contact executives directly",
        "contact executives",
        "vulnerability information for leverage in salary",
        "vulnerability information for leverage in job negotiations",
        "leverage disclosure",
        "leverage this vulnerability",
        "threaten to disclose",
        "threaten public disclosure",
        "demand payment",
        "demand reward",
        "negotiate bounty outside the program",
        "outside the program",
        "regulatory pressure",
        "legal pressure",
        "negative press",
        "bad press",
        "embarrass the program",
        "public embarrassment",
    ]
    return _match_block("Possible interaction/comms violation", text, findings)


def _check_post_disclosure_violations(text: str) -> List[str]:
    findings = [
        "continue testing after disclosure",
        "authorization ends",
        "publish exploit code before the program patches",
        "published exploit code before",
        "portfolio piece before disclosure",
        "portfolio piece before public acknowledgment",
        "wait for formal disclosure",
    ]
    return _match_block("Possible post-disclosure policy violation", text, findings)


def _check_general_rule_violations(text: str) -> List[str]:
    findings = [
        "is this okay",
        "if you're asking",
        "reading and testing only is permitted",
        "programs explicitly define scope",
        "illegal",
    ]
    return _match_block("Possible general-rule risk wording", text, findings)


def _match_block(prefix: str, text: str, phrases: List[str]) -> List[str]:
    issues: List[str] = []
    lowered = text.lower()
    for phrase in phrases:
        if phrase in lowered:
            issues.append(f"{prefix}: {phrase}")
    return issues


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_evidence_file(path: Path) -> List[str]:
    issues: List[str] = []
    if not path.exists():
        return [f"Missing evidence file: {path}"]
    try:
        data = load_json(path)
    except Exception as exc:
        return [f"Evidence file unreadable: {exc}"]

    for key in ["platform", "target_id", "check_type", "status", "result_hash", "timestamp", "requires_auth", "body", "headers"]:
        if key not in data:
            issues.append(f"Evidence missing required field: {key}")

    body = data.get("body", {})
    if isinstance(body, dict) and "error" in body:
        issues.append(f"Evidence body contains error: {body['error']}")

    return issues


def validate_manifest_file(path: Path) -> List[str]:
    issues: List[str] = []
    if not path.exists():
        return [f"Missing manifest file: {path}"]
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        return [f"Manifest file unreadable: {exc}"]

    seen = 0
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except Exception as exc:
            issues.append(f"Manifest line {lineno} invalid JSON: {exc}")
            continue
        seen += 1
        for key in ["run_id", "platform", "result_count", "result_hash", "provider", "device_name", "fallback_used", "timestamp", "status"]:
            if key not in data:
                issues.append(f"Manifest line {lineno} missing field: {key}")

    if seen == 0:
        issues.append("Manifest file contains no JSONL records")

    return issues


COMPLIANCE_RULES = [
    "No fabricated or synthetic reports.",
    "No speculative PoC narratives.",
    "No speculative title / weakness / scope mapping without verified evidence.",
    "Only real identified findings, real identified scope, and real identified weakness IDs may be used.",
    "Submission is allowed only after reproduction, impact statement, remediation, and explicit user approval.",
    "No unauthorized access, no lateral movement, no service disruption.",
    "No public disclosure before program patch/fix.",
    "Respect rate limits and backoff on 429.",
]


def _flatten_json_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        parts: List[str] = []
        for key, val in value.items():
            parts.append(str(key))
            parts.append(_flatten_json_text(val))
        return "\n".join(parts)
    if isinstance(value, list):
        parts: List[str] = []
        for item in value:
            parts.append(_flatten_json_text(item))
        return "\n".join(parts)
    return "" if value is None else str(value)


def validate_output_root(output_root: Path | None = None) -> Dict[str, Any]:
    root = Path(output_root) if output_root else DEFAULT_OUTPUT_ROOT
    result: Dict[str, Any] = {
        "output_root": str(root),
        "evidence_checked": 0,
        "manifest_checked": 0,
        "issues": [],
    }
    evidence_dir = root / "evidence"
    manifest_dir = root / "manifests"
    if evidence_dir.exists():
        for path in sorted(evidence_dir.glob("*.json")):
            result["evidence_checked"] += 1
            result["issues"].extend(
                [f"{path}: {issue}" for issue in _check_evidence_compliance(path)]
            )
    if manifest_dir.exists():
        for path in sorted(manifest_dir.glob("*.json")):
            result["manifest_checked"] += 1
            result["issues"].extend(
                [f"{path}: {issue}" for issue in _check_manifest_compliance(path)]
            )
    return result


def _check_evidence_compliance(path: Path) -> List[str]:
    issues: List[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"Evidence file unreadable: {exc}"]
    required_keys = ["platform", "target_id", "check_type", "status", "result_hash", "timestamp", "requires_auth", "body", "headers"]
    for key in required_keys:
        if key not in data:
            issues.append(f"Evidence missing required field: {key}")
    body = data.get("body", {})
    if isinstance(body, dict) and "error" in body:
        issues.append(f"Evidence body contains error: {body['error']}")
    text = _flatten_json_text(body)
    normalized = _normalize(text)
    issues.extend(_check_prohibited_content(normalized))
    issues.extend(_check_severity_inflation(normalized))
    issues.extend(_check_scope_boundary_violations(normalized))
    issues.extend(_check_disclosure_violations(normalized))
    issues.extend(_check_behavioral_violations(normalized))
    issues.extend(_check_interaction_violations(normalized))
    issues.extend(_check_post_disclosure_violations(normalized))
    issues.extend(_check_general_rule_violations(normalized))
    issues.extend(check_report_quality(normalized))
    issues.extend(check_technical_consistency(normalized))
    return issues


def _check_manifest_compliance(path: Path) -> List[str]:
    issues: List[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        return [f"Manifest file unreadable: {exc}"]
    seen = 0
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except Exception as exc:
            issues.append(f"Manifest line {lineno} invalid JSON: {exc}")
            continue
        seen += 1
        required_keys = ["run_id", "platform", "result_count", "result_hash", "provider", "device_name", "fallback_used", "timestamp", "status"]
        for key in required_keys:
            if key not in data:
                issues.append(f"Manifest line {lineno} missing field: {key}")
        normalized = _normalize(_flatten_json_text(data))
        issues.extend(_check_prohibited_content(normalized))
        issues.extend(_check_severity_inflation(normalized))
        issues.extend(_check_scope_boundary_violations(normalized))
        issues.extend(_check_disclosure_violations(normalized))
        issues.extend(_check_behavioral_violations(normalized))
        issues.extend(_check_interaction_violations(normalized))
        issues.extend(_check_post_disclosure_violations(normalized))
        issues.extend(_check_general_rule_violations(normalized))
    if seen == 0:
        issues.append("Manifest file contains no JSONL records")
    return issues


def _main(argv: List[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="zqm-bounty-hub compliance checker")
    parser.add_argument("--payload", help="Path to JSON report payload", default=None)
    parser.add_argument("--output-root", help="Path to outputs root", default=None)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)
    if args.payload:
        try:
            payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"Payload unreadable: {exc}")
            return 2
        issues = check_report_payload(payload)
        if args.json:
            print(json.dumps({"payload": args.payload, "issues": issues}))
        else:
            print(f"Payload: {args.payload}")
            print(f"Issues: {len(issues)}")
            for issue in issues:
                print(f"  - {issue}")
        return 0 if not issues else 3
    report = validate_output_root(args.output_root)
    if args.json:
        print(json.dumps(report))
    else:
        print(f"Output root: {report['output_root']}")
        print(f"Evidence checked: {report['evidence_checked']}")
        print(f"Manifest checked: {report['manifest_checked']}")
        print(f"Issues: {len(report['issues'])}")
        for issue in report["issues"]:
            print(f"  - {issue}")
    return 0 if not report["issues"] else 4


if __name__ == "__main__":
    raise SystemExit(_main())
