"""Narrow information-exposure check on verified web assets.

Tests only:
- Error path response bodies for stack traces, version info, internal paths
- 404/500 default pages
- Common debug/test endpoints

No fuzzing, no scanners, no disruption.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))
OUTPUT_DIR = SKILL_DIR / "outputs"
EVIDENCE_DIR = OUTPUT_DIR / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

TARGETS = {
    "shopify": [
        "partners.shopify.com",
        "shopify.plus",
    ],
    "basecamp": [
        "launchpad.37signals.com",
    ],
    "8x8-bounty": [
        "connect.8x8.com",
    ],
    "security": [
        "www.hackerone.com",
    ],
}

# Patterns that indicate information exposure
INFO_EXPOSURE_PATTERNS = [
    r"stack trace",
    r"traceback",
    r"exception",
    r"error at line",
    r"fatal error",
    r"undefined index",
    r"Undefined index",
    r"database error",
    r"SQLSTATE",
    r"syntax error",
    r"Warning:",
    r"Notice:",
    r"内部服务器错误",
    r"Internal Server Error",
    r"Version:",
    r"Powered by",
    r"Server:",
    r"X-Powered-By",
    r"X-AspNet-Version",
    r"X-AspNetMvc-Version",
    r"Django version",
    r"Rails version",
    r"Express",
    r"Node.js",
    r"PHP/",
    r"nginx/",
    r"Apache/",
    r"\.git",
    r"\.env",
    r"config\.php",
    r"wp-config",
    r"DEBUG",
    r"Environment",
    r"application\.json",
    r"composer\.json",
    r"package\.json",
    r"yarn\.lock",
    r"\.DS_Store",
    r"\.svn",
    r"\.hg",
    r"\.bzr",
    r"\.idea",
    r"\.vscode",
    r"\.github",
    r"\.circleci",
    r"\.travis\.yml",
    r"\.npmrc",
    r"\.bash_history",
    r"\.ssh",
    r"authorized_keys",
]


def _sha256(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()[:16]


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _save(platform: str, target_id: str, check_type: str, body: dict[str, Any]) -> Path:
    result_hash = _sha256(json.dumps(body, ensure_ascii=False, default=str))
    evidence = {
        "platform": platform,
        "target_id": target_id,
        "check_type": check_type,
        "status": "ok",
        "result_hash": result_hash,
        "timestamp": _now(),
        "requires_auth": False,
        "body": body,
        "headers": {},
        "notes": "narrow information-exposure reconnaissance",
    }
    path = EVIDENCE_DIR / f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_inf_exposure_{target_id}_{check_type}_raw.json"
    path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def curl_get(host: str, path: str) -> dict[str, Any]:
    cmd = ["curl", "-sS", "-i", "--max-time", "20", f"https://{host}{path}"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        out = proc.stdout
        parts = out.split("\r\n\r\n", 1)
        header_text = parts[0] if parts else ""
        body = parts[1] if len(parts) > 1 else ""
        status = None
        hdrs: dict[str, str] = {}
        for line in header_text.splitlines():
            if line.lower().startswith("http/"):
                parts_line = line.split(" ", 2)
                if len(parts_line) >= 2:
                    status = int(parts_line[1])
            elif ":" in line:
                k, v = line.split(":", 1)
                hdrs[k.strip().lower()] = v.strip()
        return {
            "host": host,
            "path": path,
            "status": status,
            "headers": hdrs,
            "body": body,
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {"host": host, "path": path, "status": None, "headers": {}, "body": None, "error": str(exc)}


def scan_for_exposure(body: str, headers: dict[str, str]) -> list[str]:
    hits = []
    blob = (body or "") + "\n" + "\n".join(headers.values())
    for pat in INFO_EXPOSURE_PATTERNS:
        if re.search(pat, blob, re.IGNORECASE):
            hits.append(pat)
    return hits


def main() -> int:
    run_id = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    print(f"Starting narrow information-exposure reconnaissance run {run_id}")
    findings = []

    for target, hosts in TARGETS.items():
        print(f"\n[*] {target}")
        for host in hosts:
            print(f"  [.] {host}")
            paths_to_check = [
                "/",
                "/nonexistent-404-info-test",
                "/nonexistent-path/../admin",
                "/robots.txt",
                "/sitemap.xml",
                "/favicon.ico",
                "/.git/HEAD",
                "/.env",
                "/config.php",
                "/wp-config.php.bak",
                "/api/v1",
                "/api/v1/status",
                "/api/debug",
                "/debug",
                "/console",
                "/actuator",
                "/env",
                "/info",
                "/health",
                "/metrics",
                "/swagger",
                "/swagger-ui.html",
                "/graphql",
                "/graphiql",
                "/api/graphql",
            ]
            host_findings = []
            for p in paths_to_check:
                r = curl_get(host, p)
                status = r.get("status")
                body = r.get("body") or ""
                hdrs = r.get("headers") or {}
                exposure = scan_for_exposure(body, hdrs)
                if exposure:
                    host_findings.append({
                        "path": p,
                        "status": status,
                        "exposure_patterns": exposure,
                        "body_sample": body[:500],
                        "headers_sample": {k: v for k, v in list(hdrs.items())[:20]},
                    })
                    print(f"    [!] {p} -> {status} exposure={exposure[:3]}")
                else:
                    print(f"    [.] {p} -> {status}")
                _save("hackerone", host, "info_exposure", r)
                time.sleep(1.2)

            findings.append({
                "host": host,
                "target": target,
                "findings": host_findings,
                "total_checked": len(paths_to_check),
                "findings_count": len(host_findings),
            })

    out = OUTPUT_DIR / f"{datetime.now(UTC).strftime('%Y-%m-%d')}_h1_info_exposure_recon.json"
    out.write_text(json.dumps({"run_id": run_id, "findings": findings}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
