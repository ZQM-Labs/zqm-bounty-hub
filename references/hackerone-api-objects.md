# HackerOne API Reference Objects

Source: official HackerOne developer docs.
All objects follow JSON API shape: top-level `id`, `type`, `attributes`, and optional `relationships`.
Base URL: `https://api.hackerone.com`
Auth: HTTP Basic auth with API Token identifier as username, token value as password.

activity
-------
Represents an action performed on a report.

Attributes:
- id: string
- type: string
- attributes.report_id: string | null
- attributes.message: string | null
- attributes.internal: boolean
- attributes.created_at: string(date-time)
- attributes.updated_at: string(date-time)

Relationships:
- actor: user | program
- attachments: [attachment]

attachment
---------
Users can add attachments when they file or interact with a report. Handle with caution.

Attributes:
- id: string
- type: "attachment"
- attributes.file_name: string
- attributes.content_type: string
- attributes.file_size: integer
- attributes.expiring_url: string
  - Expires after 60 minutes.
- attributes.created_at: string(date-time)

bounty
------
Created when a program pays a bounty. A report may have multiple bounty objects.

Attributes:
- id: string
- type: "bounty"
- attributes.amount: string | null  # USD amount
- attributes.bonus_amount: string | null  # USD bonus
- attributes.awarded_amount: string | null  # awarded currency amount
- attributes.awarded_bonus_amount: string | null
- attributes.awarded_currency: string | null
- attributes.created_at: string(date-time)

earning
-------
An earning object represents bounty earnings, pentest completions, or retest completions.

Type discriminators:
- earning-bounty-earned
- earning-pentest-completed
- earning-retest-completed

Attributes:
- id: string
- type: string
- attributes.amount: number

Relationships:
- bounty: bounty object  # for earning-bounty-earned
- pentester: pentester object  # for earning-pentest-completed
- report_retest_user: report-retest-user object  # for earning-retest-completed
- program: program object

group
-----
Represents a set of users and permissions.

Attributes:
- id: string
- type: "group"
- attributes.name: string
- attributes.permissions: [string]
  - Possible values: reward_management, program_management, user_management, report_management
- attributes.created_at: string(date-time)

hacktivity_item
--------------
Limited disclosure record returned by `/v1/hackers/hacktivity`.

Attributes:
- id: integer
- type: "report"
- attributes.title: string | null
- attributes.substate: report-states
- attributes.url: string(url) | null
- attributes.disclosed_at: string(date-time) | null
- attributes.submitted_at: string(date-time) | null
- attributes.disclosed: boolean
- attributes.cve_ids: [string] | null
- attributes.cwe: string | null
- attributes.severity_rating: severity-ratings | null
  - none / low / medium / high / critical
- attributes.votes: integer | null
- attributes.total_awarded_amount: integer | null
- attributes.latest_disclosable_action: string | null
- attributes.latest_disclosable_activity_at: string(date-time) | null

Relationships:
- report_generated_content:
  - data:
    - id: string
    - type: "report_generated_content"
    - attributes.hacktivity_summary: string | null
- reporter:
  - data:
    - type: "user"
    - attributes.name: string | null
    - attributes.username: string
- program:
  - data:
    - type: "program"
    - attributes.handle: string
    - attributes.offers_bounties: boolean | null
    - attributes.url: string(url) | null

links
-----
Pagination links included in list responses.

Attributes:
- prev: string | null
- self: string
- next: string | null

payout
------
A payout object represents a completed payout.

Attributes:
- amount: number | null  # USD
- paid_out_at: string(date-time) | null
- reference: string | null
- payout_provider: string | null
- status: string | null

pentest
-------
A pentest object represents a pentest engagement.

Attributes:
- id: string
- type: "pentest"
- attributes.name: string
- attributes.description: string

pentester
---------
Represents completion of a pentest by a user.

Attributes:
- id: string | null
- type: "pentester"
- attributes.completed_at: string(date-time)
- relationships.pentest:
  - data: pentest object

program
-------
Represents a disclosure program or bug bounty program.

Attributes:
- id: string
- type: "program"
- attributes.handle: string
- attributes.name: string
- attributes.currency: string | null
- attributes.policy: string | null
- attributes.profile_picture: string(uri)
- attributes.submission_state: string
- attributes.triage_active: boolean | null
- attributes.state: string | null
  - Example: public_mode
- attributes.started_accepting_at: string(date-time) | null
- attributes.number_of_reports_for_user: integer | null
- attributes.number_of_valid_reports_for_user: integer | null
- attributes.bounty_earned_for_user: number | null
- attributes.last_invitation_accepted_at_for_user: string(date-time) | null
- attributes.bookmarked: boolean | null
- attributes.allows_bounty_splitting: boolean | null
- attributes.offers_bounties: boolean | null
- attributes.open_scope: boolean | null
- attributes.fast_payments: boolean | null
- attributes.gold_standard_safe_harbor: boolean | null

Relationships:
- structured_scopes:
  - data: [structured-scope]

program_small
------------
Reduced program object used within report relationships.

Attributes:
- id: string
- type: "program"
- attributes.handle: string

report
------
A submitted vulnerability report.

Attributes:
- id: string
- type: "report"
- attributes.title: string
- attributes.vulnerability_information: string | null
- attributes.state: report-states
- attributes.created_at: string(date-time)
- attributes.submitted_at: string(date-time) | null
- attributes.triaged_at: string(date-time) | null
- attributes.closed_at: string(date-time) | null
- attributes.last_reporter_activity_at: string(date-time) | null
- attributes.first_program_activity_at: string(date-time) | null
- attributes.last_program_activity_at: string(date-time) | null
- attributes.last_activity_at: string(date-time) | null
- attributes.last_public_activity_at: string(date-time) | null
- attributes.bounty_awarded_at: string(date-time) | null
- attributes.swag_awarded_at: string(date-time) | null
- attributes.disclosed_at: string(date-time) | null
- attributes.reporter_agreed_on_going_public_at: string(date-time) | null
- attributes.cve_ids: [string]

Relationships:
- program:
  - data: program_small
- attachments: [attachment]
- swag: [swag]
- weakness:
  - data: weakness
- structured_scope:
  - data: structured-scope
- severity:
  - data: severity
- reporter:
  - data: user
- activities: [activity]
  - ordered by most recent first
- bounties: [bounty]
- summaries: [report-summary]

report_generated_content
------------------------
AI summary content for a report or hacktivity entry.

Attributes:
- id: string
- type: "report_generated_content"
- attributes.hacktivity_summary: string | null

report-intent
------------
Draft report prepared with AI assistance before submission.

Attributes:
- id: string
- type: "report-intent"
- attributes.title: string | null
- attributes.description: string
- attributes.state: string
  - pending / ready_to_submit / submitted
- attributes.has_failing_jobs: boolean
- attributes.has_canceled_jobs: boolean
- attributes.job_status_by_type: object
  - Example keys:
    - assistant_response
    - revise_intent
    - analyze_asset_type
    - analyze_vulnerability_presence
    - analyze_bug_type
    - determine_asset
    - analyze_cif
    - analyze_bug_class_completeness
    - assistant_summary
- attributes.metadata: object
  - Example keys:
    - bug_class
    - http_method
    - vulnerable_url
    - vulnerable_parameter

Relationships:
- program
  - type: any
- report:
  - type: any
  - Present only after submission.
- attachments: [attachment]

report-retest
-------------
Retest engagement object.

Attributes:
- id: string
- type: "report-retest"

Relationships:
- report:
  - data: report

report-retest-user
------------------
Completion record for a retest.

Attributes:
- id: string
- type: "report-retest-user"
- attributes.completed_at: string(date-time)

Relationships:
- report_retest:
  - data: report-retest

report-states
-------------
Values:
- new
- pending-program-review
- triaged
- needs-more-info
- resolved
- not-applicable
- informative
- duplicate
- spam
- retesting

report-summary
--------------
Summary added to a report before disclosure.

Attributes:
- id: string
- type: "report-summary"
- attributes.content: string
- attributes.category: string
  - researcher / team / triage
- attributes.created_at: string(date-time)
- attributes.updated_at: string(date-time)

Relationships:
- user:
  - data: user

scope-exclusion
---------------
Category excluded from rewards in addition to core ineligible findings.

Attributes:
- id: string
- type: "scope-exclusion"
- attributes.category: string | null
- attributes.details: string | null
- attributes.created_at: string(date-time) | null
- attributes.updated_at: string(date-time) | null

severity
--------
Represents the severity of a report.

Attributes:
- id: string
- type: "severity"
- attributes.rating: severity-ratings
- attributes.author_type: string
  - User | Team
- attributes.user_id: integer
- attributes.score: number | null  # CVSS score
- attributes.attack_vector: string | null
  - network / adjacent / local / physical
- attributes.attack_complexity: string
  - low / high
- attributes.privileges_required: string
  - none / low / high
- attributes.user_interaction: string | null
  - none / required
- attributes.scope: string | null
  - unchanged / changed
- attributes.confidentiality: string
  - none / low / high
- attributes.integrity: string
  - none / low / high
- attributes.availability: string
  - none / low / high
- attributes.created_at: string(date-time)

severity-ratings
---------------
Values:
- none
- low
- medium
- high
- critical

structured-scope
----------------
Asset defined by a program.

Attributes:
- id: string
- type: "structured-scope"
- attributes.asset_identifier: string
- attributes.asset_type: string
- attributes.confidentiality_requirement: string
  - none / low / medium / high
- attributes.integrity_requirement: string
  - none / low / medium / high
- attributes.availability_requirement: string
  - none / low / medium / high
- attributes.max_severity: string
  - none / low / medium / high / critical
- attributes.created_at: string(date-time)
- attributes.updated_at: string(date-time)
- attributes.instruction: string | null
- attributes.eligible_for_bounty: boolean
- attributes.eligible_for_submission: boolean
- attributes.reference: string | null

swag
----
Non-financial award.

Attributes:
- id: string
- type: "swag"
- attributes.sent: boolean
- attributes.created_at: string(date-time)

Relationships:
- user:
  - data: user
- address:
  - data: address

user
----
Platform account.

Attributes:
- id: string
- type: "user"
- attributes.disabled: boolean
- attributes.username: string
  - unique; shares namespace with program handles
- attributes.name: string
- attributes.profile_picture:
  - 62x62: string
  - 82x82: string
  - 110x110: string
  - 260x260: string
- attributes.bio: string | null
- attributes.website: string | null
- attributes.location: string | null
- attributes.reputation: number | null
  - Present in reporter relationship of report objects
- attributes.signal: number | null
  - Range -10 to 7
- attributes.impact: number | null
  - Range 0 to 50
- attributes.hackerone_triager: boolean | null
- attributes.created_at: string(date-time)

Relationships:
- participating_programs: [object]
  - Only present on User > Read endpoint
  - Returns private programs where user is invited

weakness
--------
CWE/CAPEC weakness categorization.

Attributes:
- id: string
- type: "weakness"
- attributes.name: string
- attributes.description: string
- attributes.external_id: string
  - CWE or CAPEC reference, e.g. CWE-352
- attributes.created_at: string(date-time)

address
-------
Postal address for swag delivery.

Attributes:
- id: string
- type: "address"
- attributes.name: string
- attributes.street: string
- attributes.city: string
- attributes.postal_code: string
- attributes.state: string
- attributes.country: string
- attributes.tshirt_size: string | null
  - M_Small / M_Medium / M_Large / M_XLarge / M_XXLarge
  - W_Small / W_Medium / W_Large / W_XLarge / W_XXLarge
- attributes.phone_number: string | null
- attributes.created_at: string(date-time)
