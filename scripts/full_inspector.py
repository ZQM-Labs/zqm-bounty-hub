"""Full inspector: complete weaknesses + raw exclusions for priority targets."""
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

EVIDENCE_DIR = SKILL_DIR / "outputs" / "evidence"
MANIFEST_DIR = SKILL_DIR / "outputs" / "manifests"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST_DIR.mkdir(parents=True, exist_ok=True)


def _sha256(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()[:16]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _save(platform: str, target_id: str, check_type: str, body: Dict[str, Any], run_id: str) -> Path:
    result_hash = _sha256(json.dumps(body, ensure_ascii=False, default=str))
    evidence = {
        "platform": platform,
        "target_id": target_id,
        "check_type": check_type,
        "status": "ok",
        "result_hash": result_hash,
        "timestamp": _now(),
        "requires_auth": True,
        "body": body,
        "headers": {"Accept": "application/json", "Authorization": "Basic <redacted>"},
    }
    path = EVIDENCE_DIR / f"{run_id}_h1_{target_id}_{check_type}_raw.json"
    path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest = {
        "run_id": run_id,
        "platform": platform,
        "result_count": 1,
        "result_hash": result_hash,
        "provider": "full_inspector",
        "device_name": os.environ.get("COMPUTERNAME", "unknown"),
        "fallback_used": False,
        "timestamp": _now(),
        "status": "ok",
    }
    mpath = MANIFEST_DIR / f"{run_id}_hackerone_manifest.jsonl"
    with open(mpath, "a", encoding="utf-8") as f:
        f.write(json.dumps(manifest, ensure_ascii=False) + "\n")
    return path


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    handles = ["basecamp", "shopify", "8x8-bounty", "security", "anthropic", "cloudflare"]
    summaries = []
    for handle in handles:
        weaknesses = h1.program_weaknesses(handle)
        exclusions = h1.scope_exclusions(handle)
        _save("hackerone", f"prog_{handle}", "weaknesses_full", {"weaknesses": weaknesses}, run_id)
        _save("hackerone", f"prog_{handle}", "exclusions_full", {"exclusions": exclusions}, run_id)

        weaknesses_names = [w.get("attributes", {}).get("name", "") for w in weaknesses]
        weakness_ids = [w.get("id") for w in weaknesses]
        # print raw exclusion fields for first 3 exclusions to inspect structure
        exclusion_samples = []
        for ex in exclusions[:3]:
            if isinstance(ex, dict):
                exclusion_samples.append({
                    "id": ex.get("id"),
                    "type": ex.get("type"),
                    "attributes": ex.get("attributes"),
                })
            else:
                exclusion_samples.append({"raw": str(ex)[:200]})

        summary = {
            "handle": handle,
            "weakness_count": len(weaknesses),
            "weakness_ids": weakness_ids,
            "weakness_names": weaknesses_names,
            "exclusion_count": len(exclusions),
            "exclusion_samples": exclusion_samples,
            "generated_at": _now(),
        }
        summaries.append(summary)
        print(f"{handle}: weaknesses={len(weaknesses)} exclusions={len(exclusions)}")
        time.sleep(1.3)

    out = EVIDENCE_DIR / f"{run_id}_h1_full_inspector_summary.json"
    out.write_text(json.dumps({"run_id": run_id, "summaries": summaries}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSummary: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
