---
name: hunt-agentic-ttp-credential-access
description: Use when running a guided, hypothesis-driven hunt for credential-access TTPs in the agent context — agent token theft, secret/API-key exfiltration, over-broad credential scope use, or an agent reading another principal's secrets — across the security graph and recorded agent events, feeding confirmed gaps to detection-as-code.
---

# Hunt: Agentic Credential-Access TTP

Guided TTP hunt for the agent-security analogue of MITRE Credential Access: an agent or tool obtaining
credentials it should not have — stealing or replaying its own token, exfiltrating secrets/API keys
from config or tool results, using an over-broad credential scope, or reading another principal's
secret store. Research the technique, build the sweep over the graph + recorded events, confirm or
clear, and ship a rule for any confirmed gap.

## When to Activate

- Intel or a hypothesis points at credential theft/misuse by an agent (leaked token, secret in a tool
  result, scope creep on a service principal).
- A triage/investigation runbook flagged suspicious credential or secret access worth a proactive hunt.

## Objective

Prove or clear credential-access activity against `${TARGET}` under `${HYPOTHESIS}`, scoped to the
named techniques, and route confirmed theft/misuse to incident response.

## Scope

Covers: credential-access TTPs in the agent context (token theft/replay, secret/key exfil, over-broad
scope use, cross-principal secret reads). Excludes: lateral tool-abuse chains
(`hunt-tool-abuse-lateral`), injection exposure (`hunt-prompt-injection-exposure`), containment (IRPs).

## Inputs

- `${HYPOTHESIS}`: string — the credential-access hypothesis (e.g. "the billing agent's token is being
  replayed to read the secrets vault"). *Source:* analyst / intel.
- `${TECHNIQUES}`: the agentic credential-access behaviors to hunt (token theft/replay, secret exfil,
  scope abuse, cross-principal read). *Source:* hypothesis + weakness registry.
- `${TARGET}`: engagement target. *Source:* engagement.
- `${SCOPE_FILTER}` (optional): narrow to an identity / component / namespace.
- `${LOOKBACK}` (optional): recorded-event window.

## Outputs

- `${HUNT_FINDINGS}`: confirmed/suspected credential-access activity with evidence (identity nodes,
  secret/egress edges, event rows), per technique, with negative results noted.
- `${DETECTION_GAPS}`: confirmed behaviors lacking a covering rule → `detection-as-code-agent-rules`.
- `${ESCALATION}`: incident/finding id if escalated.
- `${STATUS}`: ["Success" | "Partial" | "Failure"] with per-lane notes.

## Tools

- **Gateway (connected, metered — `X-ARS-Token`, record `audit_id`):** `knowledge.query`/`knowledge.patterns`
  (technique procedures + detection ideas), `registry.resolve` (map each technique to its weakness id),
  `graph.enrich` (identities, granted scopes, secret stores, reach), runtime `security.*` (recorded
  token/secret access + egress), `risk.score`.
- **Client-side:** translate each technique into a graph/event query; analyze for anomalous
  credential/secret access; correlate to the hypothesis; decide verdict.
- **Sibling skills:** `engagement`, `enrich-indicator`, `pivot-on-indicator`, `record-in-engagement`,
  `detection-as-code-agent-rules`; atoms `atom-lookup-identity`, `atom-query-pattern`,
  `atom-trace-egress`, `atom-resolve-weakness`.

## Workflow Steps & Diagram

1. **Open engagement.** `engagement.open(${TARGET})` → context. Connected: ensure the ARS token.
2. **Research the techniques.** `atom-query-pattern` (`knowledge.query`) per technique for procedures +
   detection ideas; `atom-resolve-weakness` to bind each to its registry weakness id.
3. **Build the sweep.** From the technique shapes, construct queries over the graph (identities →
   granted scopes → secret stores/egress) and over recorded agent events (`security.*`): token reuse
   from a new context, a secret value reaching an egress edge, a scope used beyond its grant, one
   principal reading another's secret.
4. **Execute + analyze.** Run the sweep over `${LOOKBACK}` (apply `${SCOPE_FILTER}`); flag low-prevalence
   / anomalous credential access. Note negative results per technique.
5. **Enrich + pivot.** For each hit, `enrich-indicator` the identity/secret/egress; `pivot-on-indicator`
   to related nodes (what else holds that scope, where did the secret go).
6. **Decide + escalate.** Confirmed theft/misuse → open a finding and hand to
   `irp-agent-credential-compromise`. Clean → document the cleared hypothesis.
7. **Close the gap + checkpoint.** Emit `${DETECTION_GAPS}` for `detection-as-code-agent-rules`;
   `record-in-engagement`; `engagement.checkpoint`.

```mermaid
graph TD
    START([${HYPOTHESIS} + ${TECHNIQUES}]) --> OPEN["engagement.open(${TARGET})"]
    OPEN --> RES["research: knowledge.query + registry.resolve"]
    RES --> SWEEP["build sweep: graph identities/scopes/secrets + security.* events"]
    SWEEP --> ANALYZE{"anomalous credential access?"}
    ANALYZE -- "hit" --> ENR["enrich-indicator + pivot-on-indicator"]
    ENR --> VERDICT{"confirmed theft/misuse?"}
    VERDICT -- "yes" --> ESC["finding_opened → irp-agent-credential-compromise"]
    VERDICT -- "suspected/no" --> DOC["document (incl. negatives)"]
    ANALYZE -- "clean" --> DOC
    ESC --> GAP["${DETECTION_GAPS} → detection-as-code-agent-rules"]
    GAP --> CP["record-in-engagement + checkpoint"]
    DOC --> CP
```

## Decision Logic / Completion Criteria

- **Confirmed** when a recorded event shows a credential/secret obtained or used outside its granted
  scope/principal, corroborated by a graph path (identity → secret/egress). **Suspected** when the
  anomaly is present but the grant path is ambiguous.
- Confirmed → escalate to `irp-agent-credential-compromise`; never revoke/contain inside the hunt.
- **Done when:** every technique has been swept (with negatives recorded), hits are enriched and
  verdicted, gaps are handed off, and the engagement is checkpointed.

## Integration

- **Composes:** `enrich-indicator`, `pivot-on-indicator`, `record-in-engagement`,
  `detection-as-code-agent-rules`; `engagement` bookends; atoms `atom-lookup-identity`,
  `atom-query-pattern`, `atom-trace-egress`, `atom-resolve-weakness`.
- **Called by:** `threat-hunt` playbook; escalates to `irp-agent-credential-compromise`.
- **Offline:** sweep runs over the local graph + recorded events; technique research degrades to local
  pack/registry data; note degraded lanes. **Connected:** full knowledge/graph grounding + runtime
  `security.*`, metered.
