# AsterGuard Security Skills

**Agent-native application security — the method ships as skills, the knowledge stays behind a gateway.**

Instead of installing a scanner library or calling a hosted API, you add these skills to your agent
harness (Claude Code or Codex). The agent then **performs the review itself** — scans locally, builds
the security architecture (SCA graph, data-flow, information-flow, weakness graph), generates DAST +
behavioral red-team tests, runs an attacker ▸ defender ▸ judge campaign with canaries, and emits a
risk report with recommended enforcement policies.

The *method* lives in the skills (open, thin, local). The proprietary *knowledge* — the 578-weakness
registry, the control crosswalk, the calibrated risk models, the attack-pattern corpus, the
cross-session memory — lives server-side behind the **AsterVault MCP gateway** and is never shipped to
the client. The only client binaries are raw collectors (`grype`, `checkov`, `trufflehog`) and a small
proxy; everything else is the harness's own model following each skill against one shared schema
([docs/graph-schema.md](docs/graph-schema.md)).

> **One question up front: do you need our server to run these?** No — the skills run standalone in
> **offline mode** (local scan, graphs, generated tests, a full report, even the red-team loop, all on
> the harness's own model). What the **AsterVault MCP** adds is *grounding, governance and memory*:
> registry-backed weakness IDs, the framework crosswalk, calibrated ARS, an independent canary
> verifier, enforcement, and the self-improving flywheel. See **[Run it with or without
> AsterVault](#run-it-with-or-without-astervault)** below.

---

## 🎬 Demo

> _**[▶ Watch the walkthrough]( )**_ &nbsp;·&nbsp; _(video link — TODO)_

A security engineer asks their agent: *"Review `sales-copilot` for AppSec — scan it, red-team the
risky paths, and recommend enforcement policies."* The agent runs the whole pipeline and ends with a
grounded report:

| | |
|---|---|
| **The agent session** | the orchestrator invoking each skill + MCP tool, visuals rendering inline — _(screenshot / artifact — TODO)_ |
| **The output report** | SCA · attack path · offensive red-team (per-test) · recommended policies — _(screenshot / artifact — TODO)_ |

Runnable walkthroughs live in [`examples/`](examples/) — start with
[`examples/scan-to-redteam/`](examples/scan-to-redteam/) (scan → graph → attacker ▸ defender ▸ judge →
policy, over the live gateway) and [`examples/live-demo/`](examples/live-demo/).

---

## 🧭 What the agent does — the review flow

One orchestrator skill (`security-engineer`) runs the pipeline for a target (repo, container, or live
agent). Each stage is its own composable skill:

```
  target
    │
 ①  recall ........ knowledge-recall ....... what do we already know about this app?
    │
 ②  scan .......... local-scan · sca-graph .. grype + checkov + trufflehog  →  SBOM/CVE graph
    │
 ③  model ......... data-flow · information-flow · weakness-graph · agent-profiling
    │                                          stores→tools→endpoints · IFC flows · WRG · agent authority
 ④  prioritize .... risk-context ............ feature vector (KEV/EPSS/reachability/data-class) → risk
    │
 ⑤  red team ...... attacker ▸ defender ▸ judge  (+ canary)   ← generated FROM the graph, not scripted
    │
 ⑥  remediate ..... remediation ............. least-privilege policy-as-code → PR → (enforce)
    │
 ⑦  capture ....... memory-capture .......... proven breaks promoted → next review starts ahead
    │
    ▼
  risk-report  →  HTML artifact (attack path · offensive findings · recommended policies)
```

## ⚔ The red-team contract — reusable everywhere

Red teaming isn't a monolith; it's three reusable skills with a typed contract, usable in red team,
evals, and continuous testing alike. **Tests are generated from the target** (the attack graph + the
pattern corpus + memory of past tries), then each runs the loop:

```
  context ──► attacker ──attack_turn──► defender ──target_response──► judge ──► verdict
     ▲           │  (canaries woven in: honeypots, egress URLs)                   │
     └──────── context += {attack_turn, target_response}  (adaptive, multi-turn)  │
                            canary egress / scan hits ───────────────────────────►┘  (hard evidence)
```

- **`attacker(context) → attack_turn`** — the user feeds a short engagement brief (target, objective,
  scope + authorization); the rest runs as-is. Canaries are embedded in the turns. The **attacker
  model is selectable** and recorded with every run (default = the harness model).
- **`defender(attack_turn) → target_response`** — the real system-under-test, with its real defenses,
  through the AsterVault proxy or a pluggable adapter. The defender never weakens the target; it *is* it.
- **`judge(turn, response, canary_evidence) → verdict`** — decides `broke | held | inconclusive` from
  **out-of-band evidence** (a canary on egress, not the model's self-report) + ASR@budget.

## 🔁 Self-improving by design

A review isn't a one-shot report — it feeds the next one. Every proven break is distilled, **approved
by a human**, and promoted into the shared knowledge, so the next review of the same app — *or a
sibling agent, in any harness* — starts ahead. Once the recommended policies merge, the same campaign
re-runs as a **regression test that must stay held**.

```
        Run agent / red-team campaign          ← attacker ▸ defender ▸ judge
                   │
                   ▼
        Scan + probe the target                ← local-scan · canary planting
                   │
                   ▼
        Evaluate what worked                   ← judge: which attacks broke it (ASR, canary-verified)
                   │
                   ▼
        Extract useful knowledge               ← memory-capture: the proven break + the *why*
                   │
                   ▼
        Review + approve                       ← memory.promote(approved)  ·  human-gated
                   │
                   ▼
        Reuse across future agents  ───────────► next review recalls it, starts ahead
                   ▲                                   (knowledge-recall, any harness)
                   └───────────────────────────────────────────────────────────────┘
```

---

## Capabilities (skills)

| Skill | Capability |
|---|---|
| `security-engineer` | Orchestrator — runs the pipeline for a target (repo, container, or live agent) |
| `knowledge-recall` | Pull the common knowledge + prior session memory for the app/area at task start |
| `memory-capture` | Write decisions/findings/fixes/waivers (with the why) back to shared memory at task end |
| `local-scan` | Run SCA/IaC/secrets/AI-BOM collectors locally; bootstrap any that are missing |
| `proxy-recon` | Record a live agent through the AsterVault broker/proxy (no code) → traffic corpus + audit trail |
| `sca-graph` | Build the SBOM dependency tree + CVE graph |
| `data-flow` | Build the data-flow architecture (stores/fields → functions/tools → endpoints) |
| `information-flow` | Build the IFC overlay — integrity/confidentiality flows, data classes, missing controls |
| `weakness-graph` | Build the weakness↔component graph (WRG) + weakness→control crosswalk |
| `agent-profiling` | Agent AI-BOM + authority boundaries from code or recorded traffic |
| `dast-generation` | Generate DAST tests from the graphs |
| `behavioral-redteam` | Orchestrator — composes attacker/defender/judge + canaries into an adaptive, self-improving episode (ASR@budget) |
| `attacker` | Reusable adversarial driver — `attacker(context) → attack_turn`; user-fed brief, canaries woven in, selectable attacker-model, recalls prior breaks |
| `defender` | Reusable system-under-test wrapper — `defender(attack_turn) → target_response` with its real defenses |
| `judge` | Reusable evaluator — `judge(turn, response, canary_evidence) → verdict` from out-of-band evidence; captures/promotes proven breaks |
| `canary-testing` | Plant canary tokens and detect them on any egress — hard, code-checkable proof of exfiltration / injection / scope violation |
| `security-judge` | Score test runs broke/held → findings (LLM-as-judge) + safety metrics |
| `risk-context` | Hand the agent the model's feature vector (KEV/EPSS/reachability/data-class/…) so it calculates & calibrates risk itself — not a black-box score |
| `remediation` | Generate least-privilege egress/identity policy-as-code (SPIFFE, IAM, egress, OPA/Cedar, DLP, AsterVault PDP, …) from findings |
| `risk-report` | Render `graph.enrich`/`risk.score` JSON into the attack-path visual (data-driven) as an HTML Artifact |

---

## Run it with or without AsterVault

The skills are **thin** on purpose: the *workflow* is local and open; the *proprietary knowledge,
governance and memory* are the one thing we run (the AsterVault MCP). So they run in two modes.

### Offline mode — skills only, nothing leaves the box
The harness's own model does all the reasoning. You get a real, useful review: a local scan, the
structural graphs, generated DAST + behavioral tests, the attacker ▸ defender ▸ judge loop (with the
harness or a selected attacker model), locally-planted canaries, policy-as-code, and the HTML report.
Nothing is sent anywhere. **This is the honest answer to "can I run without your server?" — yes.**

### Connected mode — skills + AsterVault MCP (default)
The same skills call MCP tools for the parts that need *grounding you can trust*: registry-backed
weakness IDs, the framework crosswalk, the calibrated ARS, the independent gateway-egress canary
verifier (proof, not self-report), the attack-pattern corpus, enforcement, and cross-session memory.
Only the client's *structural* findings (ids, `package==version`, graph shape) are sent for enrichment
— **never your raw code or traffic, and never our knowledge back to you.**

### What each skill does in each mode

| Skill | Offline (no MCP) | What AsterVault adds in connected mode |
|---|---|---|
| `local-scan`, `sca-graph` | ✅ full — local collectors | — (collectors run client-side either way) |
| `data-flow`, `information-flow`, `agent-profiling` | ✅ full — structural graphs built locally | — (the schema is format, not data) |
| `dast-generation` | ✅ test skeletons from the graph | richer tests from the `testgen.patterns` corpus |
| `attacker` | ◐ harness/selected model, no history | prior-break memory + attack-pattern corpus seed the strategy |
| `defender` | ✅ local adapter to the SUT | routed through the audited AsterVault proxy |
| `judge`, `canary-testing` | ◐ plant + **local** scan | **independent** gateway-egress proof + tamper-evident audit |
| `risk-context` | ◐ agent fills the feature vector itself | **calibrated** ARS + attack-surface enrichment (`graph.enrich`/`risk.score`) |
| `weakness-graph` | ◐ structural WRG only | registry-backed IDs/severity/OWASP/CWE + control crosswalk |
| `remediation` | ✅ generates the policy-as-code PR | `policy.apply` → the gateway **enforces** it |
| `risk-report` | ✅ renders the agent's own enrichment | renders grounded `graph.enrich`/`risk.score` JSON |
| `knowledge-recall`, `memory-capture` | ✗ no shared store | **the whole point** — common knowledge + cross-session self-improvement |

✅ runs the same · ◐ runs, with weaker grounding/proof/memory · ✗ needs the MCP

**Bottom line:** offline gives you the *method* and a complete local review; AsterVault gives you
*grounding you can defend to an auditor, an independent proof-of-breach, enforcement, and memory that
compounds across runs and harnesses.*

---

## 🔀 Cross-harness by design

One security review, every agent. The skill bodies are platform-agnostic, so the **same AppSec /
agent review** runs from whichever harness your engineers already use — and every run reads and writes
the **same shared project knowledge** (grounding + memory) through AsterVault. A break proven from
Cursor is recalled from Codex; a policy merged after a Claude Code review is enforced for all of them.

```
   Claude Code ─┐
   Cursor ──────┤
   Codex ───────┼──►  AsterGuard Skills  ──►  shared project knowledge
   OpenCode ────┤     AppSec / Agent review     (weakness registry · crosswalk ·
   Cline ───────┘     (scan → graph → red team     calibrated risk · attack-pattern
                       → remediate → report)         corpus · proven-break memory)
                              │                              ▲
                              └──────────────────────────────┘
                           every review reads + writes the same brain (via AsterVault MCP)
```

- **Same review, any harness** — scan, graph, attacker ▸ defender ▸ judge, remediate, report — identical.
- **Knowledge compounds across tools** — your Cursor red-team makes the next Codex review start ahead.
- **One source of truth** — findings, controls, and proven breaks live in one place, not per-harness silos.

## Install

### Claude Code (plugin)

```bash
/plugin marketplace add CoMatrixlabs/asterguard-skills
/plugin install asterguard-security@asterguard-marketplace
```

Installing ships **`.mcp.json`**, which auto-connects the skills to the AsterVault MCP gateway (point
it with `ASTERVAULT_MCP_URL`; see [docs/MCP_WIRING.md](docs/MCP_WIRING.md)). For **offline mode**, leave
`ASTERVAULT_MCP_URL` unset — the skills detect the missing gateway and run locally. Then just ask:
*"profile this agent and red-team it"*, or run the orchestrator skill.

### Codex (skill bundle)

The skill bodies are platform-agnostic. Build the Codex bundle from the same source:

```bash
scripts/build-codex.sh   # emits ./dist/codex/ (AGENTS.md + skills/) to drop into a Codex project
```

See [docs/MCP_WIRING.md](docs/MCP_WIRING.md) for the gateway wiring across harnesses, and the
`packages` block in `.claude-plugin/marketplace.json` for the companion collectors.

## The companion packages

The skills shell out to raw collectors only; `local-scan` **delivers** whichever are missing
(`grype`, `syft`, `checkov`, `trufflehog`) and launches the bundled `asterguard-proxy`. The
marketplace manifest lists them under `packages` so a client gets everything in one install.

## Architecture

```
Client agent harness (Claude Code / Codex)
  + asterguard-skills  ── thin: workflow METHOD + MCP tool calls, NO proprietary data
        │  MCP (OAuth 2.1 / audience-bound JWT, per the MCP Authorization spec)   ← omit in offline mode
        ▼
AsterVault MCP gateway (run by AsterGuard)
  ├─ existing: AuthN · guardrail · policy PDP/PEP · credential broker · tool proxy · append-only audit
  └─ security-analysis surface (the extension):
       registry.resolve · controls.map · graph.enrich · risk.score · testgen.patterns · scan.plan · canary.* · memory.*
     (the 578-weakness registry, the control crosswalk, and the scoring models live HERE)
```

Full detail: **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** · gateway wiring:
**[docs/MCP_WIRING.md](docs/MCP_WIRING.md)** · offensive use: **[docs/OFFENSIVE_SECURITY.md](docs/OFFENSIVE_SECURITY.md)**
· positioning: **[docs/POSITIONING.md](docs/POSITIONING.md)** · schema: **[docs/graph-schema.md](docs/graph-schema.md)**

## Structure

```
asterguard-skills/
├── .claude-plugin/marketplace.json   # Claude Code plugin + companion-package manifest
├── docs/graph-schema.md              # SSOT graph schema (all skills build to this)
├── skills/<capability>/SKILL.md      # one capability each (+ scripts/, references/)
├── examples/                         # worked walkthroughs (scan-to-redteam, live-demo, …)
└── scripts/build-codex.sh            # emit the Codex target from the same skill source
```
