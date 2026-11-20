#!/usr/bin/env python3
"""Aggregate engagement run records into the four outcome artifacts.

Reads every run record in RUNS_DIR (default ./.asterguard/runs/*.json) and emits, next to it:
  outcomes.json · canary-evidence.json · regression-suite.json · archived-review.json
(see ../references/outcomes-schema.md). Stdlib only; harness-portable. The verdict is taken ONLY
from evidence.verify.fired — never from model text.

Usage: aggregate_outcomes.py [RUNS_DIR] [--engagement NAME]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

BANDS = ("critical", "high", "medium", "low", "unknown")


def _load(runs_dir: Path) -> list[dict]:
    out = []
    for p in sorted(runs_dir.glob("*.json")):
        try:
            out.append(json.loads(p.read_text()))
        except (ValueError, OSError):
            pass
    return out


def _fired(r: dict) -> bool:
    return bool(((r.get("evidence") or {}).get("verify") or {}).get("fired"))


def _audit_ids(r: dict) -> list:
    ev = r.get("evidence") or {}
    ids = list(ev.get("audit_ids") or [])
    if ev.get("audit_id") and ev["audit_id"] not in ids:
        ids.insert(0, ev["audit_id"])
    return ids


def _mode(r: dict) -> str:
    return "connected" if _audit_ids(r) and "offline" not in str(r.get("mode", "")).lower() else "offline"


def aggregate(runs: list[dict], engagement: str) -> dict:
    now = time.time()
    by_sev = {b: 0 for b in BANDS}
    tests, kill_chain, evidence, suite = [], [], [], []
    max_ars = {"ars": 0.0, "band": "low"}

    for r in runs:
        verdict = r.get("verdict") or ("broke" if _fired(r) else "held")
        ars = r.get("ars") or {}
        asr = r.get("asr") or {}
        tests.append({
            "id": r.get("id"), "test_name": r.get("test_name") or r.get("objective"),
            "verdict": verdict, "asr": asr, "weakness": r.get("weakness") or {},
            "ars": ars, "mode": _mode(r),
            "attacker_model": (r.get("attacker_model") or {}).get("model") if isinstance(r.get("attacker_model"), dict) else r.get("attacker_model"),
            "defender_model": (r.get("defender_model") or {}).get("model") if isinstance(r.get("defender_model"), dict) else r.get("defender_model"),
        })
        if verdict == "broke":
            band = ars.get("band") or "high"
            by_sev[band] = by_sev.get(band, 0) + 1
            if (ars.get("ars") or 0) >= max_ars["ars"]:
                max_ars = {"ars": ars.get("ars"), "band": band}
            kill_chain.append({"id": r.get("id"), "first_break_turn": asr.get("first_break_turn")})
            can = r.get("canary") or {}
            evidence.append({
                "id": r.get("id"), "canary_type": can.get("type"), "token_id": can.get("token_id"),
                "planted_location": can.get("planted_location"), "fired": True,
                "audit_id": (_audit_ids(r) or [None])[-1], "audit_ids": _audit_ids(r), "mode": _mode(r),
            })
            suite.append({
                "id": r.get("id"), "objective": r.get("test_name") or r.get("objective"),
                "canary_type": can.get("type"), "budget": asr.get("budget"),
                "attack_turns": r.get("attack_turns") or [], "expected": "held",
            })

    broke = sum(1 for t in tests if t["verdict"] == "broke")
    outcomes = {
        "generated": now, "engagement": engagement,
        "totals": {"tests": len(tests), "broke": broke, "held": len(tests) - broke},
        "by_severity": by_sev, "max_ars": max_ars, "tests": tests, "kill_chain": kill_chain,
    }
    canary_evidence = {"generated": now, "evidence": evidence}
    regression = {"generated": now, "suite": suite}
    archived = {
        "engagement": engagement, "generated": now,
        "verdicts": {"broke": broke, "held": len(tests) - broke}, "max_ars": max_ars,
        "report": "./.asterguard/report.html", "runs": [t["id"] for t in tests],
        "mode": "connected" if any(_mode(r) == "connected" for r in runs) else "offline",
        "note": (f"{broke} proven break(s), top ARS {max_ars['ars']} ({max_ars['band']}); "
                 "remediation bundle emitted — re-run the regression suite to confirm HELD."
                 if broke else "no proven breaks on this budget/attacker; see ASR per test."),
    }
    return {"outcomes.json": outcomes, "canary-evidence.json": canary_evidence,
            "regression-suite.json": regression, "archived-review.json": archived}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    runs_dir = Path(args[0]) if args else Path("./.asterguard/runs")
    engagement = "security-engineer-scan"
    if "--engagement" in sys.argv:
        engagement = sys.argv[sys.argv.index("--engagement") + 1]
    if not runs_dir.is_dir():
        print(f"no runs dir: {runs_dir}", file=sys.stderr)
        sys.exit(2)
    runs = _load(runs_dir)
    if not runs:
        print(f"no run records in {runs_dir}", file=sys.stderr)
        sys.exit(2)
    out_dir = runs_dir.parent
    artifacts = aggregate(runs, engagement)
    for name, data in artifacts.items():
        (out_dir / name).write_text(json.dumps(data, indent=2))
    o = artifacts["outcomes.json"]
    print(f"aggregated {o['totals']['tests']} runs → {out_dir}/  "
          f"(broke={o['totals']['broke']} held={o['totals']['held']}, "
          f"top ARS {o['max_ars']['ars']} {o['max_ars']['band']})")


if __name__ == "__main__":
    main()
