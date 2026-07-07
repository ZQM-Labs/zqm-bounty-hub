# Revenue Impact Ranking Reference

## Scope

This reference supports `scripts/rank_programs.py` and local payout tracking fields in `targets/hackerone_targets.json`.

## Ranking precedence

1. HackerOne Payments Earnings API
   - Endpoint: `GET /v1/hackers/payments/earnings`
   - Use when: token auth returns non-401 and produces payouts.
   - Output: program totals + report counts.

2. Hacktivity API
   - Endpoint: `GET /v1/hackers/hacktivity`
   - Filter by `team=<program_slug>`, sort by `-total_awarded_amount`.
   - Use top 5 disclosed paid amounts as a revenue-impact heuristic.
   - Output: estimated bounty from disclosed amounts + recent reports count.

3. Local target metadata
   - `reported_bounty_examples[].amount_usd`
   - dollar mentions in `notes`
   - Use only when API tiers return zero or unavailable.

## Output contract

`outputs/ranked_programs.json`:
```json
{
  "generated_at": "<ISO-8601>",
  "generator": "scripts/rank_programs.py",
  "ranked_count": 6,
  "ranked_programs": [
    {
      "target_id": "...",
      "program_name": "...",
      "program_slug": "...",
      "estimated_bounty_usd": 0.0,
      "recent_reports_count": 0,
      "data_source": "local_targets",
      "confidence": 0.85,
      "severity_focus": ["..."]
    }
  ]
}
```

`outputs/ranked_programs.md` markdown table summarizes the same fields.

## Fallback rules

- If earnings/hacktivity return HTTP 401 with a present token, continue with local fallbacks.
- Do NOT substitute public price tables, vendor marketing figures, or LLM guesses for `estimated_bounty_usd`.
- `data_source` must reflect actual derivation path.
- `confidence` should reflect evidence strength; disclose signals and VDP keywords are additive only when grounded in local metadata.

## Caveats

- This host returned HTTP 401 for `/v1/hackers/programs`, `/v1/hackers/payments/earnings`, and `/v1/hackers/hacktivity` during verification despite `HACKERONE_API_TOKEN` being present. Continued reliance on local metadata until auth is resolved is expected and acceptable.
- `h1_api_client.py` is absent from this host; `scripts/rank_programs.py` uses stdlib urllib instead of a missing custom adapter.
