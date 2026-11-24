"""drift — the composer. Run every applicable comparator over two version snapshots and
assemble one DriftReport: the per-facet deltas, grouped cause vs effect, an aggregate
band, and the cause -> effect narrative.

A version snapshot is a directory with any of:
  profile.json   (system_prompt, tools, controls, model)  -> prompt/tools/controls/model drift
  surface.json   (graph.enrich facets)                     -> surface drift
  sbom.json      (sca-graph SBOM+CVE roll-up)              -> sbom drift
  runs/*.json    (behavioral run-records)                  -> behavior drift

Offline (default) emits the deterministic report. With --connected, the assembled signals
are also handed to the AsterVault gateway `drift.compare` for a calibrated drift index +
multi-run trend; if the gateway is unreachable the report is still returned, marked
degraded. The model never runs locally.

CLI:
  python drift.py <A_dir> <B_dir> [--connected] [--out report.json]
"""
from __future__ import annotations

import argparse
import datetime
import sys
from typing import Any, Dict, List

try:
    from common import aggregate, emit, load_signals, read_version
    import prompt_drift, tool_drift, controls_drift, behavior_drift, surface_drift, model_drift, sbom_drift
    import explain
except ImportError:
    from tools.drift.common import aggregate, emit, load_signals, read_version
    from tools.drift import (prompt_drift, tool_drift, controls_drift, behavior_drift,
                             surface_drift, model_drift, sbom_drift, explain)

FACET_ROLE = {
    "prompt": "cause", "tools": "cause", "controls": "cause", "model": "cause",
    "behavior": "effect", "surface": "effect", "sbom": "effect",
}


def build_report(dir_a: str, dir_b: str, cfg: Dict[str, Any] = None) -> Dict[str, Any]:
    cfg = cfg or load_signals()
    va, vb = read_version(dir_a), read_version(dir_b)
    deltas: List[Dict[str, Any]] = []

    if "profile" in va and "profile" in vb:
        pa, pb = va["profile"], vb["profile"]
        deltas.append(prompt_drift.compare(pa.get("system_prompt", ""), pb.get("system_prompt", ""), cfg))
        deltas.append(tool_drift.compare(pa, pb, cfg))
        deltas.append(controls_drift.compare(pa, pb, cfg))
        deltas.append(model_drift.compare(pa, pb, cfg))
    if "surface" in va and "surface" in vb:
        deltas.append(surface_drift.compare(va["surface"], vb["surface"], cfg))
    if "runs" in va and "runs" in vb:
        deltas.append(behavior_drift.compare(va["runs"], vb["runs"], cfg))
    if "sbom" in va and "sbom" in vb:
        deltas.append(sbom_drift.compare(va["sbom"], vb["sbom"], cfg))

    # keep only facets that actually carry a change or are informative
    deltas = [d for d in deltas if d.get("signals") or d.get("added") or d.get("removed") or d.get("changed")]

    agg = aggregate(deltas, cfg)
    corr = explain.correlate(deltas, cfg)
    summary = explain.summarize(deltas, agg, cfg)

    return {
        "schema": "asterguard.drift/1",
        "version_a": dir_a,
        "version_b": dir_b,
        "generated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "mode": "offline",
        "by_facet": {d["facet"]: d for d in deltas},
        "causes": [d for d in deltas if FACET_ROLE.get(d["facet"]) == "cause"],
        "effects": [d for d in deltas if FACET_ROLE.get(d["facet"]) == "effect"],
        "aggregate": agg,
        "links_fired": corr["links_fired"],
        "narrative": corr["narrative"],
        "summary": summary,
        "calibration": {"mode": "offline", "index": None, "trend": None},
    }


def calibrate(report: Dict[str, Any]) -> Dict[str, Any]:
    """Hand the assembled signals to the gateway drift.compare for a calibrated index.

    Best-effort: if the gateway/bearer is not configured or the tool is unavailable,
    the report is returned unchanged except for a degraded calibration note.
    """
    try:
        sys.path.insert(0, _harness_dir())
        from gateway import Gateway  # type: ignore
        gw = Gateway()
        gw.initialize()
        payload = {
            "signals": sorted({s for d in report["by_facet"].values() for s in d.get("signals", [])}),
            "by_facet": {f: {"direction": d["direction"], "magnitude": d["magnitude"]}
                         for f, d in report["by_facet"].items()},
        }
        res = gw.tool(_resolve(gw, "drift.compare", "drift_compare"), payload)
        report["mode"] = "connected"
        report["calibration"] = {
            "mode": "connected",
            "index": (res or {}).get("drift_index"),
            "trend": (res or {}).get("trend"),
            "band": (res or {}).get("band"),
            "audit_id": (res or {}).get("audit_id"),
        }
    except Exception as e:  # gateway absent / tool not deployed yet
        report["calibration"] = {"mode": "degraded", "index": None, "trend": None, "error": str(e)}
    return report


def _harness_dir() -> str:
    import os
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "live-harness")


def _resolve(gw, *suffixes: str) -> str:
    names = [t["name"] for t in (gw._rpc("tools/list", {}) or {}).get("tools", [])]
    for s in suffixes:
        for n in names:
            if n.replace(".", "_").endswith(s.replace(".", "_")):
                return n
    raise RuntimeError(f"gateway exposes no drift.compare (tools: {names})")


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Compose drift across facets between two version snapshots.")
    ap.add_argument("version_a")
    ap.add_argument("version_b")
    ap.add_argument("--connected", action="store_true", help="also fetch the calibrated index from the gateway")
    ap.add_argument("--out", help="write the report JSON to this path")
    args = ap.parse_args(argv)

    report = build_report(args.version_a, args.version_b)
    if args.connected:
        report = calibrate(report)
    if args.out:
        import json
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
    emit(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
