---
name: local-scan
description: Perform a security scan locally — run SAST (code sinks), SCA (SBOM+CVE), IaC, secrets and AI-BOM collectors against a repo path or container image, and bootstrap any missing collector. Produces raw, normalized findings the graph skills consume. Use when a security engineer needs scan results on a repo or image without a hosted scanner.
---

# Local Scan

Run the raw collectors on the box and normalize their output. This skill does **collection**, not
analysis — the graph skills turn these outputs into architecture. Claude invokes the tools, reads
their native JSON, and writes normalized findings to `./.asterguard/scan.json`.

## When to Activate

- The target is a repo path or a container image ref and the engineer wants SCA/IaC/secrets/AI-BOM.
- Before any graph skill that needs packages, CVEs, or misconfigurations.
- When a collector is missing and must be delivered before scanning.

## Core Concepts

Each lane is one collector producing native JSON; Claude normalizes to a flat finding list keyed the
way the schema expects. Fail-open: a missing or failing collector degrades its lane and records the
gap, never aborts the run. "Local" is the whole point — nothing is uploaded.

## Collectors (deliver if missing)

| Lane | Collector | Command | Emits |
|---|---|---|---|
| SAST | `semgrep` (registry rulesets) | `semgrep --config p/python --config p/flask --config p/security-audit --config p/secrets --json <path>` | code-level sinks (CWE) |
| SCA | `grype` (+ `syft` for SBOM) | `syft <target> -o json > sbom.json; grype sbom:sbom.json -o json` | packages + CVEs |
| IaC | `checkov` | `checkov -d <path> -o json` | misconfigurations |
| Secrets | `trufflehog` | `trufflehog filesystem <path> --json` | exposed secrets |
| AI-BOM | this skill | parse manifests + import graph for models/tools/datasets | AI assets |

**Bootstrap:** before a lane runs, check the binary on `PATH`; if absent, install it via
`scripts/bootstrap.sh <collector>` (brew / pipx / official install script per the marketplace
`packages` manifest). Record which collectors were delivered.

## Practical Guidance

- **SAST (low freedom):** run `semgrep` with community registry rulesets (`p/python`, `p/flask`,
  `p/security-audit`, `p/secrets`), never rules fitted to the target; map each result's CWE to a
  registry `weakness_id` (via the registry's `cwe_refs`) so the sink lines up with the control
  crosswalk and any DAST probe for the same CWE. Code targets only — skip for an image ref.
  This lane is **collection** with generic rulesets; to **generate** target-grounded semgrep rules
  from the weakness graph (the static twin of DAST probes), hand off to `sast-generation` after the
  graph is built.
- **Image vs repo (low freedom):** for an image ref, run `syft`/`grype` against `registry:<ref>` or
  a local tarball — no checkout. For a repo, run all four lanes over the working tree.
- Normalize every finding to: `{lane, source, title, severity, file|resource, package, version,
  cve_id, weakness_id}` — the exact keys `sca-graph` / `weakness-graph` read.
- Keep the native collector JSON alongside the normalized file for audit (`./.asterguard/raw/`).
- Never fabricate a CVE, severity, or secret — emit only what a collector reported.

## Output

`./.asterguard/scan.json`:
```jsonc
{ "target": "...", "source": "code|infra", "collectors": { "grype": "3.x|missing", ... },
  "findings": [ { "lane": "sca", "title": "CVE-… in name==version", "severity": "...",
                  "package": "name", "version": "…", "cve_id": "CVE-…" }, … ],
  "sbom": [ { "name": "...", "version": "...", "ecosystem": "...", "transitive": true, "deps": ["…"] } ] }
```

## Enrichment, output formats & suppression

**CVE freshness via the gateway (no direct calls).** `grype` gives the local CVE baseline; connected,
`knowledge.query` enriches it with fresh CVE data that the **AsterVault gateway** sources upstream (e.g.
OSV) and meters — the client never calls a third-party CVE API directly. Offline, the local `grype`
result stands and the report notes reduced freshness.

**SARIF.** Besides `scan.json`, emit a **SARIF** report (`./.asterguard/scan.sarif`) so findings feed
GitHub code-scanning / CI. Each finding carries its `weakness_id` + severity.

**Baseline / FP-suppression.** Accept known findings via a baseline (fingerprint + glob rules) in
`./.asterguard/baseline.json`, so a re-scan surfaces only **new** issues. A suppressed finding stays in
the output marked `suppressed` with its baseline reason — never silently dropped.

## Integration

- sca-graph, weakness-graph, data-flow — consume `scan.json` / `sbom`
- sast-generation — the **generation** counterpart: turns the resulting weakness graph into
  target-grounded semgrep rules (this lane only runs generic rulesets)
- security-engineer — calls this first for code/infra targets
- proxy-recon — the traffic-source counterpart (no collectors; records live calls instead)
