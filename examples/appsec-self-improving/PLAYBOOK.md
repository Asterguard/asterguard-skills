# Playbook — self-improving AppSec for a security engineer

How one security engineer runs application security on an AI agent, end to end, from their own harness
— and how every run makes the next one faster and more consistent. The skills are the method; the
**AsterVault MCP gateway** is the shared brain (knowledge, analysis, memory), governed and team-shared.
Nothing proprietary ships to the client; the engineer's code and traffic stay local.

## The loop

```
   knowledge-recall ─► scope/scan ─► build graphs ─► test + canary ─► judge ─► remediate (PR) ─► enforce ─► memory-capture
        ▲  (pull prior patterns, decisions, waivers)                                                            │
        └──────────────────────────────── the loop compounds: capture → promote → recall ◄────────────────────┘
```

Each box is a skill; everything proprietary (registry, controls, scoring, patterns, memory) is an
AsterVault MCP call. Run it in Claude Code today, Cursor or Codex tomorrow — same gateway, same brain.

## Setup (once)

```bash
/plugin marketplace add Asterguard/asterguard-skills
/plugin install asterguard-security@asterguard-marketplace
export ASTERVAULT_MCP_URL="https://astervault.agenticrisklabs.io/mcp"   # .mcp.json wires the skills to the gateway
```

Then the engineer just talks to their agent: *"assess and red-team the support-agent, and remediate."*

Running in **Cursor / Codex** instead, or want the **offline** (no-gateway) setup and the scanner install?
That's the shared **[examples/SETUP.md](../SETUP.md)** — the loop above needs connected mode (the
`memory.*` / enforcement calls), so keep `ASTERVAULT_MCP_URL` set here.

---

## Run 1 — cold start (`support-agent`, a customer-support LLM agent)

**1. Recall.** `knowledge-recall` → `memory.recall({app: support-agent})` + `knowledge.patterns`.
First time on this app: memory is empty, but the **org's approved patterns** come back ("PII egress →
tokenize at the gateway; effectful tools require HITL"). The engineer starts with the house rules, not
a blank page.

**2. Scope + scan.** `security-engineer` picks source type `code`; `local-scan` runs grype/checkov/
trufflehog locally. `scan.plan` (MCP) says which lanes apply.

**3. Build the graphs.** `sca-graph`, `data-flow`, `information-flow`, `agent-profiling` assemble the
security graph locally (to `docs/graph-schema.md`). `weakness-graph` resolves each finding via
`registry.resolve` and maps controls via `controls.map` (MCP). The IFC overlay flags a **confidentiality
flow**: `admin_export_records (PII) → GET /admin/export`, reachable by an anonymous caller.

**4. Test + canary.** `behavioral-redteam` drives the attacker/defender episode; `canary-testing`
plants a **secret/honeytoken** in the export table and runs the attack with a benign task alongside.
The agent is routed through the gateway, so AsterVault **detects the canary leaving on egress** and
writes it to the tamper-evident audit — hard proof, not a judge's guess.

**5. Judge.** `security-judge` records the canary hit as a verified break, computes ASR@budget and
utility-under-attack, and attaches the weakness + control.

**6. Remediate as a PR.** `remediation` calls `asterguard-remediation` (`from_episode → emit → to_pr`):
emits a **SPIFFE** scoped-identity policy + an **egress allowlist** (deny all but the one legitimate
sink from the graph) + an **AsterVault PDP** rule, as a **pull request** (`emit-pr.sh`). The PR review
is the gate.

**7. Enforce.** On merge, AsterVault `policy.apply(bundle, approved=true)` loads the bundle and enforces
the egress allowlist + tokenization at the gateway — the leak is closed structurally.

**8. Capture.** `memory-capture` writes the outcome: *finding* (PII exfil via /admin/export), *fix* (the
egress+SPIFFE policy that closed it), and a *decision* ("anonymous admin routes are forbidden; tokenize
PII egress"), each scoped to `support-agent` with provenance (the PR + commit). The engineer promotes
the egress pattern (`memory.promote`, review-gated) into the **approved patterns**.

Elapsed: a full, evidence-backed AppSec pass with an enforced fix and a reviewable PR.

---

## Run 2 — warm (weeks later, a *different* engineer, in *Codex*)

Someone adds a new export endpoint to `support-agent` and asks Codex to "check this before we ship."

**1. Recall is no longer empty.** `memory.recall({app: support-agent, topic: egress})` returns Run 1's
decision and fix: *"anonymous admin routes forbidden; PII egress must tokenize; approved pattern:
egress-allowlist + SPIFFE."* `knowledge.patterns` returns that promoted pattern. The agent starts
already knowing the rule and the shape of the fix — **in a different harness than Run 1 wrote it**.

**2–6.** The scan + graph + canary run as before, but when the new endpoint trips the same
confidentiality flow, remediation **reuses the approved egress pattern** instead of re-deriving it —
consistent with Run 1, generated as a PR in seconds.

**7–8.** Enforced, and the new finding + fix captured. If the new endpoint needed a *waiver* (e.g., an
internal-only export), that waiver is captured with its justification and scope, so the *next* run
recalls it and doesn't re-flag it — but a human can revisit it because the reasoning is recorded.

The second pass is faster, more consistent, and cross-harness — the knowledge compounded.

---

## Why it's self-improving (and safe)

- **Capture → promote → recall** is the flywheel: each assessment's decisions and fixes become memory;
  curated ones become org patterns; the next task recalls both.
- **Cross-harness:** one gateway serves Claude Code, Cursor, Codex alike, so a lesson learned in one
  tool improves the others (`docs/MCP_WIRING.md`).
- **Governed and team-shared:** every recall/capture/enforce goes through AsterVault's authn → PDP/PEP →
  append-only audit, tenant/team-scoped with cross-tenant isolation. Memory is shared with the team,
  not the world.
- **No data shipped:** the engineer's code, traffic, and the generated graph stay local; only structural
  queries and captured decisions reach the gateway, and the proprietary knowledge never leaves it.

## The 10-minute narration

> "A security engineer runs an AppSec pass from their own agent. It **recalls** what the team already
> knows about this app, **scans** locally and builds the security graph, **red-teams** it with planted
> **canaries** that the gateway verifies on egress, **remediates** by generating a least-privilege
> egress/identity policy as a **pull request**, **enforces** it at the gateway on merge, and **captures**
> the decision back into shared memory. The next engineer — in a different tool — starts with that
> knowledge already loaded. The system gets better every time it's used, and no proprietary data or
> customer code ever leaves where it belongs."
