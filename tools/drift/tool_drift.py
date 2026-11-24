"""tool_drift — AI-BOM / tool-authority drift between two agent profiles.

Set-diff over the tool inventory and each tool's authority: tools added/removed,
approval (HITL) gate flipped, reach broadened, over-privilege appeared. Consumes the
`tools` list produced by the agent-profiling skill.

Tool shape (per profile.json):
  {"name","side_effect":"read|write|execute","reach":["store:...","external:..."],
   "requires_approval":bool,"scopes":[...],"over_privileged":bool}

CLI:  python tool_drift.py A/profile.json B/profile.json
"""
from __future__ import annotations

import sys
from typing import Dict, List

try:
    from common import load_json, load_signals, make_delta
except ImportError:
    from tools.drift.common import load_json, load_signals, make_delta

_EFFECTFUL = {"write", "execute", "effectful", "side-effect"}
_EGRESS_HINT = ("external", "egress", "net:", "http", "url", "internet", "anon")


def _is_egress(reach: List[str]) -> bool:
    return any(any(h in str(r).lower() for h in _EGRESS_HINT) for r in (reach or []))


def _effectful(tool: Dict) -> bool:
    return str(tool.get("side_effect", "")).lower() in _EFFECTFUL


def _by_name(profile: Dict) -> Dict[str, Dict]:
    return {t["name"]: t for t in profile.get("tools", []) if "name" in t}


def compare(profile_a: Dict, profile_b: Dict, cfg=None) -> Dict:
    cfg = cfg or load_signals()
    a, b = _by_name(profile_a), _by_name(profile_b)
    added, removed, changed, signals, evidence = [], [], [], [], []

    for name in b.keys() - a.keys():
        t = b[name]
        added.append(name)
        if _effectful(t) and _is_egress(t.get("reach", [])):
            signals.append("new_egress_tool")
            evidence.append({"signal": "new_egress_tool", "tool": name, "reach": t.get("reach", [])})

    for name in a.keys() - b.keys():
        removed.append(name)
        if _effectful(a[name]):
            signals.append("tool_removed")
            evidence.append({"signal": "tool_removed", "tool": name})

    for name in a.keys() & b.keys():
        ta, tb = a[name], b[name]
        diffs = {}
        appr_a, appr_b = bool(ta.get("requires_approval")), bool(tb.get("requires_approval"))
        if appr_a and not appr_b:
            signals.append("approval_disabled")
            evidence.append({"signal": "approval_disabled", "tool": name})
            diffs["requires_approval"] = {"from": True, "to": False}
        elif not appr_a and appr_b:
            signals.append("approval_enabled")
            evidence.append({"signal": "approval_enabled", "tool": name})
            diffs["requires_approval"] = {"from": False, "to": True}

        ra, rb = set(ta.get("reach", [])), set(tb.get("reach", []))
        if rb - ra:
            signals.append("tool_scope_broadened")
            evidence.append({"signal": "tool_scope_broadened", "tool": name, "new_reach": sorted(rb - ra)})
            diffs["reach_added"] = sorted(rb - ra)

        if bool(tb.get("over_privileged")) and not bool(ta.get("over_privileged")):
            signals.append("over_privileged_appeared")
            evidence.append({"signal": "over_privileged_appeared", "tool": name})
            diffs["over_privileged"] = {"from": False, "to": True}

        if diffs:
            changed.append({"tool": name, **diffs})

    return make_delta(
        "tools",
        added=added,
        removed=removed,
        changed=changed,
        signals=sorted(set(signals)),
        evidence=evidence,
        cfg=cfg,
    )


def main(argv: List[str]) -> int:
    if len(argv) != 2:
        print("usage: tool_drift.py <A/profile.json> <B/profile.json>", file=sys.stderr)
        return 2
    try:
        from common import emit
    except ImportError:
        from tools.drift.common import emit
    emit(compare(load_json(argv[0]), load_json(argv[1])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
