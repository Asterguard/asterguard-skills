"""controls_drift — policy / control drift between two agent profiles.

Set-diff over the enforced controls and the open control gaps: a control removed or
loosened, an allowlist widened, or a previously-closed `missing_control` that has
reappeared. Consumes the `controls` list (and optional `missing_controls`) that the
remediation / controls.map skills produce.

Control shape (per profile.json):
  {"id","kind":"egress|approval|identity|network|dlp","target","state":"enforced|advisory|off",
   "allowlist":[...]}
Optional: "missing_controls": ["target-or-weakness that currently has no control"]

CLI:  python controls_drift.py A/profile.json B/profile.json
"""
from __future__ import annotations

import sys
from typing import Dict, List

try:
    from common import load_json, load_signals, make_delta
except ImportError:
    from tools.drift.common import load_json, load_signals, make_delta

_ENFORCED = "enforced"


def _by_id(profile: Dict) -> Dict[str, Dict]:
    return {c["id"]: c for c in profile.get("controls", []) if "id" in c}


def compare(profile_a: Dict, profile_b: Dict, cfg=None) -> Dict:
    cfg = cfg or load_signals()
    a, b = _by_id(profile_a), _by_id(profile_b)
    added, removed, changed, signals, evidence = [], [], [], [], []

    for cid in b.keys() - a.keys():
        added.append(cid)
        if str(b[cid].get("state")) == _ENFORCED:
            signals.append("control_added")
            evidence.append({"signal": "control_added", "control": cid, "target": b[cid].get("target")})

    for cid in a.keys() - b.keys():
        removed.append(cid)
        if str(a[cid].get("state")) == _ENFORCED:
            signals.append("control_removed")
            evidence.append({"signal": "control_removed", "control": cid, "target": a[cid].get("target")})

    for cid in a.keys() & b.keys():
        ca, cb = a[cid], b[cid]
        diffs = {}
        if str(ca.get("state")) == _ENFORCED and str(cb.get("state")) != _ENFORCED:
            signals.append("control_loosened")
            evidence.append({"signal": "control_loosened", "control": cid,
                             "from": ca.get("state"), "to": cb.get("state")})
            diffs["state"] = {"from": ca.get("state"), "to": cb.get("state")}
        la, lb = set(ca.get("allowlist", [])), set(cb.get("allowlist", []))
        if lb - la:
            signals.append("allowlist_widened")
            evidence.append({"signal": "allowlist_widened", "control": cid, "added": sorted(lb - la)})
            diffs["allowlist_added"] = sorted(lb - la)
        if diffs:
            changed.append({"control": cid, **diffs})

    # a gap that a prior version had closed is open again
    miss_a, miss_b = set(profile_a.get("missing_controls", [])), set(profile_b.get("missing_controls", []))
    for target in miss_b - miss_a:
        signals.append("missing_control_reappeared")
        evidence.append({"signal": "missing_control_reappeared", "target": target})

    return make_delta(
        "controls",
        added=added,
        removed=removed,
        changed=changed,
        signals=sorted(set(signals)),
        evidence=evidence,
        cfg=cfg,
    )


def main(argv: List[str]) -> int:
    if len(argv) != 2:
        print("usage: controls_drift.py <A/profile.json> <B/profile.json>", file=sys.stderr)
        return 2
    try:
        from common import emit
    except ImportError:
        from tools.drift.common import emit
    emit(compare(load_json(argv[0]), load_json(argv[1])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
