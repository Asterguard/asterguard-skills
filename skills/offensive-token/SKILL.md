---
name: offensive-token
description: Gate offensive execution behind a separate privileged token — present the org's privileged offensive credential (scope offensive:run, sent as the X-ARS-Offensive-Token header) on every behavior-changing attack against a live target, and refuse to execute offense without it. The everyday scan token (scan:run) can plan an attack but can never run one. Use at the start of any pentest / red-team execution; the gateway blocks offensive ops that lack this token.
---

# Offensive Token (the privileged skill tier)

Offense changes a live agent's runtime behavior — injected turns, abused tools, planted canaries — so it
runs on a **separate, higher-trust credential**, not the everyday scan token. The **offensive token** is
the org's privileged credential (`asg_off_…`, scope **`offensive:run`**) presented as the
**`X-ARS-Offensive-Token`** header on every *execution* call. The gateway's PDP enforces it: an offensive
operation without `offensive:run` is **blocked (`403 offensive privilege required`)**. This is what makes
"offensive security is off unless explicitly allowed" a control, not a convention.

> **Plan vs execute — the privilege boundary.** You can *plan* an attack on the scan tier (`recon`,
> `attack-planner` read the knowledge base with the normal `X-ARS-Token`). You cannot *execute* one —
> drive adversarial turns, chain a compromise, plant a live canary, or run the forge engine — without the
> offensive token. The gateway enforces the line at the runtime (attacker↔target) path.

## When to Activate

- The first step of any offensive **execution** (`offensive-engineer` step 0 acquires it before the
  campaign): `attacker` / `behavioral-redteam` (live) / `exploit-chain` / live `canary` ops / a
  less-restricted `attacker-model` / the forge-behind-MCP engine.
- On `403 offensive privilege required` from any runtime/offensive endpoint (the token is absent, lacks
  `offensive:run`, or expired).
- **Not** for planning or defensive analysis — `recon`, `attack-planner`, `local-scan`, the graph skills
  run on the scan tier (`ars-token`) and need no offensive token.

## Core Concepts

- **Separate credential, separate grant.** The offensive token is distinct from the ARS scan token and
  **separately provisioned** (higher trust, provisioned-on-request — not a member self-mint like the
  Default scan token). The scan token carries `scan:run` only and can never attack; the offensive token
  carries `offensive:run`. Both ride together on execution calls, alongside the gateway Bearer JWT.
- **The gateway is the enforcer.** The client refuses early for a fast, clear failure, but the real gate
  is server-side: the PDP checks `offensive:run` on every behavior-changing op and the audit records it.
  A client that forgot to attach it still gets blocked.
- **Scoped + time-boxed.** An offensive token is scoped to the authorized engagement and short-lived;
  rotate on suspected leak. A rotated token invalidates the old value immediately.
- **No secret in the repo.** The raw value lives only in the environment / secret store; this skill reads
  it, attaches it, and renews it — never writes it to the plugin, a committed file, or `./.asterguard/`.

## Method

1. **Require authorization first.** The engagement must already carry a recorded RoE authorization
   (`offensive-engineer` step 0). No authorization → do not even resolve the token; refuse.
2. **Resolve the offensive token** (without logging the raw value):
   - `ASTERGUARD_OFFENSIVE_TOKEN` in the environment — the CI / headless path (from the secret store).
   - Interactive: the signed-in member requests the org's offensive token from the hosted endpoint. This
     is a **privileged grant**, not a get-or-create — it is issued only to an entitled org and recorded.
   - **Absent → refuse to execute.** Report "offensive execution requires the privileged offensive token
     (`offensive:run`); planning only is available." Do not fall back to the scan token for execution.
3. **Attach** `X-ARS-Offensive-Token: <token>` to every execution call, alongside `X-ARS-Token`
   (metering) and `Authorization: Bearer <JWT>` (gateway auth).
4. **Renew on 403/401.** On `403 offensive privilege required` or an expiry 401, renew once and retry the
   single failed call; if renewal fails, stop and tell the user to obtain/refresh the offensive grant —
   do not loop and do not downgrade to the scan tier.
5. **Record the grant use.** Append a `decision` note to the engagement (the offensive op, `audit_id`,
   org) so privileged use is visible in `engagement.context()` — never the raw token.

## Practical Guidance

- **Least privilege by tier.** If a run only needs to *plan* or *analyze*, it never touches this token —
  keep offensive execution and its credential as small a surface as possible.
- **Env over interactive in CI.** A pipeline sets `ASTERGUARD_OFFENSIVE_TOKEN` from its secret store and
  runs offense only in jobs explicitly entitled for it.
- **Never** echo, commit, or write the token to `./.asterguard/`. Treat it as the most sensitive secret
  in the engagement — it authorizes attacks.

## Integration

- **ars-token** — the complementary scan credential (`scan:run`); planning/analysis uses that, execution
  adds this.
- **offensive-engineer** — acquires this at step 0 (after the RoE gate); refuses the execution phases
  without it.
- **attacker · behavioral-redteam · exploit-chain · attacker-model · canary-testing (live)** — their
  behavior-changing calls carry it; the gateway blocks them otherwise.
- **MCP wiring** — the header and the `offensive:run` enforcement (see `docs/MCP_WIRING.md`).
- **Server (astervault follow-up)** — the PDP that enforces `offensive:run`, the forge-behind-MCP engine
  it unlocks, and the privileged token minting.
