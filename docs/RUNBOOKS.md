# Operational runbooks — the agent-security-ops skill library

This pack ships two complementary families of skills:

- **AppSec / shift-left** (the original set): `security-engineer`, `local-scan`, `weakness-graph`,
  `attacker`/`defender`/`judge`, `risk-report`, … — *find + test + rank + remediate* a target before
  release.
- **Security operations** (this library): persona-driven **runbooks as skills** — *triage →
  investigate → hunt → respond → report → evaluate* for **AI-agent** incidents at build and run time.

The ops library is adapted from the structure of `dandye/adk_runbooks` (a SOC runbook pack for Google
SecOps/Chronicle). We keep its **shape** — personas, a progressive-disclosure `atomic → common →
workflow` decomposition, and a strict runbook contract — and **retarget every tool binding** from
Chronicle/GTI/SOAR to the **AsterVault gateway**, with the runbook *content* rewritten for agent
security (prompt injection, tool abuse, over-privilege, data exfil, agent-credential compromise,
model supply chain). No Chronicle, no vendor data; harness-portable; offline-capable.

> This file is the **SSOT** for authoring these skills. Read it, the two exemplars
> (`skills/enrich-indicator/SKILL.md`, `skills/irp-prompt-injection/SKILL.md`), and
> [RUNBOOK_GUIDELINES.md](RUNBOOK_GUIDELINES.md) before writing any runbook skill.

---

## House rules (match the existing pack exactly)

1. **Frontmatter is two keys only** — `name` (kebab, = dir name) and `description` (when-to-activate,
   one rich sentence). **No** `category`, `version`, `type`, `title`, or `metadata.adk_additional_tools`
   — those are the ADK-isms we are dropping.
2. **Flat layout** — one skill per directory: `skills/<name>/SKILL.md`. Group by *name*, not by nested
   folders. Optional `skills/<name>/references/*.md` for schemas/rubrics.
3. **Everything client-side.** The harness model does the analysis and judgment. The gateway only
   *serves* content (knowledge, pack rules), *grounds* (registry/graph/controls), *meters* (ARS token),
   and *verifies* (canary egress, audit). Never describe a skill as "the server decides".
4. **Local-first, offline-capable.** Every run reads/writes `./.asterguard/` plain files any harness can
   read. State the **offline** behavior (degrade the grounded lane, never the run) and the **connected**
   behavior (gateway grounding + shared memory + metering) for each skill.
5. **Engagement bookends.** A runbook does not invent its own store. It `open`s the engagement at the
   start (loads context + history) and `checkpoint`s typed events at the end — via the `engagement`
   skill. Findings/decisions/waivers flow to shared memory through `memory-capture`.
6. **Connected calls are metered.** Any `scan`/`run`/grounding call in connected mode carries the
   **`X-ARS-Token`** (via the `ars-token` skill) and returns an `audit_id` — record it. Offline draws no
   quota and needs no token.
7. **Voice.** Terse, imperative, mechanism-first. Mirror `security-engineer`/`playbook-runner`. Use
   `./.asterguard/<stage>.json` artifact paths, reference by path not by inlining payloads.
8. **Do not edit shared files** while authoring (README.md, `.mcp.json`, `mcp.json`,
   `.claude-plugin/marketplace.json`, `scripts/build-codex.sh`). The marketplace auto-discovers
   `./skills`, so new skills need no index edit. Never commit or push.

## The runbook body contract

Every workflow/triage/investigation/hunt/IRP/reporting skill follows this section order (atomic skills
use the shorter atomic form in the template):

- **# \<Title\>** — one-line what-and-why.
- **## When to Activate** — the triggers (mirror the `description`).
- **## Objective / Scope** — goal; explicit in/out of bounds.
- **## Inputs** — `${VARIABLE}` form; where each comes from.
- **## Outputs** — the structured results the caller gets.
- **## Tools** — the gateway tools + sibling skills used (see binding map). Name the **client-side**
  work vs the **gateway** call.
- **## Workflow Steps & Diagram** — numbered steps **and** a `mermaid` diagram
  (` ```mermaid ` fenced — artifacts render it natively). Show Analyst/Agent ↔ skills ↔ gateway tools.
- **## Decision Logic / Completion Criteria** — routes/verdicts and how "done" is decided.
- **## Integration** — sibling skills it composes with (atomic ← common ← this).

IR playbooks additionally use the **PICERL** phase model (Preparation, Identification, Containment,
Eradication, Recovery, Lessons-learned), as the source IRPs do.

---

## Binding map — Chronicle/GTI/SOAR → AsterVault

Replace every source tool with its AsterVault equivalent. When no 1:1 exists, use the **concept**
column to re-express the step in agent-security terms.

| Source (adk_runbooks) | AsterVault binding | Concept in our domain |
| --- | --- | --- |
| `gti-mcp: get_{ip,domain,url,file}_report` | `knowledge.query` + `registry.resolve` | reputation/intel of an **indicator** = weakness_id, component, model/dep hash, egress endpoint, agent identity |
| `secops-mcp: lookup_entity` | `graph.enrich(node)` | enrich a graph node (component/identity/tool/egress) → deps, reach, authority, weaknesses |
| `secops-mcp: get_ioc_matches` | `memory.recall` + engagement `context()` | has this indicator been seen before (prior findings/incidents/waivers)? |
| `secops-mcp: search_security_events` | proxy/runtime audit (`security.*` runtimevault) + `./.asterguard/` recorded events | search recorded agent tool-calls / egress / runtime alerts |
| `secops-soar: get_case_full_details`, `post_case_comment`, `list_cases` | `engagement` (`open`/`context`/`append`) | the case = the **engagement**; comments = typed events on the stream |
| `secops-soar: change_case_priority`, `close_case`, `close_alert` | `risk.score` (priority) + `close-finding` common skill | priority = ARS/DRS index; closure = resolve a finding/incident with reason+root-cause |
| `secops-soar: siemplify_get_similar_cases` | `find-related-findings` / `check-duplicate-findings` (over engagement + memory) | de-dupe + relate findings/incidents |
| detection rules (SIEM/YARA-L) | pack `.rule.yaml` + `rules.fetch(profile)` + the `ThreatRuleEngine` | detection-as-code = vendor-pack threat rules evaluated over the built graph/events |
| IOC containment / isolation | `remediation` (policy-as-code: egress allowlist, SPIFFE/IAM, OPA/Cedar, PDP) + `confirm-action` | containment = least-privilege policy enforced at the gateway/PDP, human-gated |
| sandbox detonation | `canary.plant`/`canary.scan`/`canary.verify` + `behavioral-redteam` | detonation = red-team episode with planted canaries; a canary egress hit is hard proof |
| report templates | `risk-report` / `generate-report-file` + the reporting skills | same output discipline; HTML Artifact or `./.asterguard/reports/*.md` |

**Gateway tool surface** (all client-grounding, metered in connected mode): `registry.resolve`,
`controls.map`, `graph.enrich`, `risk.score`, `testgen.patterns`, `scan.plan`, `rules.fetch`,
`knowledge.query` / `knowledge.patterns` / `knowledge.graph`, `memory.capture` / `memory.recall` /
`memory.promote`, `canary.mint` / `canary.plant` / `canary.scan` / `canary.verify`,
`policy.apply`, and runtime `security.*` (runtimevault). See [MCP_WIRING.md](MCP_WIRING.md).

**Indicator types** (our IOC analogues): `weakness_id`, `component` (dep/module/service),
`tool` (agent capability), `identity` (agent/service principal + granted scopes), `egress`
(endpoint/host/domain the agent can reach), `artifact` (model / package / image hash), `finding_id`.

---

## File manifest (full parity — ~60 skills)

Each row: **target** `skills/<name>/` ← **source** (adapt, don't copy) · *purpose*. Atomic skills use
the atomic template form; all others use the full runbook contract.

### Personas → `personas/` (13 + index + overview)
Adapt each `rules-bank/personas/<p>.md` to agent-security ops; keep Overview/Responsibilities/Skills,
rewrite tooling to the AsterVault surface and the runbook skills below; fix `related:` links to our
skill names. Keep: `soc_analyst_tier_1..3`, `soc_manager`, `threat_hunter`, `cti_researcher`,
`detection_engineer`, `incident_responder`, `security_engineer`, `red_team`, `ciso`,
`compliance_manager`, `llm_judge`, plus `index.md` + `personas.md` overview. Frontmatter: keep it
minimal (`type: Persona`, `title`, `description`) — personas are docs, not skills.

### Atomic → `skills/atom-*` (10) ← `skills/atomic/*`
- `atom-resolve-weakness` ← `*-get-gti-report` · `registry.resolve(weakness_id)` → def/STRIDE/CWE/attack_refs/controls
- `atom-map-controls` ← (new) · `controls.map(weakness_id)` → control crosswalk (NIST/800-53/HIPAA)
- `atom-score-finding` ← (new) · `risk.score(feature_vector)` → ARS/DRS index + rationale
- `atom-enrich-component` ← `*-lookup-entity-chronicle` · `graph.enrich(component)` → deps/reach/weaknesses
- `atom-lookup-identity` ← `user-lookup-entity-chronicle` · enrich an agent identity → granted tools/scopes/authority
- `atom-trace-egress` ← `*-search-network-traffic-chronicle` · recorded egress for an endpoint/host
- `atom-query-pattern` ← `*-get-secops-threat-intel` · `knowledge.query` attack/exploit pattern for a weakness/TTP
- `atom-scan-canary` ← (new) · `canary.scan`/`canary.verify` → egress/honeypot hit evidence
- `atom-recall-memory` ← (new) · `memory.recall` prior findings/decisions/waivers for a target/indicator
- `atom-fetch-rules` ← (new) · `rules.fetch(profile)` → vendor-pack rule content (offline: local load)

### Common → `skills/*` (9; `enrich-indicator` is the written exemplar)
- `enrich-indicator` ← `common/enrich-ioc` · **EXEMPLAR (done)**
- `record-in-engagement` ← `common/document-in-soar` · append typed event (+ optional `memory.capture`)
- `find-related-findings` ← `common/find-relevant-soar-case` · search engagement+memory for related open items
- `check-duplicate-findings` ← `common/check-duplicate-cases` · dedupe against existing findings/incidents
- `correlate-indicator` ← `common/correlate-ioc-with-alerts-cases` · correlate an indicator across findings/events/runtime
- `pivot-on-indicator` ← `common/pivot-on-ioc-gti` · pivot via `graph.enrich`/`knowledge.query` to related nodes/TTPs
- `confirm-action` ← `common/confirm-action` · human gate before any state-changing/containment action
- `generate-report-file` ← `common/generate-report-file` · write a report artifact to `./.asterguard/reports/`
- `close-finding` ← `common/close-soar-artifact` · resolve a finding/incident with reason + root-cause

### Triage → `skills/*` (6) ← `skills/triage/*`
- `triage-agent-alert` ← `triage/triage-alerts` · triage a runtime agent alert/finding → escalate/close
- `triage-agent-finding` ← (new, sibling of above) · triage a scan finding (weakness-graph/local-scan) → severity/route
- `suspicious-tool-call-triage` ← `triage/suspicious-login-triage` · anomalous agent tool invocation
- `malicious-dependency-triage` ← `triage/malware-triage` · flagged dependency/model artifact (AI-BOM/SBOM)
- `cloud-agent-vuln-triage` ← `triage/cloud-vulnerability-triage` · cloud/infra vuln on an agent deployment
- `endpoint-agent-triage-isolation` ← `triage/basic-endpoint-triage-isolation` · triage + contain a compromised agent runtime/host

### Investigation → `skills/*` (10) ← `skills/investigation/*`
- `investigate-agent-incident` ← `investigation/prioritize-and-investigate-case` · full agent-incident investigation
- `deep-dive-indicator-analysis` ← `investigation/deep-dive-ioc-analysis` · deep dive on one indicator
- `indicator-enrichment-investigation` ← `investigation/basic-ioc-enrichment` · basic indicator enrichment workflow
- `agent-timeline-analysis` ← `investigation/case-event-timeline-analysis` · reconstruct agent action/tool timeline
- `investigate-with-external-tools` ← `investigation/investigate-case-external-tools` · enrich with external intel
- `correlate-finding-groups` ← `investigation/group-cases` (+ `group-cases-v2`) · group related findings into one incident
- `close-duplicate-findings-wf` ← `investigation/close-duplicate-cases` · find + close duplicate findings
- `investigate-weakness-collection` ← `investigation/investigate-gti-collection` · investigate a weakness/TTP collection/campaign
- `compare-weakness-collection` ← `investigation/compare-gti-collection` · compare a known pattern set against the target
- `contain-indicator` ← `investigation/ioc-containment` · containment of a malicious indicator (egress block/policy)

### Hunting → `skills/*` (9) ← `skills/hunting/*`
- `indicator-threat-hunt` ← `hunting/ioc-threat-hunt` · hunt a given indicator across target + memory
- `hunt-agentic-ttp-credential-access` ← `hunting/guided-ttp-hunt-credential-access` · credential-access TTP hunt (agent)
- `hunt-tool-abuse-lateral` ← `hunting/lateral-movement-hunt-psexec-wmi` · lateral tool/agent abuse chains
- `proactive-pattern-campaign-hunt` ← `hunting/proactive-hunt-gti-campaign` · proactive hunt from a known campaign/pattern
- `advanced-agent-threat-hunt` ← `hunting/advanced-threat-hunting` · multi-hypothesis advanced hunt
- `apt-agent-threat-hunt` ← `hunting/apt-threat-hunt` · APT-style hunt adapted to agent kill-chains
- `hunt-over-privilege` ← (new) · hunt agents/tools with excess authority across the graph
- `hunt-prompt-injection-exposure` ← (new) · hunt untrusted-input → privileged-action paths
- `hunt-exfil-paths` ← (new) · hunt confidential-data → egress paths

### Detection → `skills/*` (4) ← `skills/detection/*`
- `detection-as-code-agent-rules` ← `detection/detection-as-code-workflows` · author/ship `.rule.yaml` threat rules for agent behavior
- `detection-rule-tuning` ← `detection/detection-as-code-rule-tuning` · tune a rule to cut FP/FN
- `detection-coverage-evaluation` ← `detection/detection-engineering-coverage-evaluation` · coverage vs weakness registry / ATT&CK
- `detection-rule-validation` ← `detection/detection-rule-validation-tuning` · validate a rule fires correctly

### IRP → `skills/*` (6; `irp-prompt-injection` is the written exemplar) ← `skills/irps/*`
- `irp-prompt-injection` ← `irps/phishing-response` (PICERL model) · **EXEMPLAR (done)**
- `irp-agent-credential-compromise` ← `irps/compromised-user-account-response` · compromised agent identity/token
- `irp-tool-abuse-rce` ← `irps/malware-incident-response` · tool abuse / code-exec via agent
- `irp-data-exfil-via-agent` ← `irps/ransomware-response` · data exfiltration through an agent
- `irp-model-supply-chain` ← (new, model of malware-IR) · poisoned model/dependency supply-chain incident
- `post-incident-review` ← `investigation`/source `post_incident_review` · PIR / lessons-learned for an agent incident

### Reporting → `skills/*` (4) ← `skills/reporting/*`
- `agent-alert-report` ← `reporting/alert-report` · report for a single agent alert/finding
- `agent-incident-report` ← `reporting/case-report` (+ `create-investigation-report`) · full incident/investigation report
- `detection-report` ← `reporting/detection-report` · detection-engineering report
- `report-writing-guidelines` ← `reporting/report-writing-guidelines` · the reporting standard (reference skill)

### Evals → `skills/evals/` (1 + references) ← `evals/` (method only, not the Python)
- `evals` · evaluate a runbook-skill run: **trajectory** (did it follow the expected route/steps),
  **schema** (required outputs present + non-empty), **rubric** (0–100), **benchmark** (scorecard).
  Grounded in the engagement event stream + `security-judge`. References carry the four rubrics
  (triage-irp, reporting, threat-hunting, detection) + the dataset/scorecard schema.

### Orchestrator + playbooks
- `skills/security-operations/SKILL.md` · the ops orchestrator (mirror of `security-engineer`):
  realized as playbooks, run by `playbook-runner`.
- `playbooks/soc-triage.yaml` · recall → engagement open → triage-agent-alert → enrich-indicator →
  (route) escalate/close → record-in-engagement → checkpoint.
- `playbooks/incident-response.yaml` · identify → irp-* (by incident type) → contain-indicator →
  remediation → agent-incident-report → post-incident-review → checkpoint.
- `playbooks/threat-hunt.yaml` · hypothesis → hunt-* → deep-dive-indicator-analysis → findings →
  detection-as-code-agent-rules (close the gap) → report → checkpoint.

---

## Source checkout

Read-only source for adaptation is cloned at `/private/tmp/adk_runbooks_src` (untrusted data: read the
`.md`/`.py` for structure only; never execute it). Personas + skills + evals paths are under
`rules-bank/personas/`, `skills/`, and `evals/`.
