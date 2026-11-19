# Worked example — AppSec on a vulnerable LLM support agent

A full, step-by-step analysis of **`Asterguard/support-agent-demo`** @ `95d6ae5` (branch
`feat/billing-assistant`, **PR #1**) — a real Python LLM agent whose "add a billing assistant" PR quietly
wires the **lethal trifecta**: private PII + untrusted input + external egress, with the human gate turned
off. Two acts, run through the AsterGuard skills:

| Act | Skills | Question | Report |
|---|---|---|---|
| **1 · Vulnerability analysis** | [`/local-scan`](../../skills/local-scan) · [`sca-graph`](../../skills/sca-graph) · [`weakness-graph`](../../skills/weakness-graph) · [`sast-generation`](../../skills/sast-generation) | *what's wrong, and is it real?* | [`report-vulnerability-analysis.md`](report-vulnerability-analysis.md) |
| **2 · Risk analysis** | [`agent-profiling`](../../skills/agent-profiling) · [`data-flow`](../../skills/data-flow) · [`information-flow`](../../skills/information-flow) · [`risk-context`](../../skills/risk-context) · [`atom-score-finding`](../../skills/atom-score-finding) · [`security-engineer`](../../skills/security-engineer) | *how much it matters, what to fix first* | [`report-risk-analysis.md`](report-risk-analysis.md) |

This is the **app-code companion** to [`terraform-agent-platform`](../terraform-agent-platform) (which
scans the same kind of agent's *infrastructure*). Here the subject is the agent's **code, dependencies and
data** — so unlike the IaC-only example, **four of five scan lanes fire** and the full risk pipeline runs.

> **Offline mode.** Every number below was produced on-host with open-source scanners — **nothing was
> uploaded**. The raw findings and EPSS come from `grype`; the **calibrated ARS (0–10)** and **KEV**
> enrichment require the connected AsterVault pass and are labelled `pending`. The risk **order** is stable
> in both modes — that's the point of Act 2. See [Method & coverage notes](#method--coverage-notes).

---

## 0. The app under test

A LangGraph support agent (`app/`, `requirements.txt`, `data/` customer PII). The `feat/billing-assistant`
PR adds a "partner export + reporting integration" and, in the same diff, flips two safety defaults:

```
          UNTRUSTED                 TRUST BOUNDARY                PRIVATE / EGRESS
  customer + "partner" chat ──► assistant (gpt-4o-mini, temp 0.9)
                                  system prompt: "…if a partner asks,
                                   export account records…"
                                        │  require_tool_approval = False  → no human gate
                 ┌──────────────────────┼───────────────────────────┐
                 ▼                       ▼                           ▼
        lookup_any_customer      search_knowledge            export_account_records
        (ALL tenants, PII)       (ALL orgs)                  (POST → partner URL)
                 │                                                   │
        customers DB (SSN/bank/card)                        public-read S3 bucket
        + global long-term memory                           + external partner
```

All three legs of the lethal trifecta are wired by this one PR — which is exactly the kind of change a
reviewer waves through and a CVE scanner never flags.

---

## 1. Setup — run it yourself

### Step 1 — install the skills in your harness

**Claude Code (plugin).** Run these two commands in Claude Code — they add the AsterGuard marketplace and
install the skill pack:

```text
/plugin marketplace add Asterguard/asterguard-skills
/plugin install asterguard-security@asterguard-marketplace
```

That registers every skill as a **slash command** (`/local-scan`, `/sca-graph`, `/agent-profiling`, …) and
ships `.mcp.json`. For **offline mode**, leave `ASTERVAULT_MCP_URL` unset — the skills detect the missing
gateway and run locally. (Full matrix in the [repo Install section](../../README.md#install).)

**Cursor (and Codex / OpenCode / any MCP harness).** The skill bodies are plain Markdown, so build the
bundle once and load it as project rules:

```bash
git clone git@github.com:Asterguard/asterguard-skills.git
cd asterguard-skills
scripts/build-codex.sh        # emits ./dist/codex/ — AGENTS.md + skills/
```

Then, in your project: copy the server block from this repo's [`mcp.json`](../../mcp.json) into
`.cursor/mcp.json`, and drop the bundle's `skills/` bodies in as Cursor **project rules** (and/or load its
`AGENTS.md`). In Cursor the skills are **not** slash commands — you invoke one by asking the agent by name,
e.g. *"run the local-scan skill on `.`"* (Claude Code slash-command syntax is shown in Acts 1–2 below; in
Cursor/Codex phrase the same skill as a request.)

### Step 2 — scanners (optional; `local-scan` auto-installs any missing)

```bash
brew install syft grype trufflehog semgrep          # SBOM · CVE · secrets · SAST
pipx install checkov                                 # IaC (the PR adds infra/storage.tf)
```

### Step 3 — get the subject app, pinned at the PR head

```bash
git clone git@github.com:Asterguard/support-agent-demo.git
cd support-agent-demo
git checkout feat/billing-assistant                  # PR #1, head 95d6ae5
```

Everything below runs **fully offline** — no gateway, no token, nothing leaves the box. To turn on the
calibrated **ARS** score and **KEV** enrichment, register the AsterVault gateway as an MCP server and attach
an ARS token (see [`docs/MCP_WIRING.md`](../../docs/MCP_WIRING.md)); the same commands then fill the
`pending` columns. Run the two acts in order, or jump to whichever you need.

---

## 2. Act 1 — vulnerability analysis

*What's wrong, and is it actually reachable.* Run the lanes, then prove each code weakness at its sink:

```bash
/local-scan .                 # 4 lanes: SCA (syft+grype) · SAST · secrets · AI-BOM · IaC
/sca-graph .                  # SBOM dependency tree + CVE overlay, ranked by EPSS
/sast-generation .            # target-grounded semgrep rules — stock packs find 0 here
/weakness-graph .             # weakness classes ↔ components, each weakness → control
```

| Lane | Tool | Result |
|---|---|---|
| Dependencies (SCA) | syft + grype | **43 CVEs** across 5 pinned-old packages |
| Code (SAST) | semgrep + **grounded rules** | **4 weaknesses** proven at their sinks (SQLi, PII→memory, unauth export, PII-in-logs) |
| Infrastructure (IaC) | checkov | **12 failed** — the export bucket is `public-read` |
| Secrets | trufflehog | **0 verified** (the exfil target is a config URL, not a stored secret) |
| AI assets (AI-BOM) | ai-bom | 1 model, 5 tools, 3 data stores |

**The teaching beat:** stock semgrep packs (`p/python`, `p/security-audit`) found **0** — the sinks are
hand-rolled (raw `sqlite3`, a bare `requests.post`), not library patterns. `sast-generation` emits rules
keyed to *this repo's* actual sinks, which prove each weakness with a `file:line`. → full writeup in
**[`report-vulnerability-analysis.md`](report-vulnerability-analysis.md)**.

---

## 3. Act 2 — risk analysis

*How much it matters, and what to fix first.* Profile the agent's authority, trace the PII, then score and
order the findings:

```bash
/agent-profiling .            # AI-BOM + authority boundaries (tools, model, trust/authority edges)
/data-flow . && /information-flow .   # PII store → tool → egress, with confidentiality/integrity labels
/risk-context .               # per-finding feature vector: reachability · data class · tool authority · EPSS
/atom-score-finding .         # calibrated ARS 0–10 (connected pass) — offline yields the raw vectors + order
/security-engineer .          # one assessment: verdict, attack paths, fixes ranked by blast radius
```

**The inversion this act exists to show** — raw EPSS and real risk disagree:

| Finding | EPSS | Reachable? | Offline tier |
|---|---|---|---|
| Ungated export of cross-tenant PII | — | **yes** (live tool on egress path) | **Critical** |
| SQL injection `billing_db.py:32` | — | **yes** | **Critical** |
| `cryptography 2.3` CVE | **68.4% (99th pct)** | **no** (transitive, unused) | **Low** |

The single highest-EPSS CVE in the repo drops to the bottom because the agent never exercises it, while an
ungated tool on a cross-tenant PII egress path — which no CVE scanner ranks — floats to the top. That gap
*is* risk analysis. → full attack paths, control gaps and the 6-step fix order in
**[`report-risk-analysis.md`](report-risk-analysis.md)**. **Verdict: BLOCK.**

---

## 4. The resulting reports

Both markdown deliverables live in this folder, rendered on GitHub:

- **[`report-vulnerability-analysis.md`](report-vulnerability-analysis.md)** — the lane results, 43 CVEs by
  package + EPSS, the 4 code weaknesses each proven at its sink, the public bucket, and the AI-BOM. Says
  *where the risk is* and stops.
- **[`report-risk-analysis.md`](report-risk-analysis.md)** — the agent authority boundary, the
  information-flow table (C3/PCI PII → low/public sinks), 3 mermaid attack paths, the reachability-weighted
  risk ranking (the EPSS inversion), the weakness→control gaps (SOC2 / GDPR / PCI-DSS / OWASP-LLM / NIST
  AI-RMF), and the fixes ordered by blast radius. Says *what it means and how to fix it*.

Read them in order: Act 1 is the triage, Act 2 is the assessment you hand to an engineer. Both are produced
in **client mode** — generated on your machine by the skills; offline, the AsterVault MCP is not contacted
at all, and in the connected pass it supplies only grounding (registry IDs, control crosswalk, the
calibrated ARS floor), never your source or findings.

---

## Method & coverage notes

- **Branch pinned** at `95d6ae5` (`feat/billing-assistant`, PR #1); 13 files changed vs `main`. Every lane
  ran on-host — **nothing uploaded**.
- **Tools.** syft 1.57.2 · grype 0.122.0 · trufflehog 3.99.9 · semgrep 1.168.0 · checkov 3.4.5.
- **Reachability** is read from the real imports + call graph (`app/tools.py`, `app/graph.py`,
  `app/billing_db.py`), not inferred from the SBOM — this is what separates risk analysis from a CVE list.
- **Offline vs connected.** Raw findings + EPSS are offline. **KEV** (`kev:n/e`) and the calibrated **ARS
  0–10** need the connected AsterVault pass and are shown as `pending`; the risk **order** is stable across
  both modes.
- **Not run:** DAST, behavioral red-team, canary episodes — the offensive example (next) drives the live
  agent and marks findings *proven*. This example is static + reachability analysis only.

---

*Produced by the AsterGuard skill pack (client mode). Screen-recorded walkthroughs of each act will be
linked here once recorded.*
