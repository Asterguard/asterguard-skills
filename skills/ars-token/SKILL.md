---
name: ars-token
description: Present the organization's per-org scan credential (the ARS token, sent as the X-ARS-Token header) on every connected scan/run/review call, so each run is authorized, entitled, and metered to the org. Ensures the token is present, renews it on expiry, and never persists the raw value. Use whenever the skills run in connected mode against a hosted AsterGuard/AsterVault endpoint; offline-local runs need no token.
---

# ARS Token (per-org scan credential · metering & entitlement)

The **ARS token** is the organization's machine credential for running scans. It is a per-org
service credential (`asg_…`, scope `scan:run`) presented as the **`X-ARS-Token`** header on every
connected scan/run/review call. It is what makes a run *attributable* — the gateway authorizes it,
counts it against the org's entitlement, and writes a metered usage event. Without it, connected
scan/run endpoints answer `401 invalid or missing X-ARS-Token`.

This is the credential that turns the chain from **offline-local** into **connected + metered + entitled**.
It is separate from, and complementary to, the MCP gateway's audience-bound **Bearer JWT**: the JWT
proves *who is calling* the gateway; the ARS token proves *which org's quota the scan draws on*.

## When to Activate

- **Connected mode** — `ASTERVAULT_MCP_URL` is set, or any call targets a hosted AsterGuard scan/run/
  review endpoint. `engagement.open()` ensures the token before the first metered call.
- On a `401 invalid or missing X-ARS-Token` from any scan/run/review endpoint (the token is absent or expired).
- **Not** in offline mode — local collectors (`local-scan`) and local graph building draw no quota and
  need no token. Skip this skill entirely when `ASTERVAULT_MCP_URL` is unset.

## Core Concepts

- **One credential per org, not per user.** The ARS token identifies the *organization*; every member's
  run on any harness (Claude Code, Codex, CI) draws on the same org entitlement and is attributed to it.
- **Metered by construction.** Each connected scan/run/review call the token carries is recorded as a
  usage event attributed to the org (action = the endpoint), and returns an `audit_id`. Usage is
  therefore accountable and billable without any extra bookkeeping in the skills.
- **Least privilege.** The token carries scope `scan:run` only — it runs scans, it does not administer
  the org. Rotate it on suspected leak; a rotated token invalidates the old value immediately.
- **No secret in the repo (SSOT = the environment/secret store).** The raw token lives only in the
  caller's environment or secret store, never in the plugin, a committed file, or an engagement log.
  This skill reads it, attaches it, and renews it — it never writes the raw value anywhere.

## Method

1. **Resolve the token** (in order, first hit wins), without logging the raw value:
   - `ASTERGUARD_ARS_TOKEN` in the environment — the headless/CI path (set it from your secret store).
   - For a signed-in org member, **mint-or-fetch** the org's *Default scan token* from the hosted
     scan-token endpoint (get-or-create; the raw value is returned only on mint or rotate, hash-only at
     rest). This is the interactive path when no env token is set.
2. **Attach** `X-ARS-Token: <token>` to every connected scan/run/review call — alongside the gateway's
   `Authorization: Bearer <JWT>`. Both headers ride together: the JWT authenticates to the gateway, the
   ARS token meters the scan.
3. **Renew on 401.** On `401 invalid or missing X-ARS-Token`, renew once and retry: refresh the member
   JWT and/or re-mint the scan token, then replay the single failed call. If renewal itself fails, stop
   and tell the user to re-authenticate — do not loop.
4. **Record the draw.** Append a lightweight metering `note` to the engagement (endpoint, `audit_id`,
   org) so quota usage is visible in `engagement.context()` — never the raw token.

## Practical Guidance

- **Env over interactive in CI.** A pipeline sets `ASTERGUARD_ARS_TOKEN` from its secret store; it should
  never mint interactively. A human on a laptop can let step 1's fetch mint the Default token once.
- **One org, many harnesses.** The same token value works across Claude Code, Codex, Cursor and CI —
  that is the point: the org's usage compounds and meters in one place.
- **An expired JWT reads as a missing ARS token.** If connected calls 401 after ~15 minutes of a session,
  it is almost always the member JWT, not the scan token — refresh the JWT first (step 3).
- **Never** echo the token to chat, commit it, or write it to `./.asterguard/`. Treat it like any other
  live secret (see the repo's secret-handling rule).

## Integration

- engagement — calls this at `open()` (connected mode) to ensure the token before any metered call; the
  metering note lands in the engagement's event stream
- security-engineer, pr-gate — their connected scan/run/review calls carry the token; a metered run is
  the norm, an unmetered env-fallback run the exception
- MCP wiring — the header travels with the gateway Bearer JWT (see `docs/MCP_WIRING.md`)
- AsterVault scan/run endpoints — the gate that verifies scope `scan:run` and records the usage event

## References

- [MCP wiring](../../docs/MCP_WIRING.md) — how the header rides with the gateway JWT
- [Run playbook](../../docs/RUN_PLAYBOOK.md) — the connect step
