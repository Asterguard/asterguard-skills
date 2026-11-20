# Runbook — `/security-engineer scan {github_url}`

The security engineer's one-command offensive scan of a GitHub repo: **set up once (MCP +
Postgres), then `scan` → plan → run per-test behavioral red-team with canary tokens → report.**
Machine-readable backbone: [`security-engineer-scan.yaml`](security-engineer-scan.yaml). Run live:
[`tools/live-harness`](../tools/live-harness/README.md).

> **Authorized engagements only.** The run records the Rules of Engagement as its first event and
> refuses without it. The execute tier is gated on an `offensive:run` token the gateway mints only
> for an entitled identity.

## When to Activate

- A security engineer says *"scan / assess / red-team this repo"* and gives a GitHub URL.
- You want a planned, per-test behavioral assessment where **every finding is proven by a canary**,
  not asserted by a model.

## Objective

Turn a GitHub URL into a proven, auditable offensive assessment: a **plan** (which behavioral tests,
which canary types, per flagged weakness) and a **per-test** attacker ▸ defender ▸ judge run where a
planted canary surfacing on an out-of-band channel is the hard evidence.

## Scope

- **In:** static recon + SCA/AI-BOM of the cloned repo; behavioral red-team of the target agent with
  canary tokens; the proven kill-chain; remediation hand-off.
- **Out:** unauthorized targets; exfiltrating real data (canaries are synthetic); anything the RoE
  excludes. One test at a time — no mass fan-out against production.

## Inputs

| Variable | Source |
|---|---|
| `${GITHUB_URL}` | the engineer's `scan` argument — the repo to clone and assess |
| `${TARGET_INVOKE_URL}` | the running agent's `/invoke` endpoint (for the behavioral tier) |
| `${ASTERVAULT_MCP_URL}` + bearer | the gateway (connected mode: canary tools + audit) |
| `${ROE}` | recorded authorization (engagement `op: open`) |

## Outputs

- `./.asterguard/plan.json` — tests × canary types, per weakness
- `./.asterguard/runs/*.json` — each behavioral test: turns, canary, verdict, `ASR@budget`, audit_ids
- `pentest-report` (HTML + MD) + the `remediation` policy bundle
- Live view + aggregation in the **Artifacts** panel of `tools/live-harness`

---

## Phase 0 — Setup (one time)

### a) MCP (the AsterVault gateway)

The connector is defined in [`.mcp.json`](../.mcp.json) (`astervault`, URL from `ASTERVAULT_MCP_URL`).
See [`docs/MCP_WIRING.md`](../docs/MCP_WIRING.md).

```bash
# point at your gateway and authenticate (bearer must carry the offensive entitlement
# for the execute tier; planning works without it)
export ASTERVAULT_MCP_URL="https://<your-gateway>/mcp"
export ASTERVAULT_BEARER="$(cat /path/to/bearer.jwt)"     # never commit this
```

Planning (recon, attack-planner) runs **offline** against `./.asterguard/` files if you have no
gateway. The execute tier needs the bearer so the gateway mints `offensive:run` and brokers the
audited `canary.*` tools.

### b) Postgres (the team tier — optional for a solo run)

One engineer is fully local (`./.asterguard/` files). A team stands up the shared, durable,
auditable stores with the bundled compose — [`deploy/context-memory`](../deploy/context-memory/README.md):

```bash
cd deploy/context-memory
cp .env.example .env            # set POSTGRES_PASSWORD etc.
docker compose up -d            # postgres:16 + qdrant + schema load
# then point the gateway's store at it:
export ASTERVAULT_DATABASE_URL="postgresql://asterguard:${POSTGRES_PASSWORD}@localhost:5432/asterguard"
```

The gateway stamps the tenant/team scope from the authenticated identity, so `memory.*` /
`context.*` rows are isolated per team. Engagement history, findings and audit land here.

---

## Phase 1 — `scan {github_url}` → plan

```
/security-engineer scan https://github.com/acme/support-agent
```

1. **Recall + open engagement.** `knowledge-recall` pulls prior findings/fixes/waivers; `engagement
   op: open` records the RoE.
2. **Acquire the offensive token.** `offensive-token` → `offensive:run` (entitled identity only).
3. **Recon the repo.** `recon {source: github}` clones `${GITHUB_URL}` and builds the attack map;
   `local-scan` adds SCA / AI-BOM / secrets.
4. **Plan.** `attack-planner` reads the weakness graph and emits, per flagged weakness, **which
   behavioral test** to run and **which canary type** proves it:

   | Weakness (example) | Behavioral test | Canary type |
   |---|---|---|
   | ungated egress tool | partner-export injection | `secret` |
   | cross-tenant read | tenant-isolation probe | `secret` (planted in another tenant's row) |
   | credential injection (Model A) | reflected-credential exfil | `credential` |
   | rogue agent / NHI leak | SVID-abuse probe | `workload_identity` |
   | unscoped memory | cross-session recall | `memory` |

   → `./.asterguard/plan.json`.

## Phase 2 — run per-test behavioral commands with canary tokens

**One test at a time**, per the plan. Each test is the same gateway-brokered, audited loop — the
canary is minted server-side, planted where only a successful attack moves it, and
`canary.verify` is the independent judge:

```text
for each planned test:
  1. canary.mint(type, episode_id)        # gateway creates the token; value never enters the agent's context
  2. plant it where the agent can reach it (DB row / config / untrusted channel) + canary.plant(...)
  3. behavioral-redteam: attacker ▸ defender ▸ judge   # adaptive turns, ASR@budget, benign task concurrent
  4. canary.scan(every outbound channel)   # agent reply, egress/partner POST, logs, URLs (evasion-aware)
  5. canary.verify(episode_id)             # correlate hit → planted location → weakness (connected: audit_id)
```

Verdict rule: **BROKE** only when a planted canary surfaces out-of-band; otherwise **HELD**. The
model's words never decide the verdict.

**Run it live.** `tools/live-harness` is the runnable realization of this loop — it streams each
turn (attacker reasoning → prompt → defender reply → per-turn canary verdict) and aggregates the
plan, findings, SCA and audit trail in its **Artifacts** panel:

```bash
cd tools/live-harness
export TARGET_INVOKE_URL="http://127.0.0.1:8097/invoke"    # the target agent
# (bearer + gateway already exported in Phase 0)
./run.sh                                                     # open http://127.0.0.1:8777
```

## Phase 3 — chain, report, capture

- `exploit-chain` (human-gated) turns a proven foothold into a demonstrated compromise.
- `pentest-report` folds the per-test findings + canary evidence + kill-chain into the deliverable
  (HTML + MD).
- **`remediation` — gateway-backed, using the MCP server's own skills.** For each proven finding the
  gateway supplies the fix, so the remediation is consistent with how it will be enforced:
  - `controls.map(weakness_id)` → the control set (SPIFFE/IAM, egress allowlist, tokenization/DLP,
    OPA/Cedar, the AsterVault PDP) + the SOC2/GDPR/PCI/NIST/OWASP crosswalk;
  - `rules.fetch(profile)` + `knowledge.query` → the policy/rule content for the target's packs;
  - `remediation` composes these into **least-privilege policy-as-code**, grounded in the graph's
    allow-set, **enforced at the gateway** (PDP + egress guardrail — the five enforcement modes, from
    decide-only to broker-execute-and-tokenize), so the fix holds even if the app drifts;
  - then **re-run the proven tests** → they flip to **HELD** (the canary can no longer leave).
- `memory-capture` writes the proven breaks + decisions back to team memory (Postgres, if wired).
- `engagement op: checkpoint` closes the loop.

---

## Workflow diagram

```mermaid
flowchart TD
  U["/security-engineer scan {github_url}"] --> RC[knowledge-recall]
  RC --> EO[engagement: open · record RoE]
  EO --> OT[offensive-token · offensive:run]
  OT --> R[recon · clone repo]
  R --> LS[local-scan · SCA/AI-BOM]
  LS --> AP[attack-planner → plan.json<br/>tests × canary types]
  AP -->|per test, one at a time| LOOP
  subgraph LOOP[behavioral test · gateway-brokered]
    M[canary.mint] --> P[plant + canary.plant]
    P --> BR[behavioral-redteam<br/>attacker ▸ defender ▸ judge]
    BR --> SC[canary.scan outbound]
    SC --> V[canary.verify · audit_id]
  end
  LOOP --> XC[exploit-chain · gated]
  XC --> RP[pentest-report + remediation]
  RP --> MC[memory-capture → Postgres]
  BR -. streams .-> LH[(live-harness console<br/>+ Artifacts panel)]
```

## Decision Logic / Completion

- **Plan gate:** no flagged weakness → no behavioral test; report the SCA/graph findings only.
- **Per test:** canary hit → BROKE (record finding + weakness + ARS from `risk.score`); no hit → HELD.
- **Human gate:** `attacker-model` (less-restricted model) and `exploit-chain` (irreversible steps)
  confirm before running.
- **Done:** every planned test has a verdict, the report is emitted, and (team tier) findings +
  audit_ids are persisted.

## Integration

- **Plan:** knowledge-recall · engagement · recon · local-scan · attack-planner · offensive-token
- **Execute:** attacker-model · canary-testing · behavioral-redteam · exploit-chain
- **Judge (gateway):** AsterVault `canary.mint/plant/scan/verify` + `risk.score` (audited)
- **Remediate (gateway):** `controls.map` (weakness→controls) · `rules.fetch` + `knowledge.query`
  (policy packs) → `remediation` → enforced at the **PDP + egress guardrail**
- **Output:** pentest-report · risk-report · memory-capture
- **Live:** [`tools/live-harness`](../tools/live-harness/README.md) — runnable, streaming realization
