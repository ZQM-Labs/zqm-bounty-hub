"""HackerOne API adapter for zqm-bounty-hub.

Uses the verified h1_api_client and maps its responses to the
bounty hub evidence/manifest contract.
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

from adapter_registry import load_routing

import h1_api_client as h1


def _init_paths_from_registry() -> tuple[Path, Path]:
    routing = load_routing()
    output_root = Path(routing.get("bounty_hub", {}).get(
        "output_root",
        r"C:\Users\zqmco\.hermes\shared\skills\zqm-bounty-hub\outputs"
    ))
    return output_root / "evidence", output_root / "manifests"


def _ensure_dirs() -> None:
    global EVIDENCE_DIR, MANIFEST_DIR
    EVIDENCE_DIR, MANIFEST_DIR = _init_paths_from_registry()
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()[:16]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_compliance_check(parameters: Dict[str, Any]) -> Dict[str, Any]:
    from compliance_check import check_report_payload, validate_evidence_file, validate_manifest_file

    report_path = Path(parameters.get("report_payload", ""))
    evidence_path = Path(parameters.get("evidence", ""))
    manifest_path = Path(parameters.get("manifest", ""))

    issues = []
    if report_path.exists():
        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            issues.extend(check_report_payload(payload))
        except Exception as exc:
            issues.append(f"report_payload unreadable: {exc}")
    else:
        issues.append("report_payload path missing")

    if evidence_path.exists():
        issues.extend(validate_evidence_file(evidence_path))
    if manifest_path.exists():
        issues.extend(validate_manifest_file(manifest_path))

    return {"status": "non_compliant" if issues else "compliant", "issues": issues}


def run(target_id: str, check_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Run one HackerOne task for the given target_id."""
    _ensure_dirs()
    timestamp = _now()
    run_id = parameters.get("run_id") or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    task_id = f"h1_{target_id}_{check_type}"

    try:
        if check_type == "program_catalog":
            body = {"programs": h1.programs()}
        elif check_type == "program_detail":
            handle = parameters.get("program_handle") or target_id
            body = h1.program_by_handle(handle)
        elif check_type == "structured_scopes":
            handle = parameters.get("program_handle") or target_id
            body = {"scopes": h1.structured_scopes(handle)}
        elif check_type == "hacktivity":
            body = {"hacktivity": h1.hacktivity()}
        elif check_type == "hacktivity_program":
            handle = parameters.get("program_handle") or target_id
            try:
                body = {"hacktivity": h1.hacktivity(program_handle=handle)}
            except RuntimeError as exc:
                msg = str(exc)
                if "400" in msg and "Invalid Query" in msg:
                    body = {"hacktivity": h1.hacktivity(), "filtered_by": handle, "fallback": "global"}
                else:
                    raise
        elif check_type == "my_reports":
            body = {"reports": h1.my_reports()}
        elif check_type == "earnings":
            body = {"earnings": h1.earnings()}
        elif check_type == "compliance":
            body = {"compliance": _run_compliance_check(parameters)}
            # compliance is a local sandbox check; no auth required
        else:
            body = {"error": f"unsupported check_type: {check_type}"}

        status = "ok"
        requires_auth = True
        if check_type == "compliance":
            if body.get("compliance", {}).get("status") == "non_compliant":
                status = "non_compliant"
                requires_auth = False
            else:
                status = "compliant"
                requires_auth = False
    except Exception as exc:  # pragma: no cover
        body = {"error": str(exc)}
        status = "error"
        requires_auth = True

    result_hash = _sha256(json.dumps(body, ensure_ascii=False, default=str))

    evidence = {
        "platform": "hackerone",
        "target_id": target_id,
        "check_type": check_type,
        "status": status,
        "result_hash": result_hash,
        "timestamp": timestamp,
        "requires_auth": requires_auth,
        "body": body,
        "headers": {"Accept": "application/json", "Authorization": "Basic <redacted>"},
    }

    evidence_path = EVIDENCE_DIR / f"{run_id}_{task_id}_raw.json"
    evidence_path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")

    manifest = {
        "run_id": run_id,
        "platform": "hackerone",
        "result_count": 1 if status == "ok" else 0,
        "result_hash": result_hash,
        "provider": "h1_api_client",
        "device_name": os.environ.get("COMPUTERNAME", "unknown"),
        "fallback_used": False,
        "timestamp": timestamp,
        "status": status,
    }
    manifest_path = MANIFEST_DIR / f"{run_id}_hackerone_manifest.jsonl"
    with open(manifest_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(manifest, ensure_ascii=False) + "\n")

    return {
        "platform": "hackerone",
        "target_id": target_id,
        "check_type": check_type,
        "status": status,
        "result_hash": result_hash,
        "timestamp": timestamp,
        "evidence_path": str(evidence_path),
        "manifest_path": str(manifest_path),
    }
