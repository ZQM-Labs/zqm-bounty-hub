"""Read-only opportunity alerts from cached HackerOne intelligence.

Maps hacktivity weakness signals to cached program scopes, writes a
time-prefixed alerts manifest.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = SKILL_DIR / "outputs" / "cache"
OUTPUT_DIR = SKILL_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _load(name: str) -> Dict[str, Any]:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    p = CACHE_DIR / f"{today}_{name}.json"
    fallback = sorted(CACHE_DIR.glob(f"*_{name}.json"))
    if not p.exists() and fallback:
        p = fallback[-1]
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def build_alerts(top_n: int = 12) -> Dict[str, Any]:
    hack = _load("hacktivity").get("items") or []
    progs = _load("programs").get("items") or []
    by_handle = {p.get("handle"): p for p in progs if p.get("handle")}
    details = _load("program_details").get("results") or {}

    cwe_counts: Dict[str, int] = Counter()
    severity_counts: Dict[str, int] = Counter()
    for item in hack:
        attr = item.get("attributes") or {}
        cwe = attr.get("cwe")
        if cwe:
            cwe_counts[cwe] += 1
        sev = attr.get("severity_rating")
        if sev:
            severity_counts[sev] += 1

    handle_weak_map = defaultdict(list)
    for item in hack:
        attr = item.get("attributes") or {}
        rel = (item.get("relationships") or {})
        prog_handle = (((rel.get("program") or {}).get("data") or {}).get("attributes") or {}).get("handle")
        cwe = attr.get("cwe")
        sev = attr.get("severity_rating")
        amount = attr.get("total_awarded_amount")
        if prog_handle and cwe:
            handle_weak_map[prog_handle].append({"cwe": cwe, "severity_rating": sev, "amount": amount})

    alert_programs = []
    for handle in sorted(set(list(by_handle.keys()) + list(details.keys())[:50])):
        detail = details.get(handle) or {}
        weakness_names = detail.get("weaknesses") or []
        scopes = detail.get("structured_scopes") or []
        weak_count = len(weakness_names)
        scope_count = len(scopes)
        trend_counts = Counter((w.get("cwe") for w in handle_weak_map.get(handle, []) if w.get("cwe")))
        trending = [{ "cwe": k, "count": v} for k, v in trend_counts.most_common(8)]
        score = 0
        for cwe, count in trend_counts.items():
            score += count * (4 if cwe in cwe_counts and cwe_counts[cwe] >= 3 else 1)
        score += weak_count * 3
        score += scope_count * 1
        alert_programs.append({
            "handle": handle,
            "score": score,
            "weakness_count": weak_count,
            "scope_count": scope_count,
            "trending_cwes": trending,
            "submission_state": (((detail.get("detail") or {}).get("submission_state"))) if isinstance(detail.get("detail"), dict) else detail.get("submission_state"),
            "name": (by_handle.get(handle) or {}).get("name"),
        })
    alert_programs.sort(key=lambda x: x.get("score", 0), reverse=True)
    out_path = OUTPUT_DIR / f"{_day()}_opportunity_alerts.json"
    out_path.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "top_global_cwes": [{"cwe": k, "count": v} for k, v in cwe_counts.most_common(20)],
        "top_global_severities": severity_counts.most_common(10),
        "top_alert_programs": alert_programs[:top_n],
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output": str(out_path),
        "top_handles": [x.get("handle") for x in alert_programs[:top_n]],
    }


def _day() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def main(argv: List[str] | None = None) -> int:
    result = build_alerts()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
