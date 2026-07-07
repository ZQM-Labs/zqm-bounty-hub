# HackerOne Hacktivity Program Filter Quirk

Observed: 2026-07-07
Platform: HackerOne `/v1/hackers/hacktivity`
Account: `zqm-computing`

## Finding

`/v1/hackers/hacktivity?queryString=team:{handle}` returns HTTP 400

```json
{
  "errors": [
    {
      "status": "400",
      "title": "Invalid Query",
      "detail": "Unable to parse ElasticSearch query",
      "source": { "parameter": "" }
    }
  ]
}
```

Tested handles:
- `team:basecamp`
- `team:shopify`

Both failed with the same ElasticSearch parse error. Other valid query filters exist on this endpoint, so `team:` specifically is the issue here, not all Lucene filters.

## Adapter Behavior

`hacktivity_program(program_handle=handle)` raises `RuntimeError` with the 400 detail above. The adapter must fall back to global `hacktivity()` and record:
- `filtered_by`
- `fallback: "global"`
- `warning`

## Workaround

Use global `/v1/hackers/hacktivity` for discovery. Program-specific hacktivity filtering is not reliable via this endpoint from this account/API version unless HackerOne updates query syntax support.

If program-only hacktivity is required, prefer manual browser/UI review or ask HackerOne support whether `team:` indexing is supported for this token/account type.

## Do Not Retry Blindly

Repeating `team:{handle}` queries wastes rate-limit budget and produces no new signal. Stop after the first 400 and switch strategy.
