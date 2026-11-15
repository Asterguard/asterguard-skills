---
name: sca-graph
description: Build the SCA graph — the SBOM dependency tree plus a CVE overlay — from a local scan. Produces package nodes linked by depends_on, with cve nodes attached by affected_by, deduped and severity-ranked. Use when a security engineer needs the dependency/vulnerability structure of a repo or image, or asks why a CVE count is what it is.
---

# SCA Graph

Turn a flat SBOM + CVE list into the dependency **tree** with a vulnerability overlay, built to the
shared schema. This is the structure behind "which package pulls in what, and what's vulnerable."

## When to Activate

- After `local-scan` has produced `sbom` + SCA findings.
- The engineer wants the dependency tree, the vulnerable-package roll-up, or a CVE explanation.
- A CVE count looks wrong — the graph makes duplication vs. real breadth visible (e.g. one CVE
  across many packages, or one package at two versions from a multi-stage image).

## Core Concepts

- A **package** node per `name==version` (`comp:package:`), `meta.transitive` and `ecosystem` set.
- A **`depends_on`** edge per dependency relation → the tree. Roots are direct deps of the app.
- A **cve** node per distinct `cve_id` (`comp:cve:`), linked to each affected package by
  **`affected_by`**. Dedupe CVEs by id; a CVE affecting N packages is ONE node with N edges.
- Rank by severity then EPSS/KEV when present.

## Method

1. Read `./.asterguard/scan.json` → `sbom` + sca findings.
2. Emit one package node per `name==version`; add `depends_on` edges from `sbom[].deps`.
3. Emit one cve node per distinct `cve_id`; add `affected_by` edges to its package(s).
4. Roll up: per package, worst severity + CVE count; per CVE, affected-package count.
5. Write nodes/edges into the shared graph envelope (`./.asterguard/graph.json`).

## Practical Guidance

- **Dedupe is by CVE id, not by row.** If the same `cve_id` appears for two package versions, that is
  one cve node with two `affected_by` edges — reported once. (This is what prevents an inflated count.)
- **Separate origin:** tag each package `meta.origin = app | os_base_image | runtime` (Alpine `-rN` /
  Debian `+debN` = os_base_image; `node`/`python` interpreters = runtime). A container SBOM is
  dominated by OS/base-image packages — surface app deps first; keep OS/base-image behind a roll-up.
- Collapse the view to **vulnerable packages** (one row per package, worst sev + CVE count), not a
  flat CVE list — the graph already holds the full detail for drill-down.

## Integration

- local-scan — provides the SBOM + CVEs
- weakness-graph — CVEs map to weakness/control; cross-link there
- risk-report — renders the package roll-up and CVE drill-down

## References

- [Graph schema (SSOT)](../../docs/graph-schema.md)
