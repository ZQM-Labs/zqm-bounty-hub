# HackerOne API Reference

Source material: official HackerOne developer docs, verified 2026-07-05.

Base URL
--------
https://api.hackerone.com

Auth
----
HTTP Basic auth.
- username = API Token identifier
- password = API Token value
Header example:
  Authorization: Basic base64(<identifier>:<token>)

Endpoints
---------
GET /v1/hackers/hacktivity
- queryString : Apache Lucene query string
  - filter examples: severity_rating, asset_type, substate, cwe, cve_ids, reporter, team, total_awarded_amount, disclosed_at, has_collaboration, disclosed
- sort : latest_disclosable_activity_at, disclosed_at, total_awarded_amount, votes
  - prefix with `-` for descending
- page[number] : default 1
- page[size] : 1..100, default 25

Response shape:
{
  "data": [
    {
      "id": ...,
      "type": "report",
      "attributes": {
        "title": ...,
        "substate": ...,
        "url": ...,
        "disclosed_at": ...,
        "cve_ids": [...],
        "cwe": ...,
        "severity_rating": ...,
        "votes": ...,
        "total_awarded_amount": ...,
        "latest_disclosable_action": ...,
        "latest_disclosable_activity_at": ...,
        "submitted_at": ...,
        "disclosed": true|false
      },
      "relationships": {
        "program": {
          "data": {
            "type": "program",
            "attributes": {
              "handle": ...,
              "name": ...,
              "currency": ...,
              "url": ...
            }
          }
        }
      }
    }
  ]
}

GET /v1/hackers/me/reports
- page[number]
- page[size]

GET /v1/hackers/reports/{id}
- id required

POST /v1/hackers/reports
Body:
{
  "data": {
    "type": "report",
    "attributes": {
      "team_handle": "...",
      "title": "...",
      "vulnerability_information": "...",
      "impact": "...",
      "severity_rating": "none|low|medium|high|critical",
      "weakness_id": 0,
      "structured_scope_id": 0
    }
  }
}

GET /v1/hackers/payments/balance
Response:
{
  "data": {
    "balance": ...
  }
}

GET /v1/hackers/payments/earnings
- page[number]
- page[size]

GET /v1/hackers/payments/payouts
- page[number]
- page[size]

GET /v1/hackers/programs
- page[number]
- page[size]

GET /v1/hackers/programs/{handle}
- handle required

GET /v1/hackers/programs/{handle}/structured_scopes
- handle required
- filter[id__gt]
- filter[created_at__gt]
- filter[updated_at__gt]
- page[number]
- page[size]
- max 10,000 scopes; use filter[id__gt] to continue beyond that

GET /v1/hackers/programs/{handle}/weaknesses
- handle required
- page[number]
- page[size]

GET /v1/hackers/programs/{handle}/scope_exclusions
- handle required

Report Intents
-------------
GET    /v1/hackers/report_intents
POST   /v1/hackers/report_intents
GET    /v1/hackers/report_intents/{id}
PATCH  /v1/hackers/report_intents/{id}
DELETE /v1/hackers/report_intents/{id}
POST   /v1/hackers/report_intents/{id}/submit
GET    /v1/hackers/report_intents/{report_intent_id}/attachments
POST   /v1/hackers/report_intents/{report_intent_id}/attachments
DELETE /v1/hackers/report_intents/{report_intent_id}/attachments/{id}

Key fields
----------
- severity_rating: none, low, medium, high, critical
- disclosed: boolean
- total_awarded_amount: numeric bounty amount
- handle: program slug, e.g. gitlab, shopify
- asset_type / structured_scope asset_identifier: scope target
- eligible_for_bounty / eligible_for_submission: program constraints

Response envelope
-----------------
Success: JSON API object with data/links.
Failure: {"errors":[{"status":...}]}
Auth failure: 401
Forbidden: 403
Not found: 404

Rate limits
----------
Rate caps by operation class:
- Read operations: 600 requests per minute (general)
- Read operations: 300 requests per minute (report pages)
- Read operations: 50 requests per minute (structured scopes endpoint)
- Write operations: 25 requests per 20 seconds
When you hit the limit:
- Response: 429 Too Many Requests
- Response body: {"errors":[{"status":"429","title":"Rate limited","detail":"..."}]}
Best practice:
- Implement exponential backoff or request queuing
- Do not hammer retries; respect 429 and back off

Notes
-----
- All requests require `Accept: application/json`
- Use official HackerOne handles in program paths, not display names
- No public disclosure before patch per program policy
