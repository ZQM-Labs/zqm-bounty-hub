# API Security Testing

Recommended libraries and tools:
- `requests` / `httpx` — baseline API interaction
- `prism` / `openapi-spec-validator` — OpenAPI contract validation
- `graphql-http` / `graphql-core` — GraphQL introspection and query crafting
- `postman`/`newman` — collection replay and regression checks
- `mitmproxy` — request/response logging and replay
- `schemathesis` — property-based API testing against OpenAPI/AsyncAPI specs
- `arbitrary` / `hypothesis-jsonschema` — schema-based fuzz inputs where consent covers it
- `jwt` libs — token inspection/debug; do not brute secrets without authorization

Process defaults:
- Map API surface first: documented endpoints, undocumented routes, versioned paths, GraphQL mutations.
- Validate authz boundaries: horizontal privilege, vertical privilege, object-level authorization, mass assignment.
- Use contract-driven tests where OpenAPI/GraphQL SDL is available.
- Stop on first confirmation of sensitive impact; do not pivot to production data.

Windows host tool availability:
- `httpx`/`requests`, `aiohttp`: installed for fast async API probing where consent covers it
- `schemathesis`, `graphql-core`, `openapi-spec-validator`: installed and verified
- `mitmproxy`: installed for request/response replay
- Newman/Postman CLI: not installed in venv; manual replay via `requests`/`httpx` if needed
- `PyJWT`/`jwcrypto`: installed for token inspection/debug without unsupported runtime brute-force

Evidence requirements:
- Capture exact HTTP method, path, headers, body, and response for rejected and accepted authz states.
- For authorization bugs, save both unprivileged and privileged request/response pairs.
- Mask tokens, API keys, and secrets in all persisted evidence.

Windows notes:
- `schemathesis` requires Python; install in active venv.
- `mitmproxy` provides `mitmweb` GUI if needed.

GraphQL auth-boundary quick-check pattern:
- If the app uses persisted queries, do not assume introspection is required for useful checks.
- First validate with a known persisted query using real auth cookies: expect `200` and non-error data.
- Retry the same persisted query with all auth cookies removed: expect `Not Authenticated` / schema/query error, never the same successful response.
- If unauthenticated returns equivalent data, that is an auth bypass/authorization finding regardless of schema visibility.

Persisted-query constraint:
- Some GraphQL endpoints only accept registered hashes; arbitrary introspection or syntactic sugar queries return `PersistedQueryNotSupported`.
- Do not waste time on schema enumeration there; pivot to browser-captured operation hashes and auth-boundary comparison instead.

Public-vs-private endpoint convention:
- `api.instacart.com/v1/...` may return `403` for unauthenticated clients but `200` for browser-authenticated traffic with the same host/path.
- Always reproduce browser request headers when testing authenticated API surfaces: `Origin`, `Referer`, `x-client-identifier`, and cookie-backed session tokens.
- CORS preflight returning `403` is not itself a bypass; use actual fetch-style requests from the browser context to verify intended behavior.
