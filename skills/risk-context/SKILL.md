---
name: risk-context
description: Give the agent the full risk CONTEXT for a finding or app — the model's feature vector (KEV, EPSS, reachability, data class, tool authority, blast radius, exposure, …) plus the attack path and control status — so it can calculate and explain risk itself, to the org's appetite, instead of consuming a black-box score. Use when a security engineer wants to reason about, prioritize, or calibrate risk, not just read a number.
---

# Risk Context

Don't hand down a number — hand over the **context to compute one**. This skill lays out the risk
features with their reasoning so the agent (or engineer) reasons to a risk judgment transparently, maps
the app's tests/findings onto those features, and can **build its own calibration** over them.

**Free vs Enterprise (the line):**
- **Free** — the feature **explanations** (`references/features.md`: what each means, why it matters, how
  tests map to it) + the feature **values** from your own scan + **your own reasoning**. No number needed.
- **Enterprise** — the calibrated **ARS (0–10)** + band + the four scoring heads, i.e. the weight tables
  that collapse the features into one number. The weights are the proprietary model and stay server-side.

So the free tier is fully useful on its own: the agent reasons about risk from the features; enterprise
adds the calibrated score on top of the same features.

## When to Activate

- The engineer asks "how risky is this, and why?" or "what should we fix first?".
- You want a risk judgment the org can **see and adjust**, not a black box.
- Calibrating risk to the org's appetite, or teaching another system to score risk.

## The feature vector (the context the MCP returns)

For a finding/app, `risk.score` returns these **feature values** (0–1) — the raw material for reasoning:

| Feature | What it tells you |
|---|---|
| `severity_weight` | the scanner's severity (the **floor** — risk is never below it) |
| `owasp_weight` | OWASP-LLM category weight (injection / disclosure / excessive-agency rank high) |
| `data_class` | sensitivity on the path — public → internal → PII/PCI/PHI → regulated |
| `kev` | is it a **known-exploited** vulnerability (CISA KEV)? |
| `epss` | exploit **probability** (EPSS, 0–1) |
| `reachability` | runtime · reachable · build-only · unreachable — **the biggest lever** |
| `tool_authority` | can it **act** (effectful tool / agency / exfil / rce)? |
| `blast_ctx` | blast radius — single resource → tenant → account → org |
| `business_criticality` / `asset_criticality` | how much the asset matters |
| `external_facing` | internet-reachable? |
| `auth_anon` | reachable **anonymously**? |

The model aggregates these through four heads — **Exploitability**, **Exposure**, **Blast radius**,
**Attack/Breach** — then floors at severity and bands (critical ≥9 · high ≥7 · medium ≥4). The exact
weights are the calibration and stay server-side; the **feature values and the heads** come back so you
can reason without them.

## Method

1. `risk.score({finding})` or `{app}` → `features` (the 12 values) + `floor`. On enterprise the response
   also carries `{ars, band, breakdown}`; on free it's the features alone — reason from them.
2. **Map the app's tests/findings onto the features** (LLM-reasoned, see `references/features.md`): e.g. a
   `canary.verify → fired` ⇒ runtime-reachable + anonymous + the canary's data class; an SCA CVE ⇒
   severity + kev/epss + reachability. State the mapping, don't just assert a level.
3. Pull the surrounding context: the attack path + `missing_control` (`graph.enrich`), the proven
   evidence, the data classes on the path.
4. **Reason to a judgment:** lead with the dominant features — "KEV + runtime-reachable + anonymous +
   PII ⇒ top-tier" — and name what's *missing* ("not reachable" or "a passing DLP control" would drop it).
5. **Prioritize** by the features the org weights most (reachability + KEV + regulated data first).
6. On enterprise, use the ARS to sanity-check the reasoning; if you disagree, say why (a feature the
   model can't see — e.g. a compensating control it didn't know about).

## Build-your-own calibration

Because the **features** are provided, the agent (Claude or another system) can define its *own*
weighting — the org's risk appetite — over them, and **learn it from memory**: `memory.recall` the past
decisions/waivers for this app, see which findings the team actually actioned, and weight accordingly.
That calibration is itself a skill the agent can write, grounded in the standardized features here.

## Practical Guidance

- **Features over the digit** — "9.2 because KEV, reachable, SSN" is actionable; "9.2" alone isn't.
- **Respect the floor** — never argue a `high` finding down to medium; argue *above* the floor.
- **Reachability and auth_anon dominate** — a critical that's unreachable is rarely the top fix; say so.
- **Don't re-ship the weights** — the calibration lives in the MCP; reason from the returned features.

## Integration

- weakness-graph, information-flow, canary-testing — supply the feature inputs + the proven evidence
- remediation — each "what-moves-it" feature maps to a policy fix
- risk-report — renders the scored, contextualized findings into the attack-path visual
- memory — past outcomes train the org's own calibration
- AsterVault `risk.score` (features + heads), `graph.enrich`

## References

- [Risk features — explanations + test→feature mapping (free tier)](./references/features.md)
- [AsterVault MCP tools](../weakness-graph/references/astervault-tools.md)
