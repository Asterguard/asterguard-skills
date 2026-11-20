# Extending AsterGuard

AsterGuard is built so you extend **data and configuration, not code**. The skills are plain Markdown
methods, playbooks compose them as data, and the engines read a profile that describes your target.
This guide lists every extension point — pick the layer that fits what you want to do.

> **The three layers** (from [`docs/RUNBOOK_GUIDELINES.md`](docs/RUNBOOK_GUIDELINES.md)): **atomic
> skills** (one gateway tool, one job) → **common skills** (reusable multi-step blocks) → **playbooks**
> (whole workflows). Extend at the layer that matches the change: a new atomic for a new tool, a new
> playbook to recompose what already exists.

---

## 1. Scan your own app — write a target profile

The highest-leverage customization. A **target profile** is a JSON that describes an app so the generic
engines (SCA / SAST / DAST / behavioral) can assess it — nothing is hardcoded. Copy the example and
point `TARGET_PROFILE` at yours; no code changes.

- Template: [`tools/live-harness/targets/support-agent-demo.json`](tools/live-harness/targets/support-agent-demo.json)
- Loader + fields: [`tools/live-harness/target_profile.py`](tools/live-harness/target_profile.py)

```jsonc
{
  "name": "my-agent",
  "tools": ["lookup", "export", "search"],          // for the AI-BOM
  "sensitive_paths": ["/admin", "/export"],         // DAST probes
  "requirements": "requirements.txt",               // what SCA scans
  "plant": { "kind": "sqlite", "table": "customers", // where a canary is planted so it's retrievable
             "column": "ssn", "row_id": "1" },
  "dataflow": { "nodes": [ /* source/agent/tool/sink */ ], "edges": [ /* with legs */ ] }
}
```

**Profile vs environment.** The profile is the app's *structure* (committable, portable); the
*environment* is where it runs — `TARGET_INVOKE_URL`, `TARGET_DB`, `TARGET_REPO`, `ASTERVAULT_MCP_URL`,
the bearer. See the env table in [`tools/live-harness/README.md`](tools/live-harness/README.md). With no
profile the engines use neutral generic defaults, so the library always runs.

## 2. Add or override a skill

A skill is a directory under [`skills/`](skills/) with a `SKILL.md`: YAML frontmatter (`name`,
`description`) plus the method in Markdown. No code runs — it's instructions your harness follows, so
skills are portable across harnesses.

```markdown
---
name: my-check
description: One sentence that triggers this skill and says what it does.
---
# My Check
## When to Activate
## Objective
## Inputs / Outputs
## Integration   <!-- which atomic/common skills + gateway tools it builds on -->
```

- Use the `skill-creator` skill for conventions and to measure triggering accuracy.
- **Override** an existing skill by copying its directory and editing — playbooks reference skills by
  name, so your version slots in without touching the playbook.
- Skills that need a tool may ship a `scripts/` helper (see
  [`skills/report-outcomes/scripts/aggregate_outcomes.py`](skills/report-outcomes/scripts/aggregate_outcomes.py)).

## 3. Compose a pipeline — write a playbook

Playbooks ([`playbooks/*.yaml`](playbooks/)) are the composition *as data*: an ordered list of skill
steps plus `rules`, `gate`, and `report`. Recompose the pipeline for your org without editing any skill.

```yaml
name: my-pipeline
posture: offensive
input: repo
steps:
  - { skill: recon }
  - { skill: attack-planner }
  - { skill: behavioral-redteam, with: { budget: "ASR@5" } }
  - { skill: report-outcomes }
rules: { authorized_only: true, offensive_token_required: true }
```

Model it on [`security-engineer-scan.yaml`](playbooks/security-engineer-scan.yaml) (one target) or
[`pentest-pr-gate.yaml`](playbooks/pentest-pr-gate.yaml) (diff-scoped gate).

## 4. Customize detection

- **SAST rules** — edit [`tools/live-harness/semgrep-rules.yaml`](tools/live-harness/semgrep-rules.yaml)
  (runs offline, no registry login). Connected, the gateway serves framework-profiled packs via
  `rules.fetch`; the engine runs them the same way.
- **DAST probes & canaries** — `sensitive_paths` and the canary types in the profile; the
  `testgen.patterns` corpus from the gateway enriches generation.
- **Weakness → control mapping** — the gateway's `controls.map`; the policy packs it serves drive
  `remediation`.

## 5. Swap the engines (pluggable, env/profile-driven)

In [`tools/live-harness/`](tools/live-harness/), each engine is replaceable without forking the whole:

| Swap | Where | How |
|---|---|---|
| How to invoke / plant / read egress | `adapter.py` | the profile's `plant` + `TARGET_*` env |
| Attacker model | `attacker.py` | `ATTACKER_API_BASE` / `ATTACKER_MODEL` (any OpenAI-compatible endpoint) |
| Defender | the target itself | `TARGET_INVOKE_URL` |
| Gateway | `gateway.py` | `ASTERVAULT_MCP_URL` + bearer |
| Engagement store | `store.py` | `ENGAGEMENT_DB` (SQLite path) |

## 6. Connected vs offline

Every skill runs **offline** against `./.asterguard/` files (one engineer, air-gapped). A team wires the
**AsterVault MCP gateway** (`.mcp.json` → `ASTERVAULT_MCP_URL` + bearer) as the shared brain: rule packs,
the audited canary judge (subscription tier), and the Postgres/Qdrant stores in
[`deploy/context-memory`](deploy/context-memory/). Remediation emits policy-as-code enforced at *your*
gateway PDP / egress guardrail.

## 7. Package and share

- **Plugin / marketplace** — [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json)
  packages skills so a team installs them with `/plugin install`. Add your org's plugins there.
- **Personas** — [`personas/`](personas/) frame which skills a role runs.
- **Examples** — add a worked example under [`examples/`](examples/) (see
  [`examples/SETUP.md`](examples/SETUP.md) and
  [`examples/live-offensive-scan`](examples/live-offensive-scan)).

---

## Conventions

- **Authorized engagements only.** Offensive skills record the RoE and refuse without it; the execute
  tier is gated on an `offensive:run` token. Keep those gates when you extend.
- **Proof, not assertion.** A finding is a surfaced canary (`canary.verify`, audited) — don't lower that
  bar in a custom skill or playbook.
- **No secrets in the repo.** Bearers, keys and env go in the environment or git-ignored files, never a
  committed file.
- **Artifacts under `./.asterguard/`.** Each stage writes its artifact there, referenced by path, so
  runs stay cacheable, resumable, and portable to the platform.
