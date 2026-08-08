"""Passive reconnaissance for verified bounty-hub targets.

Allowed methods only:
- DNS resolution
- Certificate transparency logs (crt.sh)
- Wayback Machine historical URLs
- Public GitHub code search
- Public HTTP headers / tech fingerprinting

No active scanning, no fuzzing, no disruption.
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
    "basecamp": [
        "launchpad.37signals.com",
    ],
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
        "notes": "passive reconnaissance only",
    }
    path = EVIDENCE_DIR / f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_passive_{target_id}_{check_type}_raw.json"
    path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def passive_dns(host: str) -> dict[str, Any]:
    import socket
    try:
        ip = socket.gethostbyname(host)
        return {"host": host, "ip": ip, "error": None}
    except Exception as exc:
        return {"host": host, "ip": None, "error": str(exc)}


def crt_sh(host: str) -> dict[str, Any]:
    import json as _json
    import urllib.error
    import urllib.request
    url = f"https://crt.sh/?q={host}&output=json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = _json.loads(r.read().decode("utf-8", errors="ignore"))
        names = []
        for entry in data[:200]:
            name = entry.get("name_value", "")
            if name:
                names.append(name)
        return {"host": host, "names": names, "count": len(names), "error": None}
    except Exception as exc:
        return {"host": host, "names": [], "count": 0, "error": str(exc)}


def wayback(host: str) -> dict[str, Any]:
    import json as _json
    import urllib.error
    import urllib.request
    url = f"https://archive.org/wayback/available?url={host}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = _json.loads(r.read().decode("utf-8", errors="ignore"))
        snap = data.get("archived_snapshots", {}).get("closest", {})
        return {"host": host, "available": bool(snap), "url": snap.get("url"), "timestamp": snap.get("timestamp"), "error": None}
    except Exception as exc:
        return {"host": host, "available": False, "url": None, "timestamp": None, "error": str(exc)}


def github_search(host: str) -> dict[str, Any]:
    import json as _json
    import urllib.error
    import urllib.request
    query = f'"{host}"'
    url = f"https://api.github.com/search/code?q={urllib.parse.quote(query)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = _json.loads(r.read().decode("utf-8", errors="ignore"))
        items = data.get("items", [])[:20]
        return {
            "host": host,
            "total": data.get("total_count", 0),
            "items": [{"name": it.get("name"), "html_url": it.get("html_url"), "repo": it.get("repository", {}).get("full_name")} for it in items],
            "error": None,
        }
    except Exception as exc:
        return {"host": host, "total": 0, "items": [], "error": str(exc)}


def public_headers(host: str) -> dict[str, Any]:
    import urllib.error
    import urllib.request
    url = f"https://{host}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}, method="GET")
        with urllib.request.urlopen(req, timeout=30) as r:
            headers = {k: v for k, v in r.getheaders()}
            return {
                "host": host,
                "status": r.getcode(),
                "headers": dict(list(headers.items())[:30]),
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        # still capture headers on 4xx/5xx
        headers = {k: v for k, v in exc.headers.items()} if exc.headers else {}
        return {
            "host": host,
            "status": exc.code,
            "headers": dict(list(headers.items())[:30]),
            "error": str(exc),
        }
    except Exception as exc:
        return {"host": host, "status": None, "headers": {}, "error": str(exc)}


def main() -> int:
    run_id = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    print(f"Starting passive reconnaissance run {run_id}")
    results = []

    for target, hosts in TARGETS.items():
        print(f"\n[*] {target}")
        for host in hosts:
            print(f"  [.] {host}")
            dns = passive_dns(host)
            certs = crt_sh(host)
            wb = wayback(host)
            gh = github_search(host)
            hdrs = public_headers(host)

            _save("hackerone", host, "passive_dns", dns)
            _save("hackerone", host, "passive_crtsh", certs)
            _save("hackerone", host, "passive_wayback", wb)
            _save("hackerone", host, "passive_github", gh)
            _save("hackerone", host, "passive_headers", hdrs)

            res = {
                "host": host,
                "target": target,
                "dns": dns,
                "cert": certs,
                "wayback": wb,
                "github": gh,
                "headers": hdrs,
            }
            results.append(res)
            print(f"    dns={dns.get('ip')} certs={certs.get('count')} wayback={wb.get('available')} github={gh.get('total')} status={hdrs.get('status')}")

            time.sleep(1.5)

    out = OUTPUT_DIR / f"{datetime.now(UTC).strftime('%Y-%m-%d')}_h1_passive_recon.json"
    out.write_text(json.dumps({"run_id": run_id, "results": results}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
