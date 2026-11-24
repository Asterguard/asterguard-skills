"""sbom_drift — dependency / supply-chain drift between two SBOM+CVE snapshots.

Diffs the package set and the CVE surface across versions: a dependency added, a new
Known-Exploited-Vulnerability (KEV) in the tree, or a growing CVE surface. Consumes the
SBOM+CVE roll-up the sca-graph skill produces.

sbom.json shape:
  {"packages":[{"name","version","cves":[{"id","severity":"low|medium|high|critical",
   "kev":bool,"epss":0..1}]}]}

CLI:  python sbom_drift.py A/sbom.json B/sbom.json
"""
from __future__ import annotations

import sys
from typing import Dict, List, Set

try:
    from common import load_json, load_signals, make_delta
except ImportError:
    from tools.drift.common import load_json, load_signals, make_delta

_SEV_WEIGHT = {"low": 1, "medium": 3, "high": 7, "critical": 10}


def _pkg_key(p: Dict) -> str:
    return f"{p.get('name')}@{p.get('version')}"


def _cve_ids(sbom: Dict) -> Set[str]:
    out = set()
    for p in sbom.get("packages", []):
        for c in p.get("cves", []):
            out.add(str(c.get("id")))
    return out


def _kev_ids(sbom: Dict) -> Set[str]:
    out = set()
    for p in sbom.get("packages", []):
        for c in p.get("cves", []):
            if c.get("kev"):
                out.add(str(c.get("id")))
    return out


def _severity_load(sbom: Dict) -> int:
    total = 0
    for p in sbom.get("packages", []):
        for c in p.get("cves", []):
            total += _SEV_WEIGHT.get(str(c.get("severity", "")).lower(), 0)
    return total


def compare(sbom_a: Dict, sbom_b: Dict, cfg=None) -> Dict:
    cfg = cfg or load_signals()
    pa = {_pkg_key(p) for p in sbom_a.get("packages", [])}
    pb = {_pkg_key(p) for p in sbom_b.get("packages", [])}
    added, removed, signals, evidence = [], [], [], []

    for k in pb - pa:
        added.append(k)
        signals.append("dependency_added")
    for k in pa - pb:
        removed.append(k)

    for cid in _kev_ids(sbom_b) - _kev_ids(sbom_a):
        signals.append("new_kev")
        evidence.append({"signal": "new_kev", "cve": cid})

    load_a, load_b = _severity_load(sbom_a), _severity_load(sbom_b)
    if load_b > load_a:
        signals.append("cve_surface_grew")
        evidence.append({"signal": "cve_surface_grew", "from": load_a, "to": load_b,
                         "new_cves": sorted(_cve_ids(sbom_b) - _cve_ids(sbom_a))})

    return make_delta(
        "sbom",
        added=added,
        removed=removed,
        signals=sorted(set(signals)),
        evidence=evidence,
        cfg=cfg,
    )


def main(argv: List[str]) -> int:
    if len(argv) != 2:
        print("usage: sbom_drift.py <A/sbom.json> <B/sbom.json>", file=sys.stderr)
        return 2
    try:
        from common import emit
    except ImportError:
        from tools.drift.common import emit
    emit(compare(load_json(argv[0]), load_json(argv[1])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
