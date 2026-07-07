"""Placeholder Bugcrowd adapter for zqm-bounty-hub.

NOTE: Bugcrowd auth contract is unverified on this host.
Official docs domain `developers.bugcrowd.com` failed DNS resolution,
so exact header/path format remains unknown.

This adapter implements the evidence/manifest contract and emits
a clear `unsupported_platform` status when called.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))
from adapter_registry import validate_evidence, validate_manifest
EVIDENCE_DIR = SKILL_DIR / "outputs" / "evidence"
MANIFEST_DIR = SKILL_DIR / "outputs" / "manifests"
UNVERIFIED_REASON = "Bugcrowd auth contract unverified; docs domain DNS failure on this host"


def _ensure_dirs() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()[:16]


def run(target_id: str, check_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Run one Bugcrowd task."""
    _ensure_dirs()
    timestamp = datetime.now(timezone.utc).isoformat()
    run_id = parameters.get("run_id") or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    task_id = f"bugcrowd_{target_id}_{check_type}"

    body = {
        "error": UNVERIFIED_REASON,
        "required_action": "Verify Bugcrowd API auth header/path format before use",
    }
    status = "unsupported_platform"
    result_hash = _sha256(json.dumps(body, ensure_ascii=False, default=str))

    evidence = {
        "platform": "bugcrowd",
        "target_id": target_id,
        "check_type": check_type,
        "status": status,
        "result_hash": result_hash,
        "timestamp": timestamp,
        "requires_auth": True,
        "body": body,
        "headers": {},
        "notes": UNVERIFIED_REASON,
    }
    evidence_path = EVIDENCE_DIR / f"{run_id}_{task_id}_raw.json"
    evidence_path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")

    manifest = {
        "run_id": run_id,
        "platform": "bugcrowd",
        "result_count": 0,
        "result_hash": result_hash,
        "provider": "placeholder",
        "device_name": os.environ.get("COMPUTERNAME", "unknown"),
        "fallback_used": True,
        "timestamp": timestamp,
        "status": status,
    }
    manifest_path = MANIFEST_DIR / f"{run_id}_bugcrowd_manifest.jsonl"
    with open(manifest_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(manifest, ensure_ascii=False) + "\n")

    return {
        "platform": "bugcrowd",
        "target_id": target_id,
        "check_type": check_type,
        "status": status,
        "result_hash": result_hash,
        "timestamp": timestamp,
        "evidence_path": str(evidence_path),
        "manifest_path": str(manifest_path),
    }
