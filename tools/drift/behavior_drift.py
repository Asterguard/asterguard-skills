"""behavior_drift — empirical behavioral drift between two red-team run-sets.

Aligns two sets of behavioral run-records by test, then measures what changed in the
agent's *behavior* under the same attacks: a held attack that now breaks, ASR@budget
moving, refusal rate dropping. This is the EFFECT the cause-side facets predict.

Also reports a dependency-free Beta-Binomial posterior for the aggregate ASR (a credible
estimate from few trials — the honest version of a bare success percentage).

Run-record shape (per runs/*.json, one object or an array):
  {"test_id","weakness_id","verdict":"broke|held|inconclusive",
   "asr":{"budget":N,"value":0..1,"first_break_turn":N}}

CLI:  python behavior_drift.py A/runs B/runs      (dirs or single .json files)
"""
from __future__ import annotations

import sys
from typing import Dict, List

try:
    from common import load_runs, load_signals, make_delta
except ImportError:
    from tools.drift.common import load_runs, load_signals, make_delta


def _key(r: Dict) -> str:
    return str(r.get("test_id") or r.get("weakness_id") or r.get("id") or "")


def _by_key(runs: List[Dict]) -> Dict[str, Dict]:
    return {_key(r): r for r in runs if _key(r)}


def _asr(r: Dict) -> float:
    a = r.get("asr") or {}
    if "value" in a:
        return float(a["value"])
    return 1.0 if r.get("verdict") == "broke" else 0.0


def _beta_binomial(breaks: int, total: int) -> Dict:
    """Jeffreys-prior Beta(0.5+k, 0.5+n-k) posterior: mean + std, closed form, no deps."""
    a, b = 0.5 + breaks, 0.5 + (total - breaks)
    s = a + b
    mean = a / s
    var = (a * b) / (s * s * (s + 1))
    return {"mean": round(mean, 3), "std": round(var ** 0.5, 3), "breaks": breaks, "trials": total}


def compare(runs_a: List[Dict], runs_b: List[Dict], cfg=None) -> Dict:
    cfg = cfg or load_signals()
    a, b = _by_key(runs_a), _by_key(runs_b)
    changed, signals, evidence = [], [], []

    for k in a.keys() & b.keys():
        va, vb = a[k].get("verdict"), b[k].get("verdict")
        if va == "held" and vb == "broke":
            signals.append("new_break")
            evidence.append({"signal": "new_break", "test": k})
            changed.append({"test": k, "verdict": {"from": va, "to": vb}})
        elif va == "broke" and vb == "held":
            signals.append("break_fixed")
            evidence.append({"signal": "break_fixed", "test": k})
            changed.append({"test": k, "verdict": {"from": va, "to": vb}})
        da, db = _asr(a[k]), _asr(b[k])
        if db > da + 1e-9:
            signals.append("asr_increased")
            evidence.append({"signal": "asr_increased", "test": k, "from": da, "to": db})

    # aggregate refusal rate (held / total) across matched + all runs
    def refusal(runs: List[Dict]) -> float:
        n = len(runs) or 1
        return sum(1 for r in runs if r.get("verdict") == "held") / n

    ra, rb = refusal(runs_a), refusal(runs_b)
    if rb < ra - 1e-9:
        signals.append("refusal_dropped")
        evidence.append({"signal": "refusal_dropped", "from": round(ra, 3), "to": round(rb, 3)})

    delta = make_delta(
        "behavior",
        added=sorted(b.keys() - a.keys()),
        removed=sorted(a.keys() - b.keys()),
        changed=changed,
        signals=sorted(set(signals)),
        evidence=evidence,
        cfg=cfg,
    )
    # attach the statistical estimate (informational; does not affect direction)
    delta["asr_posterior"] = {
        "a": _beta_binomial(sum(1 for r in runs_a if r.get("verdict") == "broke"), len(runs_a)),
        "b": _beta_binomial(sum(1 for r in runs_b if r.get("verdict") == "broke"), len(runs_b)),
    }
    return delta


def main(argv: List[str]) -> int:
    if len(argv) != 2:
        print("usage: behavior_drift.py <A/runs> <B/runs>", file=sys.stderr)
        return 2
    try:
        from common import emit
    except ImportError:
        from tools.drift.common import emit
    emit(compare(load_runs(argv[0]), load_runs(argv[1])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
