"""zqm-bounty-hub shared adapter registry helpers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parent.parent
ROUTING_PATH = SKILL_DIR / "adapter-routing.json"

REQUIRED_MANIFEST_FIELDS = [
    "run_id", "platform", "result_count", "result_hash", "provider",
    "device_name", "fallback_used", "timestamp", "status",
]
REQUIRED_EVIDENCE_FIELDS = [
    "platform", "target_id", "check_type", "status", "result_hash",
    "timestamp", "requires_auth", "body", "headers",
]


def load_routing() -> dict:
    if not ROUTING_PATH.exists():
        raise FileNotFoundError(f"Missing adapter routing: {ROUTING_PATH}")
    return json.loads(ROUTING_PATH.read_text(encoding="utf-8"))


def adapter_for(platform: str) -> dict[str, Any]:
    routing = load_routing()
    platform_adapters = routing.get("platform_adapters", {})
    if platform not in platform_adapters:
        raise KeyError(f"Unknown platform adapter: {platform}")
    return platform_adapters[platform]


def resolve_adapter_module_path(platform: str) -> str:
    cfg = adapter_for(platform)
    rel = cfg.get("adapter_module")
    if not rel:
        raise ValueError(f"No adapter_module configured for {platform}")
    return str((SKILL_DIR / rel).resolve())


def validate_manifest(payload: dict) -> bool:
    missing = [k for k in REQUIRED_MANIFEST_FIELDS if k not in payload]
    return not missing


def validate_evidence(payload: dict) -> bool:
    missing = [k for k in REQUIRED_EVIDENCE_FIELDS if k not in payload]
    return not missing


def mirror_paths(run_id: str, task_id: str, platform: str, evidence_dir: Path, manifest_dir: Path, mirror_root: Path) -> tuple[Path, Path]:
    """Mirror evidence and manifest lines to a shared durable store."""
    if not mirror_root:
        return evidence_dir, manifest_dir
    mirror_evidence = Path(mirror_root) / "bounty-hub" / "evidence"
    mirror_manifest = Path(mirror_root) / "bounty-hub" / "manifests"
    mirror_evidence.mkdir(parents=True, exist_ok=True)
    mirror_manifest.mkdir(parents=True, exist_ok=True)
    src_evidence = evidence_dir / f"{run_id}_{task_id}_raw.json"
    if src_evidence.exists():
        dst = mirror_evidence / src_evidence.name
        dst.write_text(src_evidence.read_text(encoding="utf-8"), encoding="utf-8")
    src_manifest = manifest_dir / f"{run_id}_{platform}_manifest.jsonl"
    if src_manifest.exists():
        dst = mirror_manifest / src_manifest.name
        dst.write_text(src_manifest.read_text(encoding="utf-8"), encoding="utf-8")
    return mirror_evidence, mirror_manifest
