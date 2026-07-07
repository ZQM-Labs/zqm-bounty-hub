# Ripio Authenticated Recon Checklist — Own Account Only
**Target Program**: Ripio (HackerOne) — `ripio`  
**Researcher alias**: zqm-computing@wearehackerone.com  
**Test account email**: zqmcomputing@gmail.com → use H1 alias when signing up on Ripio  
**Policy refs**: ATO $6,000 challenge, test-plan rules, hard exclusions

## Setup
[ ] Create Ripio account using `zqm-computing@wearehackerone.com`  
[ ] Enable 2FA in account settings (MFA enabled is required for meaningful testing)  
[ ] Record account creation timestamp + confirmation email  
[ ] Do NOT touch `ripiotestuser1@gmail.com`; only use your own account  
[ ] Add identifier to all traffic: `X-Bug-Bounty: HackerOne-zqm-computing` and `X-H1-traffic: zqm-computing`

## Passive/Browser Recon (no automated scanners)
[ ] Inspect `https://app.ripio.com/` and `https://www.ripio.com/` source for JS endpoints  
[ ] Look for `/api`, `/api/v1`, `/v2`, `/graphql`, `/auth`, `/login`, `/register` in JS bundles  
[ ] Check login form `action`, hidden fields, CSRF tokens, password autocomplete  
[ ] Check registration form for email verification bypass, invite-code reuse, referrer leakage  
[ ] Inspect 2FA enrollment/setup flow for backup-code reuse, QR secret leakage  
[ ] Inspect `/security.txt` if present; check `robots.txt` for internal paths  
[ ] Review `bridge.ripio.com` JavaScript bundle for wallet/dApp auth endpoints

## Auth/2FA Recon
[ ] Capture `/login` or equivalent POST request; inspect response for tokens/redirects  
[ ] Check for credential stuffing protections: rate limit, IP lockout, account lockout  
[ ] Check 2FA backup codes: generated once, reusable, leaked in responses  
[ ] Check 2FA bypass via param tampering: `2fa_verified=true`, `mfa_passed=1`  
[ ] Check trusted-device/remember-me token hijack or fixation  
[ ] Check password-reset token predictability, reuse, or race condition  
[ ] Check email-change flow for CSRF or authorization bypass  
[ ] Check login-with-SSO/OAuth if available for open redirect or token swapping  
[ ] Check session fixation on login state change  
[ ] Check missing `Secure`/`HttpOnly`/`SameSite` on auth cookies only with a working exploit

## Account/Profile Recon
[ ] Fetch `/account/profile` or equivalent; check for other-user data leakage by id traversal  
[ ] Check API for user enumeration by changing `id`/`email`/`username` parameter  
[ ] Check if email address or phone is disclosed to other users without consent  
[ ] Check account deletion/reactivation state leakage  
[ ] Check KYC/ID verification document exposure or download bypass

## Wallet/Balance Recon (only analytical, no transfers)
[ ] Inspect wallet balance endpoints for other-user data by ID/Pointer fuzz  
[ ] Check if deposit/withdraw history exposes other users’ transactions  
[ ] Check for race condition in withdrawal/transfer amount calculation  
[ ] Check if webhooks/notifications leak sensitive amounts or addresses to wrong user  
[ ] Check for crypto-address reuse, validator exposure, or transaction malleability

## Business Logic Recon
[ ] Check fee/percentage manipulation in exchange/transfer amount fields  
[ ] Check currency conversion rounding errors or precision loss  
[ ] Check referral/bonus code replay or duplication  
[ ] Check order-side buy/sell race for negative balances or free credits  
[ ] Check withdrawal destination change without 2FA re-prompt

## API/Web3 Recon
[ ] Inspect `/api/v1`, `/api/v2`, `/bridge`, `/api/auth/*`, `/api/wallet/*` with your own session  
[ ] Check for GraphQL introspection where enabled  
[ ] Check for IDOR on `/api/users/{id}`, `/api/accounts/{id}`, `/api/wallets/{id}`  
[ ] Check for inventory/transaction history enumeration  
[ ] Check if production bridge contracts are reachable in testing context (only local fork per Web3 policy)

## Reporting Constraints (MUST follow)
[ ] No brute force against any endpoint  
[ ] No social engineering  
[ ] No testing against other users’ data  
[ ] No DoS / service degradation  
[ ] Do not compromise `@gmail.com` provider or act on `ripiotestuser1@gmail.com`  
[ ] Web3 PoC must use local fork only; no mainnet/testnet interaction  
[ ] POC must be reproducible and human-readable in <5 minutes  
[ ] Do not exfiltrate, transfer, or modify funds

## Deliverable Template
1. Affected asset: exact URL/path/contract+function  
2. Description: what and how  
3. Security boundary: what trust boundary is crossed  
4. Attacker model: required auth state, 2FA status, owned account  
5. Reproduction: numbered steps with curl/HAR/video  
6. Impact: data/actions accessible, funds at risk, users affected  
7. Default relevance: default or special config  
8. Production relevance: production vs test-only

## Stop Conditions
- If any probe touches another user’s data → stop and report immediately  
- If uncertainty about compliance → pause and verify against this checklist  
- If finding needs brute force or SE → drop; Ripio explicitly excludes these
