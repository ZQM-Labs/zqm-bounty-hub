"""Full-scope investigation for zqm-bounty-hub priority targets.

Read-only enumeration of:
- program_detail
- structured_scopes
- weaknesses
- scope_exclusions

Outputs structured target plans with only verified live API data.
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


root = r"C:\Users\zqmco\.hermes\shared\skills\zqm-bounty-hub\outputs"
EVIDENCE_DIR = Path(root) / "evidence"
MANIFEST_DIR = Path(root) / "manifests"
TARGETS_PATH = SKILL_DIR / "targets" / "hackerone_targets.json"

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
        "provider": "full_scope_investigation",
        "device_name": os.environ.get("COMPUTERNAME", "unknown"),
        "fallback_used": False,
        "timestamp": _now(),
        "status": status,
    }
    _save_manifest(manifest)
    return evidence


def _get_program(handle: str) -> Dict[str, Any]:
    try:
        body = h1.program_by_handle(handle)
        _build_evidence("hackerone", f"prog_{handle}", "program_detail", "ok", body)
        return {"ok": True, "body": body}
    except Exception as exc:
        body = {"error": str(exc)}
        _build_evidence("hackerone", f"prog_{handle}", "program_detail", "error", body)
        return {"ok": False, "body": body, "error": str(exc)}


def _get_scopes(handle: str) -> List[Dict[str, Any]]:
    try:
        data = h1.structured_scopes(handle)
        body = {"scopes": data}
        _build_evidence("hackerone", f"prog_{handle}", "structured_scopes", "ok", body)
        return data
    except Exception as exc:
        body = {"error": str(exc)}
        _build_evidence("hackerone", f"prog_{handle}", "structured_scopes", "error", body)
        return []


def _get_weaknesses(handle: str) -> List[Dict[str, Any]]:
    try:
        data = h1.program_weaknesses(handle)
        body = {"weaknesses": data}
        _build_evidence("hackerone", f"prog_{handle}", "weaknesses", "ok", body)
        return data
    except Exception as exc:
        body = {"error": str(exc)}
        _build_evidence("hackerone", f"prog_{handle}", "weaknesses", "error", body)
        return []


def _get_exclusions(handle: str) -> List[Dict[str, Any]]:
    try:
        data = h1.scope_exclusions(handle)
        body = {"scope_exclusions": data}
        _build_evidence("hackerone", f"prog_{handle}", "scope_exclusions", "ok", body)
        return data
    except Exception as exc:
        body = {"error": str(exc)}
        _build_evidence("hackerone", f"prog_{handle}", "scope_exclusions", "error", body)
        return []


def summarize_scope(scopes: List[Dict[str, Any]]) -> Dict[str, Any]:
    eligible_bounty = [s for s in scopes if s.get("attributes", {}).get("eligible_for_bounty")]
    eligible_submission = [s for s in scopes if s.get("attributes", {}).get("eligible_for_submission")]
    asset_types: Dict[str, int] = {}
    for s in scopes:
        at = s.get("attributes", {}).get("asset_type") or "UNKNOWN"
        asset_types[at] = asset_types.get(at, 0) + 1

    return {
        "total": len(scopes),
        "eligible_for_bounty": len(eligible_bounty),
        "eligible_for_submission": len(eligible_submission),
        "asset_types": asset_types,
        "bounty_ids": [s.get("id") for s in eligible_bounty[:50]],
        "critical_scope_ids": [
            s.get("id") for s in eligible_bounty if s.get("attributes", {}).get("max_severity") == "critical"
        ][:20],
    }


def build_target_plan(handle: str) -> Dict[str, Any]:
    print(f"[*] Investigating {handle} ...")
    program = _get_program(handle)
    if not program["ok"]:
        return {
            "handle": handle,
            "status": "error",
            "error": program.get("error"),
            "generated_at": _now(),
        }

    raw = program.get("body") if isinstance(program, dict) else {}
    if isinstance(raw, list) and raw:
        raw = raw[0]
    attrs = raw.get("attributes", {}) if isinstance(raw, dict) else {}
    scopes = _get_scopes(handle)
    weaknesses = _get_weaknesses(handle)
    exclusions = _get_exclusions(handle)

    scope_summary = summarize_scope(scopes)
    weakness_ids = [w.get("id") for w in weaknesses]
    weakness_names = [w.get("attributes", {}).get("name") for w in weaknesses]

    plan = {
        "handle": handle,
        "status": "investigated",
        "program_name": attrs.get("name"),
        "offers_bounties": attrs.get("offers_bounties"),
        "submission_state": attrs.get("submission_state"),
        "open_scope": attrs.get("open_scope"),
        "fast_payments": attrs.get("fast_payments"),
        "scope_summary": scope_summary,
        "weakness_ids": weakness_ids[:20],
        "weakness_names": weakness_names[:20],
        "exclusions_count": len(exclusions),
        "exclusions_sample": [e.get("attributes", {}).get("asset_identifier") for e in exclusions[:10]],
        "generated_at": _now(),
    }

    return plan


def main() -> int:
    _ensure_dirs()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    print(f"Starting full-scope investigation run {run_id}")
    print(f"Targets: {', '.join(PRIORITY_HANDLES)}")
    print()

    plans: List[Dict[str, Any]] = []
    for handle in PRIORITY_HANDLES:
        try:
            plan = build_target_plan(handle)
            plans.append(plan)
        except Exception as exc:
            plans.append({
                "handle": handle,
                "status": "exception",
                "error": str(exc),
                "generated_at": _now(),
            })
        # gentle pacing; respect 50 req/min structured scope boundary
        time.sleep(1.2)

    out_path = EVIDENCE_DIR / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}_h1_full_scope_investigation.json"
    out_path.write_text(json.dumps({"run_id": run_id, "plans": plans}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved investigation: {out_path}")

    # emit summary counts only
    print("\nSummary:")
    for plan in plans:
        h = plan.get("handle")
        st = plan.get("status")
        sc = plan.get("scope_summary") or {}
        print(f"- {h}: status={st} total_scopes={sc.get('total')} bounty_eligible={sc.get('eligible_for_bounty')} submission_eligible={sc.get('eligible_for_submission')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
