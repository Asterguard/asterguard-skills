# Audit readiness — compliance skills + the MCP server surface

A second pipeline alongside the security review, built from the same parts. Where `security-engineer`
runs **findings → controls** ("where are my security gaps?"), `compliance-auditor` runs **evidence →
controls** ("can I *prove* each control to an auditor?"). Same thin-client / server-knowledge split,
same two run modes, same memory.

```
  framework choice (iso-27001 | iso-9001 | soc2 | hipaa)
        │
  evidence-collection ──► corpus (git · PRs · CI · docs · scan/graph · applied policies)   [local + security graph]
        │
  control-rubric ───────► per-control: audit questions + required evidence + security_signal
        │                  (MCP controls.rubric when connected · bundled YAML pack offline)
        ▼
  evidence-judge ───────► per control: satisfied | gap | parked  + CITATION   (no citation, no verdict)
        │
  audit-verify ─────────► independent second opinion · one re-judge · disagreement → parked
        │
  evidence-drafting ────► draft the missing artifact for each gap (unsigned, human completes)
        │
  audit-report ─────────► HTML artifact: coverage %, cited verdicts, gaps + drafts, parked items
        │                  "readiness, not certification — a human signs"
        ▼
  memory-capture ───────► verdicts + accepted evidence + waivers (the why) → next cycle starts ahead
```

## The differentiator — the security review *is* evidence

AsterGuard already produces grounded, cited security artifacts: canary-verified breaks, applied egress/
identity policies, SCA/IaC scan results, and `controls.map` linkages. Each rubric control can name a
`security_signal` (weakness ids + an observable "satisfied_when"), so a control like ISO 27001 **A.8.12
/ SOC 2 CC6.1 / HIPAA 164.312(e)(1)** (data-leakage / transmission security) is answered by *proof* — an
exfil canary that stays **held** on egress after the DLP policy merged — not by a policy document that
merely asserts it. That is what makes the report audit-ready rather than an LLM opinion.

## Run modes (same as the rest of the pack)

- **Offline:** bundled seed YAML packs + local retrieval; the harness model judges and verifies.
  Produces a real readiness report with citations to local artifacts. Nothing leaves the box. Seed
  packs are representative subsets — the report says so.
- **Connected:** `controls.rubric` (full grounded catalog) + `evidence.search` (the shared evidence
  corpus) + `controls.map` (the one crosswalk). Only *structural* evidence pointers go to the MCP —
  never raw regulated data; AsterVault's broker/tokenize modes mask what must be sent.

---

## What goes in the MCP server (AsterVault, the `astervault` repo)

The client skills stay thin; the compliance **knowledge, grounding and shared corpus** are the server's
job. Three additions to the security-analysis surface (beside `registry.resolve` / `controls.map` /
`graph.enrich` / `risk.score` / `testgen.patterns`):

### 1. `controls.rubric` — the grounded rubric catalog
```
controls.rubric(framework, version?) -> { framework, version, controls: [rubric_control] }
```
- Owns the **full, versioned** control catalogs (ISO 27001:2022, ISO 9001:2015, SOC 2 TSC, HIPAA
  Security Rule, …) in the `rubric_control` shape (see `control-rubric/references/rubric-schema.md`).
- `maps_to` is reconciled server-side with `controls.map` so there is one crosswalk SSOT.
- `security_signal` is authored per control to link the catalog to the weakness registry — this is the
  server-side glue that makes security findings count as compliance evidence.
- Storage: catalog as data (YAML/DB) behind the tool; same tiering/governance as the registry.

### 2. `evidence.search` — the shared evidence corpus
```
evidence.search(framework, control_id, query, scope?) -> { records: [ {id, source, locator, kind, when, snippet, citation} ] }
evidence.upsert(records)   # evidence-collection indexes structural pointers here
```
- Backed by the existing **compliance-evidence store** (the Qdrant corpus that already holds
  tests + findings — reuse it, do not stand up a parallel store). Index *structural* records +
  citations; keep raw regulated data on the client.
- Enables cross-run, cross-harness recall: evidence gathered from one review is retrievable by the next.
- Tenancy / audience-binding / audit come for free from the gateway (every call returns an `audit_id`).

### 3. `controls.map` — reuse as-is
No change: the weakness→control crosswalk already exists and already covers these frameworks. The
rubric's `maps_to` and the `security_signal` → control linkage both ride on it. **Do not fork a second
crosswalk.**

### Memory
Verdicts, accepted evidence, and waivers (with the why) go through the existing `memory.*` plane
(`memory.capture` / `memory.promote` / `memory.recall`), scoped to the app + framework. The
human-signed sign-off is the promotion gate — nothing is "accepted evidence" until a person approves it.

### Data-shipping rule (unchanged)
The client's *structural* evidence (citations, finding ids, control ids, graph shape) may go to
AsterVault for grounding and shared recall. The server's catalogs and crosswalk never ship to the
client; the client's raw code, documents, and regulated data stay local. Offline mode sends nothing.

---

## Not in scope (yet)
- **External evidence connectors** (Jira / GitHub Issues / Linear / exported mail). This first cut is
  local + security-graph only; connectors are an additive `evidence-collection` source later, mirroring
  audit-ready's connector set, behind the same untrusted-input quarantine.
- **Certification.** The output is readiness; a human reviews and signs. AsterGuard does not certify.
