"""Full bounty review across all 593 HackerOne programs."""
from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

import requests

TOKEN = os.environ.get("HACKERONE_API_TOKEN")
if not TOKEN:
    raise SystemExit("Set HACKERONE_API_TOKEN before running full_bounty_review.py")
IDENTIFIER = os.environ.get("HACKERONE_API_TOKEN_IDENTIFIER") or "zqm-computing"
BASE = "https://api.hackerone.com/v1/hackers"
OUT_PATH = Path(r"C:\Users\zqmco\AppData\Local\hermes\skills\zqm-bounty-hub\outputs\2026-07-05_h1_full_bounty_review.json")
SKILL_DIR = Path(__file__).resolve().parent.parent.parent
RATE_LIMIT_SLEEP = 1.3  # structured scopes limit: 50 req/min
MAX_WORKERS = 10


def session() -> requests.Session:
    s = requests.Session()
    s.auth = (IDENTIFIER, TOKEN)
    s.headers.update({"Accept": "application/json"})
    return s


def get_all_programs(sess: requests.Session) -> list[dict]:
    items: list[dict] = []
    page = 1
    while True:
        r = sess.get(f"{BASE}/programs", params={"page[size]": 100, "page[number]": page}, timeout=30)
        r.raise_for_status()
        data = r.json()
        items.extend(data.get("data", []) or [])
        if not data.get("links", {}).get("next"):
            break
        page += 1
        time.sleep(0.2)
    return items


def get_structured_scopes(sess: requests.Session, handle: str) -> list[dict]:
    r = sess.get(f"{BASE}/programs/{handle}/structured_scopes", params={"page[size]": 100}, timeout=30)
    if r.status_code != 200:
        return []
    return r.json().get("data", []) or []


def get_weaknesses(sess: requests.Session, handle: str) -> list[dict]:
    r = sess.get(f"{BASE}/programs/{handle}/weaknesses", params={"page[size]": moderate_size(handle)}, timeout=30)
    if r.status_code != 200:
        return []
    return r.json().get("data", []) or []


def moderate_size(handle: str) -> int:
    # Avoid fixed size being too large for all
    return 50


def analyze_scopes(items: list[dict]) -> dict:
    attrs = [s.get("attributes", {}) for s in items]
    return {
        "count": len(attrs),
        "bounty_count": sum(1 for a in attrs if a.get("eligible_for_bounty")),
        "submission_count": sum(1 for a in attrs if a.get("eligible_for_submission")),
        "critical_count": sum(1 for a in attrs if a.get("max_severity") == "critical"),
        "high_count": sum(1 for a in attrs if a.get("max_severity") == "high"),
        "medium_count": sum(1 for a in attrs if a.get("max_severity") == "medium"),
        "low_count": sum(1 for a in attrs if a.get("max_severity") == "low"),
        "urls": [a.get("asset_identifier") for a in attrs if a.get("asset_type") == "URL"][:20],
        "wildcards": [a.get("asset_identifier") for a in attrs if a.get("asset_type") == "WILDCARD"][:20],
        "other": [a.get("asset_identifier") for a in attrs if a.get("asset_type") == "OTHER"][:20],
    }


def analyze_weaknesses(items: list[dict]) -> dict:
    names = [w.get("attributes", {}).get("name") for w in items if w.get("attributes", {}).get("name")]
    return {
        "count": len(names),
        "top": names[:30],
        "unique_count": len(set(names)),
    }


def score_bounty_value(a: dict, scopes: dict, weaknesses: dict, disclosed: dict) -> dict:
    score = 0
    reasons = []
    if a.get("offers_bounties") is True:
        score += 30
        reasons.append("offers_bounties")
    if a.get("open_scope") is True:
        score += 20
        reasons.append("open_scope")
    score += min(40, scopes.get("count", 0) * 0.5)
    if scopes.get("bounty_count", 0) > 0:
        score += min(20, scopes["bounty_count"] * 0.5)
        reasons.append("bounty_scopes")
    if scopes.get("critical_count", 0) > 0:
        score += min(20, scopes["critical_count"] * 0.5)
        reasons.append("critical_scopes")
    max_award = disclosed.get("max_award", 0) or 0
    if max_award >= 1000:
        score += 20
        reasons.append("high_value_bounty")
    elif max_award >= 100:
        score += 10
        reasons.append("low_value_bounty")
    bc = a.get("bounty_earned_for_user") or 0
    if bc > 0:
        score += min(20, bc / 100)
        reasons.append("user_earnings")
    return {"score": round(min(100, score), 2), "reasons": reasons}


def process_program(sess: requests.Session, program: dict, disclosed_lookup: dict[str, dict]) -> dict:
    a = program.get("attributes", {})
    handle = a.get("handle")
    if not handle:
        return {}

    scopes_items = get_structured_scopes(sess, handle)
    weaknesses_items = get_weaknesses(sess, handle)
    scopes = analyze_scopes(scopes_items)
    weaknesses = analyze_weaknesses(weaknesses_items)
    disclosed = disclosed_lookup.get(handle, {})
    value = score_bounty_value(a, scopes, weaknesses, disclosed)

    return {
        "handle": handle,
        "name": a.get("name") or handle,
        "offers_bounties": a.get("offers_bounties"),
        "submission_state": a.get("submission_state"),
        "open_scope": a.get("open_scope"),
        "fast_payments": a.get("fast_payments"),
        "gold_standard_safe_harbor": a.get("gold_standard_safe_harbor"),
        "bounty_earned_for_user": a.get("bounty_earned_for_user") or 0,
        "number_of_valid_reports_for_user": a.get("number_of_valid_reports_for_user") or 0,
        "scopes": scopes,
        "weaknesses": weaknesses,
        "disclosed": disclosed,
        "bounty_value_score": value["score"],
        "bounty_value_reasons": value["reasons"],
    }


def main() -> int:
    print("Starting full bounty review...", flush=True)
    start = datetime.now(UTC)
    sess = session()

    # 1. Programs catalog
    programs = get_all_programs(sess)
    print(f"Fetched {len(programs)} programs", flush=True)

    # 2. Load disclosed research if available
    research_path = SKILL_DIR / "outputs" / "2026-07-05_h1_hacktivity_disclosed_research.json"
    disclosed_lookup: dict[str, dict] = {}
    if research_path.exists():
        research = json.loads(research_path.read_text(encoding="utf-8"))
        for handle, meta in research.get("program_disclosed_counts", {}).items():
            disclosed_lookup[handle] = meta
        print(f"Loaded disclosed research for {len(disclosed_lookup)} programs", flush=True)

    # 3. Enrich programs with scopes + weaknesses
    enriched: list[dict] = []
    # Process in two waves: scopes first, then top-N weaknesses
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(process_program, session(), p, disclosed_lookup): p for p in programs}
        for i, future in enumerate(as_completed(futures), 1):
            try:
                result = future.result()
                if result:
                    enriched.append(result)
            except Exception as exc:
                handle = futures[future].get("attributes", {}).get("handle", "?")
                print(f"Error processing {handle}: {exc}", flush=True)
            if i % 100 == 0:
                print(f"Processed {i}/{len(programs)}...", flush=True)

    # 4. Rank by bounty value
    ranked = sorted(enriched, key=lambda x: x.get("bounty_value_score", 0), reverse=True)

    # 5. Compute summary stats
    total_programs = len(ranked)
    bounty_programs = [r for r in ranked if r.get("offers_bounties") is True]
    open_programs = [r for r in ranked if r.get("submission_state") == "open"]
    value_gt0 = [r for r in ranked if r.get("bounty_value_score", 0) > 0]

    summary = {
        "total_programs": total_programs,
        "offers_bounties": len(bounty_programs),
        "submission_open": len(open_programs),
        "value_positive": len(value_gt0),
        "avg_value_score": round(sum(r.get("bounty_value_score", 0) for r in ranked) / max(1, total_programs), 2),
        "top_10": [
            {
                "handle": r["handle"],
                "name": r["name"],
                "bounty_value_score": r["bounty_value_score"],
                "reasons": r["bounty_value_reasons"],
                "offers_bounties": r.get("offers_bounties"),
                "submission_state": r.get("submission_state"),
                "open_scope": r.get("open_scope"),
                "scopes_count": r.get("scopes", {}).get("count", 0),
                "bounty_scopes": r.get("scopes", {}).get("bounty_count", 0),
                "critical_scopes": r.get("scopes", {}).get("critical_count", 0),
                "max_award": r.get("disclosed", {}).get("max_award", 0),
            }
            for r in ranked[:10]
        ],
    }

    out = {
        "generated_at": datetime.now(UTC).isoformat(),
        "platform": "hackerone",
        "review_type": "full_bounty_review",
        "auth_identifier": IDENTIFIER,
        "summary": summary,
        "ranking": ranked,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    elapsed = (datetime.now(UTC) - start).total_seconds()
    print(f"Completed in {elapsed:.1f}s", flush=True)
    print(f"Summary: {summary['total_programs']} total, {summary['offers_bounties']} offer bounties, {summary['submission_open']} open, {summary['value_positive']} positive value", flush=True)
    print("Top 10:", flush=True)
    for r in summary["top_10"]:
        print(f"  {r['handle']:25} score={r['bounty_value_score']:5.1f} reasons={r['reasons']} scopes={r['scopes_count']} bounty_scopes={r['bounty_scopes']} critical={r['critical_scopes']} max_award=${r['max_award']}", flush=True)
    print("Saved to", OUT_PATH, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
