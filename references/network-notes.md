# ZQM Bounty Hub — Network Notes Reference

Audience: security tooling authors and platform integrators.

- Respect boundary conditions: no out-of-scope host reachability tests unless explicitly scoped
- Handling multi-region endpoints: scope by DNS names only, not IP history
- Avoid mass DNS enumeration unless scope explicitly allows it
- DNS records and endpoint lists are only useful if scoped
- Consider cache path handling and TTL when scoping repeated scans
