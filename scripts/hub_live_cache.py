"""Live intelligence cache for zqm-bounty-hub discovery prioritization.

Reads HackerOne from scanned sources, paginates with backoff, and writes
time-prefixed cache documents only.

Run order:
- Primary write run:
    python hub_live_cache.py --once
- Follow-on read-only runs:
    python hub_scores.py
    python hub_opportunity_alerts.py
    python hub_pipeline.py
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import h1_api_client as h1  # noqa: E402

OUTPUT_DIR = SKILL_DIR / "outputs"
CACHE_DIR = OUTPUT_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _day() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _cache_slug(resource: str) -> Path:
    return CACHE_DIR / f"{_day()}_{resource}.json"


def _paginated(path: str, params: Optional[Dict[str, Any]] = None, delay: float = 0.45, limit: int = 500) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    page = 1
    while True:
        payload = h1._get_json(path, {**(params or {}), "page[number]": page, "page[size]": min(limit, 100)})
        data = (((payload or {}).get("data")) or [])
        if not data:
            break
        items.extend(data)
        nxt = (((payload or {}).get("links")) or {}).get("next")
        if not nxt or len(items) >= limit:
            break
        page += 1
        time.sleep(delay)
    return items[:limit]


def cache_programs() -> Dict[str, Any]:
    data = _paginated("/v1/hackers/programs", delay=0.45, limit=500)
    out = {
        "cached_at": _now(),
        "source": "/v1/hackers/programs",
        "count": len(data),
        "items": [
            {
                "id": x.get("id"),
                "handle": (x.get("attributes") or {}).get("handle"),
                "name": (x.get("attributes") or {}).get("name"),
                "state": (x.get("attributes") or {}).get("state"),
                "submission_state": (x.get("attributes") or {}).get("submission_state"),
                "offers_bounties": (x.get("attributes") or {}).get("offers_bounties"),
                "open_scope": (x.get("attributes") or {}).get("open_scope"),
                "registered_until": (x.get("attributes") or {}).get("bookmarked") is not None,
            }
            for x in data
        ],
    }
    _cache_slug("programs").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def cache_hacktivity() -> Dict[str, Any]:
    data = _paginated("/v1/hackers/hacktivity", delay=0.45, limit=500)
    out = {
        "cached_at": _now(),
        "source": "/v1/hackers/hacktivity",
        "count": len(data),
        "items": [{"id": x.get("id"), "title": (((x.get("attributes") or {}).get("title"))), "disclosed_at": (((x.get("attributes") or {}).get("disclosed_at"))), "severity_rating": (((x.get("attributes") or {}).get("severity_rating"))), "cwe": (((x.get("attributes") or {}).get("cwe"))), "total_awarded_amount": (((x.get("attributes") or {}).get("total_awarded_amount"))), "program_handle": ((((((((x.get("relationships") or {}).get("program") or {}).get("data") or {}).get("attributes")) or {}).get("handle"))) if False else None), "program": ((((x.get("relationships") or {}).get("program") or {}).get("data") or {}).get("attributes") or {}).get("handle")} for x in data],
    }
    _cache_slug("hacktivity").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def _detail_from(handle: str, raw: Dict[str, Any]) -> Dict[str, Any]:
    envelope = raw.get("data") or raw
    attr = (((envelope.get("attributes")) or {})) if isinstance(envelope, dict) else {}
    return {
        "id": (((envelope.get("id")))) if isinstance(envelope, dict) else None,
        "name": attr.get("name"),
        "handle": attr.get("handle"),
        "state": attr.get("state"),
        "submission_state": attr.get("submission_state"),
        "offers_bounties": attr.get("offers_bounties"),
        "open_scope": attr.get("open_scope"),
        "policy": (attr.get("policy") or "")[:280],
    }


def cache_program_details(handles: List[str], delay: float = 0.55, limit: int = 500) -> Dict[str, Any]:
    results: Dict[str, Dict[str, Any]] = {}
    for handle in handles:
        entry: Dict[str, Any] = {"handle": handle, "cached_at": _now()}
        try:
            detail = h1.program_by_handle(handle)
        except Exception as exc:
            entry["error"] = str(exc)
            results[handle] = entry
            time.sleep(delay)
            continue
        entry["detail"] = _detail_from(handle, detail)
        try:
            scopes = h1.structured_scopes(handle)
            entry["structured_scopes"] = [((((s.get("attributes") or {}).get("asset_identifier"))) or "") for s in scopes]
        except Exception as exc:
            entry["structured_scopes_error"] = str(exc)
        try:
            weaknesses = h1.program_weaknesses(handle)
            entry["weaknesses"] = [((((w.get("attributes") or {}).get("name"))) or "") for w in weaknesses]
        except Exception as exc:
            entry["weaknesses_error"] = str(exc)
        _cache_slug(f"program_{handle}").write_text(json.dumps(entry, indent=2, ensure_ascii=False), encoding="utf-8")
        results[handle] = entry
        time.sleep(delay)
    out = {"cached_at": _now(), "handles": handles, "results": results}
    _cache_slug("program_details").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def cache_report_pipeline(delay: float = 0.45, limit: int = 500) -> Dict[str, Any]:
    report_intents = _paginated("/v1/hackers/report_intents", delay=delay, limit=limit)
    my_reports = _paginated("/v1/hackers/me/reports", delay=delay, limit=limit)

    def summarize(report_like: Dict[str, Any], kind: str) -> Dict[str, Any]:
        if kind == "intent":
            attr = (report_like.get("attributes") or {})
            return {
                "kind": "intent",
                "id": report_like.get("id"),
                "state": attr.get("state"),
                "created_at": attr.get("created_at"),
                "updated_at": attr.get("updated_at"),
                "team_handle": (((report_like.get("relationships") or {}).get("program") or {}).get("data") or {}).get("attributes", {}).get("handle"),
            }
        attr = (report_like.get("attributes") or {})
        return {
            "kind": "report",
            "id": report_like.get("id"),
            "state": attr.get("state"),
            "created_at": attr.get("created_at"),
            "submitted_at": attr.get("submitted_at"),
            "triaged_at": attr.get("triaged_at"),
            "closed_at": attr.get("closed_at"),
            "team_handle": ((((report_like.get("relationships") or {}).get("program") or {}).get("data") or {}).get("attributes") or {}).get("handle"),
        }
    out = {
        "cached_at": _now(),
        "report_intents_count": len(report_intents),
        "my_reports_count": len(my_reports),
        "report_intents": [summarize(x, "intent") for x in report_intents],
        "my_reports": [summarize(x, "report") for x in my_reports],
    }
    _cache_slug("pipeline").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def run_once(handles: List[str]) -> Dict[str, Any]:
    programs = cache_programs()
    hacktivity = cache_hacktivity()
    program_details = cache_program_details(handles)
    pipeline = cache_report_pipeline()
    return {
        "cached_at": _now(),
        "programs": {"count": programs.get("count"), "path": str(_cache_slug("programs"))},
        "hacktivity": {"count": hacktivity.get("count"), "path": str(_cache_slug("hacktivity"))},
        "program_details": {"handles": len(handles), "path": str(_cache_slug("program_details"))},
        "pipeline": {"report_intents": pipeline.get("report_intents_count"), "my_reports": pipeline.get("my_reports_count"), "path": str(_cache_slug("pipeline"))},
    }


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="H1 live cache writer")
    ap.add_argument("--once", action="store_true", help="write one cache snapshot and exit")
    ap.add_argument("--handles", default="basecamp,shopify,8x8-bounty,security,anthropic,cloudflare", help="comma-separated program handles")
    args = ap.parse_args(argv)
    handles = [h.strip() for h in args.handles.split(",") if h.strip()]
    result = run_once(handles)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
