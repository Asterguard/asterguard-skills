# Offensive security / red teaming with these skills

The same stack a defender uses runs offense. The difference is intent and direction: a red-teamer uses
the **graph to choose where to attack**, an **adaptive multi-turn attacker** to get there, and
**canaries to prove impact** — then feeds what worked back into memory as a reusable break corpus.

Authorized engagements only. This is for a security engineer red-teaming **their own** org's agents.

## The red-team loop

```
map the target ─► pick the path ─► plan the campaign ─► execute (adaptive, multi-turn) ─► PROVE it ─► report + feed forward
   (graph)          (trifecta)        (patterns)           (attacker vs target, canaries)   (canary)      (memory corpus)
```

### 1. Map the target (recon)
`proxy-recon` (route the agent through the gateway → the audit trail is your recon) + `agent-profiling`
+ `data-flow` + `information-flow` build the **attack graph**. This is the offensive map: it shows the
tools, the authority boundaries, and — critically — the **lethal trifecta legs**: where private data,
untrusted input, and an outbound channel meet. You attack the graph, not blindly.

### 2. Pick the path (highest-value target)
From `graph.enrich.attackSurface`: the violating flows (regulated data reachable by an untrusted source
with a missing control), over-privileged tools, anonymous-reachable stores. `risk-context` prioritizes
by the features that matter offensively — reachability, auth_anon, tool_authority, data_class. Aim at
the one path that reaches regulated data through an effectful egress tool.

### 3. Plan the campaign
`testgen.patterns(weakness_id)` returns the attack corpus; `behavioral-redteam` grounds a suite in the
chosen path. Strategies: **crescendo** (gradual escalation), **PAIR/TAP** (iterative/tree refinement),
**many-shot**, **persona**, **decomposition** (split a harmful goal across benign turns), **injection**
(direct + indirect via tool results / RAG / a planted document).

### 4. Execute — attacker vs target, adaptive and multi-turn
An **attacker model** (ideally a less safety-restricted research model) drives user turns and/or
injected content against the **exact target config** (its real system prompt, tools, defenses) through
the gateway. It carries a strategy library and **memory of past attempts**, uses the target's responses
to adapt (static jailbreak lists overstate robustness), and runs a concurrent benign task to measure
**utility under attack**. Reset the sandbox with **fresh canaries per attempt**; report **ASR@budget**
(ASR@1/@10/@100) and the attacker model used — never a bare success rate.

### 5. Prove it (the offensive deliverable)
`canary-testing` plants honeytokens (a fake secret in the store, a credential in the mock auth, a
document the task never needs). A canary appearing on **any** egress — email, HTTP, a markdown image
URL, a commit, base64/split-encoded — is **demonstrated exfiltration**, detected by the gateway on the
wire and written to the tamper-evident audit. That's the thing offensive work is usually weak at:
*proof of impact*, not "it might be exploitable." The independent verifier is the gateway, not your
claim and not the target's self-report.

### 6. Report + feed forward
`risk-report` renders the **proven attack path** (red, `proven` badge) + the kill chain + ASR. Then
`memory-capture` + `memory.promote` save the **proven break** into a reusable corpus — the red team's
own library of what worked on this org, recalled on the next engagement. And the broke tests hand
straight to the blue team as **regression tests** (offense feeds defense).

## Offensive principles (from the eval literature)

- **Budget the attacker** — ASR is meaningless without effort; report it as a function of attempts.
- **Adaptive > static** — defenses that look strong against a fixed list fall to an attacker that uses feedback.
- **Independent verification** — decide "succeeded" from out-of-band evidence (canary, egress log, state
  diff), never the target's or the attacker's own report.
- **Utility under attack** — a defense that refuses everything isn't secure, it's broken; measure it.

## What's strong vs. the honest gaps

**Strong:** the graph tells you *where* (targeted, not spray-and-pray), adaptive multi-turn campaigns,
hard canary proof, and a memory corpus that compounds across engagements — run locally from your own
agent, no SaaS.

**DAST execution — an adapter, not an engine we own.** Assume a configured **HTTP-layer / DAST harness**
exists (the customer's internal implementation, or ZAP / AgentDojo). The skills *generate and target*
the tests from the graph and drive them through a pluggable adapter — the same seam as AsterVault's
resource adapters. Swapping the harness never changes the skills. So this is an integration point, not a
build.

**Payloads — not a static exploit library (that's the old model).** Payloads come from three sources
that beat a frozen DB: (1) **`testgen.patterns`** — a server-side corpus, extensible as data, seedable
from public sets (PyRIT, Garak, Nuclei, promptfoo); (2) the **adaptive attacker model**, which generates
and refines payloads per turn from the target's feedback; (3) **memory** — proven breaks on this org
become reusable exemplars. Static jailbreak lists *overstate* robustness; the corpus + adaptive + memory
model is the modern, stronger approach. The only real work is **seeding the corpus well**, not shipping a
monolithic exploit database.

**Formerly the remaining gaps, now first-class skills:** the two additive gaps — attacker-model
selection and exploitation beyond proof-of-reach — are now closed, and the whole loop is a named
offensive posture:

- **`offensive-engineer`** — the authorized-pentest orchestrator (the `pentest` playbook): authorize →
  recon → plan → campaign → exploit-chain → prove → report → feed-forward. Rules of engagement are a
  mandatory, recorded step 0.
- **`recon`** — the attack-map + path-selection skill (doctrine steps 1–2).
- **`attack-planner`** — the MCP as a **knowledge base**: given the agent, it decides *what* to test
  (test kinds + example techniques), which **canary types** to plant (egress / credential-identity /
  **workload-identity** / injection / **memory** / **context** / document / …), the budget, and the next steps.
- **`exploit-chain`** — chains a canary-proven foothold into a demonstrated multi-step compromise
  (escalate → lateral → impact), each step independently proven (closes "beyond proof-of-reach").
- **`attacker-model`** — selects and **governs** the attacker model: authorized-only, recorded in the
  run artifacts + the audit, reported with ASR (closes "attacker-model selection").
- **`pentest-report`** — the compliance-ready deliverable (PoCs + ASR@budget + kill-chain + remediation
  + regression handoff).

Still deferred (server-side, additive): **seeding the `testgen.patterns` corpus well** (PyRIT / Garak /
Nuclei / promptfoo) and extending `canary.mint` with the workload-identity type — an astervault
follow-up, the same shape as the gateway integration.

## Dual-use note

Everything here is for **authorized** testing of systems you own or are engaged to test. The gateway's
authn + policy + audit mean every offensive action is itself identified, scoped, and logged — red-team
runs are accountable by construction.
