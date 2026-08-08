"""Read-only hacktivity pattern analysis for priority targets.

Queries:
- /v1/hackers/hacktivity filtered by team
- Program weaknesses
- Program public scope distribution

Outputs only verified live patterns, no findings.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import h1_api_client as h1


OUTPUT_DIR = SKILL_DIR / "outputs"
EVIDENCE_DIR = OUTPUT_DIR / "evidence"
MANIFEST_DIR = OUTPUT_DIR / "manifests"

PRIORITY_HANDLES = [
    "basecamp",
    "shopify",
    "8x8-bounty",
    "security",
    "anthropic",
    "cloudflare",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()[:16]


def _ensure_dirs() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)


def _save_evidence(evidence: Dict[str, Any]) -> Path:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    task_id = f"h1_{evidence['target_id']}_{evidence['check_type']}"
    path = EVIDENCE_DIR / f"{run_id}_{task_id}_raw.json"
    path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _save_manifest(manifest: Dict[str, Any]) -> Path:
    run_id = manifest["run_id"]
    path = MANIFEST_DIR / f"{run_id}_hackerone_manifest.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(manifest, ensure_ascii=False) + "\n")
    return path


def _build_evidence(platform: str, target_id: str, check_type: str, status: str, body: Dict[str, Any], requires_auth: bool = True) -> Dict[str, Any]:
    result_hash = _sha256(json.dumps(body, ensure_ascii=False, default=str))
    evidence = {
        "platform": platform,
        "target_id": target_id,
        "check_type": check_type,
        "status": status,
        "result_hash": result_hash,
        "timestamp": _now(),
        "requires_auth": requires_auth,
        "body": body,
        "headers": {"Accept": "application/json", "Authorization": "Basic <redacted>"},
    }
    _save_evidence(evidence)
    manifest = {
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
        "platform": platform,
        "result_count": 1 if status == "ok" else 0,
        "result_hash": result_hash,
        "provider": "hacktivity_pattern_analysis",
        "device_name": os.environ.get("COMPUTERNAME", "unknown"),
        "fallback_used": False,
        "timestamp": _now(),
        "status": status,
    }
    _save_manifest(manifest)
    return evidence


def _get_program_weaknesses(handle: str) -> List[Dict[str, Any]]:
    try:
        data = h1.program_weaknesses(handle)
        _build_evidence("hackerone", f"prog_{handle}", "weaknesses", "ok", {"weaknesses": data})
        return data
    except Exception as exc:
        _build_evidence("hackerone", f"prog_{handle}", "weaknesses", "error", {"error": str(exc)})
        return []


def _get_hacktivity_for_program(handle: str) -> List[Dict[str, Any]]:
    try:
        data = h1.hacktivity(program_handle=handle)
        return data
    except Exception as exc:
        # team-filtered may 400; if so, global feed is already captured elsewhere
        _build_evidence("hackerone", f"prog_{handle}", "hacktivity_program", "error", {"error": str(exc)})
        return []


def analyze_weaknesses(weaknesses: List[Dict[str, Any]]) -> Dict[str, Any]:
    names = [w.get("attributes", {}).get("name", "") for w in weaknesses]
    return {
        "total": len(weaknesses),
        "names": names[:30],
        "weakness_ids": [w.get("id") for w in weaknesses[:30]],
    }


def analyze_hacktivity(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    disclosed = [it for it in items if it.get("attributes", {}).get("disclosed")]
    awarded = [it for it in items if it.get("attributes", {}).get("total_awarded_amount")]

    severity_counts: Dict[str, int] = {}
    weakness_counts: Dict[str, int] = {}
    total_awarded = 0.0
    for it in items:
        attrs = it.get("attributes", {})
        sev = attrs.get("severity_rating") or "unknown"
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        cwe = attrs.get("cwe") or "unknown"
        weakness_counts[cwe] = weakness_counts.get(cwe, 0) + 1
        total_awarded += float(attrs.get("total_awarded_amount") or 0)

    return {
        "total_items": len(items),
        "disclosed_count": len(disclosed),
        "awarded_count": len(awarded),
        "total_awarded": total_awarded,
        "severity_counts": severity_counts,
        "weakness_counts": weakness_counts,
        "sample_titles": [it.get("attributes", {}).get("title") for it in items[:10]],
    }


def main() -> int:
    _ensure_dirs()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    print(f"Starting hacktivity pattern analysis run {run_id}")
    print(f"Targets: {', '.join(PRIORITY_HANDLES)}")
    print()

    results = []
    for handle in PRIORITY_HANDLES:
        weaknesses = _get_program_weaknesses(handle)
        hack = _get_hacktivity_for_program(handle)
        weakness_summary = analyze_weaknesses(weaknesses)
        hack_summary = analyze_hacktivity(hack)

        plan = {
            "handle": handle,
            "status": "investigated",
            "weakness_summary": weakness_summary,
            "hacktivity_summary": hack_summary,
            "generated_at": _now(),
        }
        results.append(plan)
        print(f"- {handle}: weaknesses={weakness_summary['total']} hacktivity={hack_summary['total_items']} disclosed={hack_summary['disclosed_count']}")

        # pace to respect structured-scope-like read cadence
        time.sleep(0.8)

    out_path = OUTPUT_DIR / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}_h1_hacktivity_patterns.json"
    out_path.write_text(json.dumps({"run_id": run_id, "plans": results}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
