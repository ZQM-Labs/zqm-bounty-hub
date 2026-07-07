"""Read-only submission pipeline tracker from cached HackerOne reports.

Examines report intents and my reports state transitions, writes a
compact markdown status board.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

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


def _state_rank(state: str | None) -> int:
    order = {
        None: -1,
        "intent": 0,
        "needs_triage": 1,
        "triaged": 2,
        "bounty_awarded": 3,
        "resolved": 4,
        "not_applicable": 5,
        "duplicate": 5,
        "spam": 5,
        "informative": 4,
        "acknowledged": 3,
    }
    return order.get(state, 0)


def build_pipeline_markdown() -> str:
    pipeline = _load("pipeline")
    report_intents = (((pipeline.get("report_intents")) or [])[:50])
    my_reports = (((pipeline.get("my_reports")) or [])[:50])

    intents_by_team: Dict[str, List[Dict[str, Any]]]= defaultdict(list)
    reports_by_team: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in report_intents:
        intents_by_team[item.get("team_handle") or "unknown"].append(item)
    for item in my_reports:
        reports_by_team[item.get("team_handle") or "unknown"].append(item)

    lines = []
    lines.append(f"# HackerOne Submission Pipeline")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}Z")
    lines.append("")
    lines.append(f"- Report intents: {len(report_intents)}")
    lines.append(f"- My reports: {len(my_reports)}")
    lines.append("")
    lines.append("## Report Intents")
    lines.append("| Team | Count | Latest state |")
    lines.append("|------|-------|--------------|")
    for team in sorted(intents_by_team):
        items = intents_by_team[team]
        latest = sorted(items, key=lambda x: x.get("updated_at") or "", reverse=True)[0]
        lines.append(f"| {team} | {len(items)} | {latest.get('state')} |")
    lines.append("")
    lines.append("## My Reports")
    lines.append("| Team | Count | Latest state | Latest closed |")
    lines.append("|------|-------|--------------|---------------|")
    for team in sorted(reports_by_team):
        items = reports_by_team[team]
        latest = sorted(items, key=lambda x: x.get("updated_at") or x.get("created_at") or "", reverse=True)[0]
        latest_closed = next((x.get("closed_at") for x in sorted(items, key=lambda x: x.get("closed_at") or "", reverse=True) if x.get("closed_at")), "")
        lines.append(f"| {team} | {len(items)} | {latest.get('state')} | {latest_closed or ''} |")
    lines.append("")
    lines.append("## Candidate Follow-ups")
    candidates = []
    for item in my_reports:
        st = item.get("state")
        if st in {"needs_triage", "triaged"}:
            candidates.append((st, item.get("team_handle"), item.get("id"), item.get("created_at")))
    if candidates:
        candidates.sort(key=lambda x: (_state_rank(x[0]), x[3] or ""))
        for st, team, rid, created in candidates[:20]:
            lines.append(f"- `{rid}` {team or 'unknown'} -> {st} (created {created})")

    out_path = OUTPUT_DIR / f"{_day()}_pipeline_board.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return "\n".join(lines)


def _day() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def main(argv: List[str] | None = None) -> int:
    md = build_pipeline_markdown()
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
