# Playbook schema — a configurable security review as data

A **playbook** is a YAML file that composes the building-block skills + vendor packs into one named
review. Shipped playbooks live in `playbooks/`; a customer adds or forks reviews by dropping YAML in
`./.asterguard/playbooks/` (or an org dir) — no code changes. The `playbook-runner` skill executes any
playbook against this contract.

## Fields

```yaml
name: architecture-review          # required, unique
description: one line
posture: validate                  # validate (SecEng, advisory) | gate (dev, pass/fail)
input: graph                       # graph | design-doc | iac | repo | live-agent
scope:
  mode: full                       # full | diff
  paths: []                        # optional restriction
packs:
  axes: [framework, provider]      # which vendor packs to resolve …
  vendors: []                      # … optionally pinned; else detected from the profile
  auto: true                       # resolve from check-planner's profile (default true)
steps:                             # ordered; each is a `skill:` (capability) or a `lens:` (questions)
  - { skill: knowledge-recall }
  - { skill: engagement, with: { op: open } }
  - { skill: data-flow }
  - { skill: information-flow }
  - { skill: weakness-graph }
  - { lens: architecture }
rules:                             # which pack threat-rules to evaluate
  include: [architecture, authority, segmentation]   # rule categories / lenses
  exclude: []
  severity_min: medium             # info | low | medium | high | critical
  weakness_ids: []                 # optional explicit set
gate:                              # null for posture: validate; a dev gate sets thresholds
  baseline: knowledge-store        # knowledge-store | merge-base | none
  fail_on: [new_proven_break, new_ungated_sensitive_egress]
  risk_delta: { fail_at: 1.5, warn_at: 0.5 }
report:
  format: html                     # html | md
  sections: [summary, trust_boundaries, authority, data_exposure, recommendations]
```

`name`, `posture`, `input`, and `steps` are required; the rest default (`scope.mode: full`,
`packs.auto: true`, `rules: {}` = all applicable, `gate: null`, `report.format: html`).

## `input` → what the review reads

| input | source | typical lenses |
|---|---|---|
| `graph` | the built security graph | architecture, data-exposure, controls |
| `design-doc` | a design / threat-model / PRD (pre-code) | design |
| `iac` | IaC / k8s / cloud config | deployment |
| `repo` | source tree (full scan) | all |
| `live-agent` | recorded traffic | architecture, data-exposure, behavioral |

## `steps` vocabulary

- **`skill:`** — a capability skill run as a stage: `knowledge-recall`, `engagement`, `check-planner`,
  `local-scan`, `sca-graph`, `data-flow`, `information-flow`, `weakness-graph`, `agent-profiling`,
  `dast-generation`, `behavioral-redteam`, `security-judge`, `remediation`, `risk-report`,
  `memory-capture`, `compliance-auditor`. Optional `with:` passes stage args.
- **`lens:`** — a named review question-set the runner applies over the current artifacts (below). A lens
  reads; it does not scan.

## `lens` vocabulary (the review questions)

| lens | asks | reads | rule categories |
|---|---|---|---|
| `architecture` | trust boundaries, agent↔tool authority, segmentation, blast radius, cross-tenant reach | the graph | architecture, authority, segmentation, agent-control |
| `design` | STRIDE / attack-tree over the described system (pre-code) | design-doc + weakness registry | all (as a checklist) |
| `deployment` | egress allow-list, network policy, secrets mgmt, identity/least-privilege, exposure | iac + runtime packs | external-access, credential-access, risky-command |
| `data-exposure` | PII/PCI/PHI flows, egress sinks, missing DLP/gates | information-flow overlay | context-exfiltration, prompt-injection |
| `controls` | weakness→control coverage, missing controls | weakness-graph + crosswalk | — |
| `compliance` | evidence→controls readiness | compliance-auditor | — |

## `gate` (posture: gate only)

Same shape as `pr-gate`'s `references/gate-policy.md` — evaluated over the **delta**, not the backlog.
`posture: validate` ignores `gate` (advisory: it reports, never blocks).

## Resolution order (what the runner does)

1. Load the playbook (name → `playbooks/` then `./.asterguard/playbooks/`; later dir wins, so customers
   override a shipped playbook by name).
2. Resolve `input` + `scope`; `check-planner` builds the profile.
3. Resolve `packs` (`rules.fetch(profile)` connected, or local pack load offline).
4. Run `steps` in order; `lens:` steps apply their question-set + the matching pack threat-rules
   (via the engine) over the current artifacts.
5. Filter findings by `rules`; apply `gate` if `posture: gate`.
6. Emit the `report` sections; `engagement` checkpoints the run.
