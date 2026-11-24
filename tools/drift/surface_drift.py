"""surface_drift — attack-surface drift between two enriched-graph facet snapshots.

Diffs the derived attack-surface facets (reach / tools_violated / sinks / paths) that
graph.enrich produces: a new attack path, a newly-reachable regulated data class, a new
egress sink. These are EFFECTS — what the cause-side edits did to the graph. Also reports
the ARS delta when each snapshot carries one.

surface.json shape (graph.enrich facet output):
  {"ars":6.1,
   "reach":[{"store","classes":[...],"via":[...],"columns":[...]}],
   "tools_violated":[...], "sinks":[...],
   "paths":[{"kind","hops","sink","classes":[...],"missing_control"}]}

CLI:  python surface_drift.py A/surface.json B/surface.json
"""
from __future__ import annotations

import sys
from typing import Dict, List, Set, Tuple

try:
    from common import load_json, load_signals, make_delta
except ImportError:
    from tools.drift.common import load_json, load_signals, make_delta

_REGULATED = {"pii", "phi", "pci", "secret", "regulated", "financial", "credential"}


def _path_key(p: Dict) -> Tuple[str, str]:
    return (str(p.get("kind", "")), str(p.get("sink", "")))


def _reach_pairs(surface: Dict) -> Set[Tuple[str, str]]:
    pairs = set()
    for r in surface.get("reach", []):
        for c in r.get("classes", []):
            pairs.add((str(r.get("store", "")), str(c)))
    return pairs


def compare(surface_a: Dict, surface_b: Dict, cfg=None) -> Dict:
    cfg = cfg or load_signals()
    added, removed, changed, signals, evidence = [], [], [], [], []

    pa = {_path_key(p): p for p in surface_a.get("paths", [])}
    pb = {_path_key(p): p for p in surface_b.get("paths", [])}
    for k in pb.keys() - pa.keys():
        added.append({"path": pb[k]})
        signals.append("new_attack_path")
        evidence.append({"signal": "new_attack_path", "path": pb[k]})
    for k in pa.keys() - pb.keys():
        removed.append({"path": pa[k]})
        signals.append("path_closed")
        evidence.append({"signal": "path_closed", "path": pa[k]})

    ra, rb = _reach_pairs(surface_a), _reach_pairs(surface_b)
    for store, cls in rb - ra:
        if cls.lower() in _REGULATED:
            signals.append("new_reach_regulated")
            evidence.append({"signal": "new_reach_regulated", "store": store, "class": cls})

    sa, sb = set(surface_a.get("sinks", [])), set(surface_b.get("sinks", []))
    for s in sb - sa:
        signals.append("new_egress_sink")
        evidence.append({"signal": "new_egress_sink", "sink": s})

    delta = make_delta(
        "surface",
        added=added,
        removed=removed,
        changed=changed,
        signals=sorted(set(signals)),
        evidence=evidence,
        cfg=cfg,
    )
    ars_a, ars_b = surface_a.get("ars"), surface_b.get("ars")
    if ars_a is not None and ars_b is not None:
        delta["ars_delta"] = {"from": ars_a, "to": ars_b, "change": round(float(ars_b) - float(ars_a), 2)}
    return delta


def main(argv: List[str]) -> int:
    if len(argv) != 2:
        print("usage: surface_drift.py <A/surface.json> <B/surface.json>", file=sys.stderr)
        return 2
    try:
        from common import emit
    except ImportError:
        from tools.drift.common import emit
    emit(compare(load_json(argv[0]), load_json(argv[1])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
