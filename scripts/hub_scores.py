"""Read-only HackerOne program scorer for discovery prioritization.

Consumes live cache documents only; does not write new API evidence.
Outputs a markdown shortlist and ranking summary.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

SKILL_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = SKILL_DIR / "outputs" / "cache"
OUTPUT_DIR = SKILL_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _load(name: str) -> Dict[str, Any]:
    p = CACHE_DIR / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}_{name}.json"
    fallback = sorted(CACHE_DIR.glob(f"*_{name}.json"))
    if not p.exists() and fallback:
        p = fallback[-1]
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _score_program(prog: Dict[str, Any], program_details: Dict[str, Any]) -> Dict[str, Any]:
    attrs = {"submission_state": None, "offers_bounties": None, "open_scope": None}
    handle = prog.get("handle")
    detail = (((program_details.get("results") or {}).get(handle)) or {})
    for k in ["submission_state", "offers_bounties", "open_scope"]:
        attrs[k] = (((detail.get("detail") or {}).get(k))) if isinstance(detail.get("detail"), dict) else detail.get(k)
    weak = len(detail.get("weaknesses") or [])
    scope_len = len(detail.get("structured_scopes") or [])
    score = 0
    if attrs.get("submission_state") == "open":
        score += 50
    if attrs.get("offers_bounties") is True:
        score += 30
    if attrs.get("open_scope") is True:
        score += 20
    score += min(weak * 2, 40)
    score += min(scope_len * 1, 30)
    return {
        "handle": handle,
        "name": prog.get("name"),
        "score": score,
        "submission_state": attrs.get("submission_state"),
        "offers_bounties": attrs.get("offers_bounties"),
        "open_scope": attrs.get("open_scope"),
        "weakness_count": weak,
        "scope_count": scope_len,
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_ranked_list() -> Dict[str, Any]:
    programs = (((_load("programs").get("items")) or []))
    program_details = (((_load("program_details").get("results")) or {}))
    if not programs:
        return {"cached_at": _now(), "error": "missing cached programs"}
    scored = [_score_program(p, program_details) for p in programs]
    scored.sort(key=lambda x: x.get("score", 0), reverse=True)
    top = scored[:50]
    out_path = OUTPUT_DIR / f"{_day()}_ranked_programs.json"
    out_path.write_text(json.dumps({"cached_at": _now(), "top": top}, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"cached_at": _now(), "top_count": len(top), "output": str(out_path), "top_handles": [x.get("handle") for x in top[:10]]}


def _day() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def main(argv: List[str] | None = None) -> int:
    result = build_ranked_list()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
