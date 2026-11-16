# AsterGuard Security Skills

Agent-native application security for a **security engineer**. Instead of installing a library or
calling a hosted API, you add these skills to your agent harness (Claude Code or Codex) and the
agent **performs the scan locally and builds the security architecture itself** — the SCA graph,
data-flow, information-flow (IFC) and weakness graph — then generates DAST + behavioral red-team
tests, judges them, and emits a risk report. No AsterGuard server, no data leaving the box.

The intelligence lives in the skills (the *method*), not in a black box. The only binaries are raw
collectors (`grype`, `checkov`, `trufflehog`) and a small local proxy; the analysis is the agent
following each skill against one shared schema ([docs/graph-schema.md](docs/graph-schema.md)).

## Why this shape

- **Local & private** — code and traffic never leave the machine; the harness's own model does the reasoning.
- **No server, no key management** — "offline" means no AsterGuard SaaS; the harness model generates and judges.
- **SSOT-compatible** — graphs are built to the platform schema, so results push back to AsterGuard unchanged.
- **Composable** — each capability is its own skill; an orchestrator (`security-engineer`) runs the pipeline.

## Capabilities (skills)

| Skill | Capability |
|---|---|
| `security-engineer` | Orchestrator — runs the pipeline for a target (repo, container, or live agent) |
| `knowledge-recall` | Pull the common knowledge + prior session memory for the app/area at task start |
| `memory-capture` | Write decisions/findings/fixes/waivers (with the why) back to shared memory at task end |
| `local-scan` | Run SCA/IaC/secrets/AI-BOM collectors locally; bootstrap any that are missing |
| `proxy-recon` | Record a live agent through the local proxy (no code) → traffic corpus |
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

## Install

### Claude Code (plugin)

```bash
/plugin marketplace add CoMatrixlabs/asterguard-skills
/plugin install asterguard-security@asterguard-marketplace
```

Installing ships **`.mcp.json`**, which auto-connects the skills to the AsterVault MCP gateway (point
it with `ASTERVAULT_MCP_URL`; see [docs/MCP_WIRING.md](docs/MCP_WIRING.md)). Then just ask: *"profile
this agent and red-team it"*, or run the orchestrator skill.

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

## Structure

```
asterguard-skills/
├── .claude-plugin/marketplace.json   # Claude Code plugin + companion-package manifest
├── docs/graph-schema.md              # SSOT graph schema (all skills build to this)
├── skills/<capability>/SKILL.md      # one capability each (+ scripts/, references/)
├── examples/blackbox-agent-redteam/  # worked PRD + SKILLS-MAPPING (the composition demo)
└── scripts/build-codex.sh            # emit the Codex target from the same skill source
```
