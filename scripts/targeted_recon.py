"""Targeted reconnaissance for verified bounty-hub assets.

Allowed methods only:
- Curl-based manual request probing
- Content negotiation checks
- Redirect chain inspection
- CORS header inspection
- Cookie flag inspection
- Error signature inspection

No automated scanners, no fuzzing, no disruption.
"""
from __future__ import annotations

import json
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
        "accounts.shopify.com",
        "shop.app",
        "shopify.plus",
    ],
    "8x8-bounty": [
        "connect.8x8.com",
        "platform.8x8pilot.com",
    ],
    "basecamp": [
        "launchpad.37signals.com",
    ],
    "security": [
        "www.hackerone.com",
        "api.hackerone.com",
    ],
}


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
        "notes": "targeted reconnaissance only",
    }
    path = EVIDENCE_DIR / f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_recon_{target_id}_{check_type}_raw.json"
    path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def curl_probe(host: str, path: str = "/", headers: dict[str, str] | None = None, follow: bool = False) -> dict[str, Any]:
    import subprocess
    cmd = ["curl", "-sS", "-i", "--max-time", "20"]
    if follow:
        cmd.append("-L")
    if headers:
        for k, v in headers.items():
            cmd.extend(["-H", f"{k}: {v}"])
    cmd.extend([f"https://{host}{path}"])
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
        out = proc.stdout
        err = proc.stderr
        # split headers/body
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
            "body_sample": body[:1000],
            "curl_stderr": err[:500],
            "error": None,
        }
    except Exception as exc:
        return {"host": host, "path": path, "status": None, "headers": {}, "body_sample": None, "curl_stderr": None, "error": str(exc)}


def classify_cookies(headers: dict[str, str]) -> list[str]:
    findings = []
    set_cookie = headers.get("set-cookie", "")
    if not set_cookie:
        return findings
    raw = "; ".join(set_cookie) if isinstance(set_cookie, list) else str(set_cookie)
    if "Secure" not in raw:
        findings.append("cookie-missing-secure")
    if "SameSite=None" in raw:
        findings.append("cookie-samesite-none")
    if "HttpOnly" not in raw:
        findings.append("cookie-missing-httponly")
    return findings


def main() -> int:
    run_id = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    print(f"Starting targeted reconnaissance run {run_id}")
    results = []

    for target, hosts in TARGETS.items():
        print(f"\n[*] {target}")
        for host in hosts:
            print(f"  [.] {host}")
            probes = []
            # default GET
            r = curl_probe(host, "/")
            probes.append(r)
            print(f"    default: status={r.get('status')}")
            # content negotiation
            r2 = curl_probe(host, "/", headers={"Accept": "application/xml"})
            probes.append(r2)
            print(f"    xml-neg: status={r2.get('status')}")
            # Accept text/plain
            r3 = curl_probe(host, "/", headers={"Accept": "text/plain, */*"})
            probes.append(r3)
            print(f"    plain-neg: status={r3.get('status')}")
            # common error path
            r4 = curl_probe(host, "/nonexistent-404-check")
            probes.append(r4)
            print(f"    404: status={r4.get('status')}")
            # redirect probe
            r5 = curl_probe(host, "/redirect?to=https://example.com", follow=True)
            probes.append(r5)
            print(f"    redirect: status={r5.get('status')}")

            # collect cookie findings
            all_cookie_findings = []
            for pr in probes:
                if pr.get("headers"):
                    cf = classify_cookies(pr["headers"])
                    if cf:
                        all_cookie_findings.extend(cf)

            # collect CSP presence
            csp_present = any("content-security-policy" in (p.get("headers") or {}) for p in probes if p.get("headers"))

            rec = {
                "host": host,
                "target": target,
                "probes": probes,
                "cookie_findings": list(set(all_cookie_findings)),
                "csp_present": csp_present,
            }
            results.append(rec)
            for p in probes:
                _save("hackerone", host, "recon_probe", p)
            time.sleep(1.5)

    out = OUTPUT_DIR / f"{datetime.now(UTC).strftime('%Y-%m-%d')}_h1_targeted_recon.json"
    out.write_text(json.dumps({"run_id": run_id, "results": results}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
