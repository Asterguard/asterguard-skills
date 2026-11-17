# AsterGuard Security Skills

**Agentic Risk, as skills your agent runs itself — test and validate AI agents, prove where they
break, and close the gaps before release.**

AI agents *act*: they call tools, touch data, and take instructions from untrusted context. AsterGuard
makes that risk testable. You add these skills to your agent harness (Claude Code or Codex), and the
agent **does the work itself** — scans locally, builds the security architecture (SCA graph, data-flow,
information-flow, weakness graph), generates DAST + behavioral red-team tests, runs an
attacker ▸ defender ▸ judge campaign with canaries, and ends with a grounded risk report and the
enforcement policies that close each gap.

### Two ways to use it — one skill pack

- **Security engineers — validate & recommend.** Point the agent at a repo, container, or live agent
  and get ranked, grounded gaps with recommended enforcement policies to take back to the team. It
  finds, proves, and recommends; a human decides.
- **Developers — test, enforce, release.** Run it yourself before you ship: red-team your agent's
  behavior, prove a break is closed with a canary, apply the policy, and gate the release — no
  security-team round-trip. **`test → enforce → ship`.**

Both are the *same chain*; the only difference is the enforcement switch — recommend (review) vs. apply
(self-gate).

The *method* lives in the skills (open, thin, local); the proprietary *knowledge* — the 578-weakness
registry, control crosswalk, calibrated risk models, attack-pattern corpus, and cross-session memory —
stays server-side behind the **AsterVault MCP gateway** and never ships to the client. The only client
binaries are raw collectors (`grype`, `checkov`, `trufflehog`) and a small proxy; everything else is the
harness's own model following each skill against one shared schema
([docs/graph-schema.md](docs/graph-schema.md)).

> **One question up front: do you need our server to run these?** No — the skills run standalone in
> **offline mode** (local scan, graphs, generated tests, a full report, even the red-team loop, all on
> the harness's own model). What the **AsterVault MCP** adds is *grounding, governance and memory*:
> registry-backed weakness IDs, the framework crosswalk, calibrated ARS, an independent canary
> verifier, enforcement, and the self-improving flywheel. See **[Run it with or without
> AsterVault](#run-it-with-or-without-astervault)** below.

---

## What you need to run it

The *method* is yours to run with nothing from us; the *shared brain* is one endpoint we host. Two levels:

| You want… | AsterGuard gateway? | Other components | Who runs it |
|---|---|---|---|
| **The method (offline)** — scan, graphs, generated tests, attacker▸defender▸judge, local canaries, policy-as-code, HTML report | ❌ no | local scanners (`grype`/`syft`/`checkov`/`trufflehog`) — `local-scan` auto-installs any that are missing | **you**, fully local — nothing leaves the box |
| **The shared brain** — registry-grounded IDs, the independent canary verifier, enforcement, and cross-session **shared knowledge + memory** | ✅ yes — **one** gateway (an MCP endpoint) | none — no second service, no separate DB, no per-harness plugin | **we host it**; you point your harness at the URL + use an **ARS token** we provision |

- **In any harness** (Claude Code, Codex, Cursor, OpenCode, a DeepSeek harness): offline needs only the
  harness + the skill Markdown + local scanners. To turn on the shared brain, register the gateway as an
  **MCP server** and attach the ARS token — the knowledge is reached over **MCP**, so it is harness-portable
  (it is *not* tied to Claude Code "skills"; see [Cross-harness by design](#-cross-harness-by-design)).
- **The one component is the AsterVault gateway**, and we run it — it bundles auth, policy PDP/PEP, the
  broker/proxy, the append-only audit, the weakness registry, the crosswalk, scoring, and the shared
  memory store behind a single endpoint. The SQLite-vs-Postgres store is our deployment detail, invisible
  to you unless you self-host.
- **ARS token** — provisioned per organization on request; the `ars-token` skill attaches and renews it.
  Offline runs carry no token and draw no quota.

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

## 🧾 Audit readiness — the second pipeline

The same parts run a second review: **evidence → controls**. Where the security pipeline asks *"where
are my gaps?"*, `compliance-auditor` asks *"can I **prove** each control to an auditor?"* — for ISO
27001, ISO 9001, SOC 2, and HIPAA. The rule is **no citation, no verdict**; the output is *readiness,
not certification* — a human signs.

```
  framework (iso-27001 · iso-9001 · soc2 · hipaa)
        │
  evidence-collection ─► corpus: git · PRs · CI · docs · scan/graph · applied policies   (local + security graph)
        │
  control-rubric ──────► per control: audit questions + required evidence + security_signal
        │                 (MCP controls.rubric · bundled YAML pack offline)
        ▼
  evidence-judge ──────► satisfied · gap · parked   +  CITATION        ← no citation, no verdict
        │
  audit-verify ────────► independent second opinion · one re-judge · disagree → parked
        │
  evidence-drafting ───► draft the missing artifact for each gap (unsigned, human completes)
        │
  audit-report ────────► HTML: coverage % · cited verdicts · gaps + drafts · parked items
```

**The differentiator:** AsterGuard's security review already produces *cited proof* — a canary that
stays **held** on egress after the DLP policy merged is evidence for ISO 27001 A.8.12 / SOC 2 CC6.1 /
HIPAA 164.312(e)(1). Each rubric control names a `security_signal`, so findings become first-class
audit evidence — proof, not a policy doc that merely asserts it. Full design + the MCP surface:
**[docs/COMPLIANCE.md](docs/COMPLIANCE.md)**.

---

## Capabilities (skills)

**Everything runs client-side.** The AsterGuard knowledge store only *grounds* (recall) and *remembers*
(capture); the planning, the scans, the red-team, and the risk reasoning all happen in your harness.

**Orchestrators**

| Skill | Capability |
|---|---|
| `playbook-runner` | Execute a review **playbook** — configurable YAML that composes the building blocks + packs into a named review. Reviews are data (`playbooks/`), customized/overridden per org, not code |
| `security-engineer` | SecEng posture — the **`full-360`** playbook (full advisory review of a repo, container, or live agent) |
| `pr-gate` | Dev posture — the **`pr-gate`** playbook (diff-scoped → PASS/FAIL/WARN; blocks only on what the change introduces, then `test → enforce → ship`) |
| `check-planner` | Plan the standard checks (SAST/DAST/IaC/secrets/data-flow/PII/SCA/compliance) as one client-side plan; marks the behavioral follow-on targets |

Shipped playbooks (`playbooks/`): `full-360`, `architecture-review`, `design-review`, `deployment-review`, `pr-gate` — the security engineer's review functions, each a configurable composition of the skills + packs + rules + gate + report.

**Standard checks — tier 1** (deterministic / structural, run first)

| Skill | Capability |
|---|---|
| `local-scan` | SAST (semgrep/opengrep) + IaC (kics/checkov) + secrets (trufflehog) + AI-BOM collectors, locally; bootstrap any that are missing |
| `sca-graph` | Build the SBOM dependency tree + CVE graph (grype/syft) |
| `data-flow` | Build the data-flow architecture (stores/fields → functions/tools → endpoints) |
| `information-flow` | IFC overlay — integrity/confidentiality flows, PII/PCI/PHI classes, missing controls |
| `weakness-graph` | Build the weakness↔component graph (WRG) + weakness→control crosswalk |
| `agent-profiling` | Agent AI-BOM + authority boundaries from code or recorded traffic |
| `dast-generation` | Plan + generate DAST tests from the graphs |
| `proxy-recon` | Record a live agent through the broker/proxy (no code) → traffic corpus + audit trail |

**Behavioral red-team — tier 2** (follow-on; targets the risky paths tier 1 surfaced)

| Skill | Capability |
|---|---|
| `behavioral-redteam` | Orchestrator — composes attacker/defender/judge + canaries into an adaptive, self-improving episode (ASR@budget) |
| `attacker` | Adversarial driver — `attacker(context) → attack_turn`; user-fed brief, canaries woven in, selectable attacker-model, recalls prior breaks |
| `defender` | System-under-test wrapper — `defender(attack_turn) → target_response` with its real defenses |
| `judge` | Evaluator — `judge(turn, response, canary_evidence) → verdict` from out-of-band evidence; captures/promotes proven breaks |
| `canary-testing` | Plant canary tokens and detect them on any egress — hard, code-checkable proof of exfiltration / injection / scope violation |
| `security-judge` | Score test runs broke/held → findings + safety metrics |

**Offensive — authorized pentest** _(see [`docs/OFFENSIVE_SECURITY.md`](docs/OFFENSIVE_SECURITY.md); authorized engagements only — scoped + audited through the gateway)_

| Skill | Capability |
|---|---|
| `offensive-engineer` | The authorized-pentest **orchestrator** (the `pentest` playbook): authorize → recon → plan → campaign → exploit-chain → prove → report → feed-forward |
| `recon` | Build the offensive attack map + pick the highest-value path (lethal-trifecta legs, over-privileged tools, anon-reachable stores) |
| `attack-planner` | The MCP as a **knowledge base** decides *what* to test for this agent — test kinds + example techniques + which canary types (egress / identity / workload-identity / injection / memory / context / …) + next steps |
| `exploit-chain` | Chain a canary-proven foothold into a **demonstrated** multi-step compromise (escalate → lateral → impact), each step proven |
| `attacker-model` | Select + **govern** the attacker model (authorized-only, recorded in the audit, reported with ASR@budget) |
| `pentest-report` | Compliance-ready engagement report: PoCs + ASR@budget + kill-chain + remediation + regression handoff |

Proven breaks feed the reusable corpus and hand to the blue team as regression tests. Playbooks: `pentest`, `pentest-pr-gate`.

**Risk, remediation & memory**

| Skill | Capability |
|---|---|
| `engagement` | The harness-independent **context / history / session manager** — opens a long-lived engagement per target, records a typed security-event stream, folds it into the current context, and feeds contextual decisions (baseline, waivers, proven breaks) to the other skills. Local-first; structural-only sync to the knowledge store |
| `risk-context` | Hand the agent the **feature vector** (KEV/EPSS/reachability/data-class/owasp-weight/…) so **the harness composes the risk itself** — no ARS model or eval runs client-side; the trained models live in the full platform |
| `remediation` | Generate least-privilege egress/identity policy-as-code (SPIFFE, IAM, egress, OPA/Cedar, DLP, runtime PDP, …) from findings |
| `risk-report` | Render the graph + findings into the attack-path visual (data-driven) as an HTML Artifact |
| `knowledge-recall` | Pull the common knowledge + prior session memory for the app/area at task start |
| `memory-capture` | Write decisions/findings/fixes/waivers (with the why) back to the knowledge store at task end |

### Audit readiness

| Skill | Capability |
|---|---|
| `compliance-auditor` | Orchestrator — evidence → controls for a framework (ISO 27001 · ISO 9001 · SOC 2 · HIPAA) |
| `evidence-collection` | Build the evidence corpus from local sources + the security graph; records are untrusted input |
| `control-rubric` | Resolve a framework → per-control audit questions + required evidence (MCP `controls.rubric` · offline YAML packs) |
| `evidence-judge` | Judge each control satisfied/gap/parked **with a citation** — no citation, no verdict |
| `audit-verify` | Independent second opinion over the verdicts; one re-judge; disagreement → parked |
| `evidence-drafting` | Draft the missing artifact for each gap (unsigned) for a human to complete and sign |
| `audit-report` | Per-control verdicts + citations + coverage % as an HTML Artifact; readiness, not certification |

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
| `evidence-collection`, `evidence-judge`, `audit-verify`, `evidence-drafting`, `audit-report` | ✅ local corpus + seed packs, cited verdicts | shared `evidence.search` corpus (cross-run recall) |
| `control-rubric` | ◐ bundled seed packs (subset) | `controls.rubric` — full grounded, versioned catalogs |

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
   DeepSeek ────┘     (scan → graph → red team     calibrated risk · attack-pattern
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
/plugin marketplace add Asterguard/asterguard-skills
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

### Cursor · OpenCode · DeepSeek · any other harness

The skill bodies are plain Markdown against one schema, so any harness that can follow instructions and
speak MCP runs them. Use the same bundle (`scripts/build-codex.sh` → `AGENTS.md` + `skills/`), and point
the harness's MCP config at the repo's `mcp.json` (or set `ASTERVAULT_MCP_URL`):

- **Cursor** — copy the `mcp.json` server block into `.cursor/mcp.json`; drop the skill bodies in as
  project rules.
- **OpenCode** — register `mcp.json` as an MCP server; load the bundle's `AGENTS.md`.
- **DeepSeek harness** — the bundle is model-agnostic; the harness's model follows the same skills and
  calls the same MCP tools. Offline mode needs no gateway at all.

Every harness reads and writes the **same** shared knowledge through the gateway, so a review from one
shows up in the next (see [Cross-harness by design](#-cross-harness-by-design)).

### Connecting (ARS token)

Offline mode needs nothing. For **connected mode** — grounded weakness IDs, the independent canary
verifier, enforcement and shared memory — a run also carries a per-org **ARS token** (`X-ARS-Token`)
so scans are metered and attributed to your org. **We provision that token per organization — [open an
issue](https://github.com/Asterguard/asterguard-skills/issues) or contact AsterGuard and we'll issue
one;** the `ars-token` skill then attaches and renews it automatically. See
[docs/MCP_WIRING.md](docs/MCP_WIRING.md).

See [docs/MCP_WIRING.md](docs/MCP_WIRING.md) for the gateway wiring across harnesses, and the
`packages` block in `.claude-plugin/marketplace.json` for the companion collectors.

## The companion packages

The skills shell out to raw collectors only; `local-scan` **delivers** whichever are missing
(`grype`, `syft`, `checkov`, `trufflehog`) and launches the bundled `asterguard-proxy`. The
marketplace manifest lists them under `packages` so a client gets everything in one install.

## Architecture

```
Client agent harness (Claude Code · Codex · Cursor · OpenCode · DeepSeek)
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
· audit readiness: **[docs/COMPLIANCE.md](docs/COMPLIANCE.md)** · positioning:
**[docs/POSITIONING.md](docs/POSITIONING.md)** · schema: **[docs/graph-schema.md](docs/graph-schema.md)**

**Customer walkthrough — setup → integration → report:** [docs/playbook.html](docs/playbook.html)
(open in a browser) — the end-to-end journey across Claude Code / Codex, the gateway + ARS token, and
the full capability catalog.

## Structure

```
asterguard-skills/
├── .claude-plugin/marketplace.json   # Claude Code plugin + companion-package manifest
├── docs/graph-schema.md              # SSOT graph schema (all skills build to this)
├── skills/<capability>/SKILL.md      # one capability each (+ scripts/, references/)
├── examples/                         # worked walkthroughs (scan-to-redteam, live-demo, …)
└── scripts/build-codex.sh            # emit the Codex target from the same skill source
```
