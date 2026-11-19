# From app scan to red team — one self-improving Claude skill flow

The complete arc a security engineer runs in Claude Code: **scan the app → build the attack graph →
pick the targets → red-team them → prove the break → remediate → capture**. The `security-engineer`
orchestrator drives it; every other skill is a step; the AsterVault MCP is the one standardized source;
and the whole thing **gets smarter each run** because proven breaks feed memory.

The engineer supplies intent + scope once (the brief); the machine runs the rest.

## The flow

```
recall ─► scan ─► build the attack graph ─► pick targets ─► RED TEAM ─► prove ─► remediate ─► report ─► capture
  ▲       (local)   (SCA · data · info-flow)   (trifecta)   (attacker/      (canary   (PR +       (attack    (memory +
  │                                                          defender/judge)  egress)   enforce)    path)      promote)
  └──────────────────────── the corpus grows: next scan→red-team starts ahead ───────────────────────────────────┘
```

## Setup — install the skills

**Claude Code:**

```text
/plugin marketplace add Asterguard/asterguard-skills
/plugin install asterguard-security@asterguard-marketplace
```

**Cursor / Codex / other harnesses**, plus the scanners and offline-vs-connected mode, are in the shared
**[examples/SETUP.md](../SETUP.md)**. (In Cursor the skills aren't slash commands — invoke a skill by
asking the agent to run it by name.) To run the arc directly against a live gateway instead of as skills,
see [`RUN.md`](RUN.md) (the `driver.py` demo).

---

## Step by step (the prompt → the skills → the MCP)

**1. Recall + scope** — *"Scan `sales-copilot` and red-team its risky paths."*
`security-engineer` elicits the brief (target, objective, **scope + authorization**). `knowledge-recall`
→ `memory.recall` surfaces prior findings, **proven breaks**, waived paths, and the org's approved
patterns for this app. Cold run: empty; warm run: a head start.

**2. Scan (local)** — `local-scan` runs grype / checkov / trufflehog on the box → raw SCA / IaC /
secrets / AI-BOM findings. Nothing proprietary leaves; the code stays local.

**3. Build the attack graph** — `sca-graph` (dep tree + CVEs, deduped), `data-flow`, `information-flow`,
`agent-profiling`, `weakness-graph`. Findings resolve to canonical weaknesses + controls via
`registry.resolve` / `controls.map`; `graph.enrich` returns the **attack surface**.

**4. Pick the targets** — from `graph.enrich.attackSurface`: the **violating flows** — the lethal
trifecta legs (private data + untrusted input + egress + a missing control). `risk-context` prioritizes
by the features that matter offensively (reachability, `auth_anon`, `tool_authority`, `data_class`). Aim
at the path that reaches regulated data through an effectful egress tool.

**5. Red team the top targets** — `behavioral-redteam` composes the triad:
- `attacker(context)` seeds from memory + `testgen.patterns`, plants **fresh egress canaries**, drives
  adaptive multi-turn turns (crescendo / injection / decomposition); **attacker-model** recorded.
- `defender(attack_turn)` = the real target through the AsterVault proxy, with a concurrent benign task
  (utility under attack).
- `judge(turn, response, canary_evidence)` scores broke/held from evidence.

**6. Prove it** — a planted **canary on egress** (caught by the gateway, written to the tamper-evident
audit) is **demonstrated exfiltration** — the independent verifier, not a claim. `judge` → `broke`,
ASR@budget with the attacker model named.

**7. Remediate** — `remediation` turns the proven path into least-privilege policy-as-code (egress
allowlist + SPIFFE/IAM) via `asterguard-remediation` → a **PR**; on merge AsterVault `policy.apply`
**enforces** it at the gateway. The trifecta's egress leg is cut structurally.

**8. Report** — `risk-report` renders the **proven attack path** (red, `proven` badge) + findings + the
control crosswalk, as an HTML Artifact from the live `graph.enrich` / `risk.score` JSON.

**9. Capture (self-improve)** — `memory-capture` writes the decision + the proven break; `memory.promote`
graduates the reusable break into the pattern corpus `testgen.patterns` serves. **Next scan→red-team on
this app — or a sibling, in any harness — starts with these breaks already loaded.**

## Why this is one coherent skill, not nine tools

- **One orchestrator** (`security-engineer`) drives it; each step is a composable skill with typed I/O.
- **One standardized source** (the AsterVault MCP) — scan findings, weaknesses, controls, graph, risk
  features, attack corpus, and memory all speak the same schema, so the output of each step is the input
  of the next with no translation.
- **One loop** — recall at the front, capture at the back; the red-team's successes become the next
  run's seed. Scan → red team isn't a one-shot; it's a flywheel.
- **Human on intent, machine on execution** — the engineer authorizes scope once; the rest runs as-is.

## Governance
Authorized engagements only. The brief is the authorization gate; the attacker-model choice and every
tool call ride through the gateway's authn + policy + audit — the whole red-team run is accountable by
construction.
