"""model_drift — LLM/model drift between two agent profiles.

The model is part of the attack surface: a changed provider/model or a loosened sampling
/ safety configuration shifts the agent's refusal behavior. Consumes the `model` block
the agent-profiling skill records.

model shape (per profile.json):
  {"provider","model","temperature":0.2,"less_restricted":false,"safety_system":true}

CLI:  python model_drift.py A/profile.json B/profile.json
"""
from __future__ import annotations

import sys
from typing import Dict, List

try:
    from common import load_json, load_signals, make_delta
except ImportError:
    from tools.drift.common import load_json, load_signals, make_delta

_TEMP_JUMP = 0.3  # temperature increase considered a meaningful loosening


def compare(profile_a: Dict, profile_b: Dict, cfg=None) -> Dict:
    cfg = cfg or load_signals()
    ma, mb = profile_a.get("model") or {}, profile_b.get("model") or {}
    changed, signals, evidence = [], [], []

    id_a = (ma.get("provider"), ma.get("model"))
    id_b = (mb.get("provider"), mb.get("model"))
    if id_a != id_b:
        signals.append("model_changed")
        evidence.append({"signal": "model_changed", "from": id_a, "to": id_b})
        changed.append({"model": {"from": id_a, "to": id_b}})

    loosened = []
    if mb.get("less_restricted") and not ma.get("less_restricted"):
        loosened.append("less_restricted flag set")
    if ma.get("safety_system") and not mb.get("safety_system"):
        loosened.append("safety system removed")
    ta, tb = ma.get("temperature"), mb.get("temperature")
    if ta is not None and tb is not None and float(tb) - float(ta) >= _TEMP_JUMP:
        loosened.append(f"temperature {ta} -> {tb}")
    if loosened:
        signals.append("model_less_restricted")
        evidence.append({"signal": "model_less_restricted", "reasons": loosened})

    return make_delta(
        "model",
        changed=changed,
        signals=sorted(set(signals)),
        evidence=evidence,
        cfg=cfg,
    )


def main(argv: List[str]) -> int:
    if len(argv) != 2:
        print("usage: model_drift.py <A/profile.json> <B/profile.json>", file=sys.stderr)
        return 2
    try:
        from common import emit
    except ImportError:
        from tools.drift.common import emit
    emit(compare(load_json(argv[0]), load_json(argv[1])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
