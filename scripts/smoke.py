#!/usr/bin/env python3
"""Offline smoke test — the one command to run before you push.

Hermetic: no model, no gateway, no network, no secrets. It is the single source of
truth for "is the pack still sound?" and is exactly what CI runs on every PR. It bundles
three gates so a new feature cannot silently break the pack:

  1. contract validation   — scripts/validate.py --offline (skills, playbooks, personas,
                             links on disk, mcp.json, signals.yaml SSOT agreement);
  2. tool unit tests        — the deterministic tools' own unittest suites (drift today);
  3. pipeline smoke         — run the drift composer end-to-end on the committed
                             v1 -> v2 fixture and assert the report is shaped and sane
                             (a known regression is detected: direction worse, causes and
                             effects present, cause->effect links fire).

Each gate is skipped cleanly (not failed) when its inputs are absent on this ref, so the
script stays correct as tools come and go.

Exit code: 0 if every present gate passes, 1 otherwise.

Usage:  python scripts/smoke.py [-v]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIFT = os.path.join(ROOT, "tools", "drift")
FIX = os.path.join(DRIFT, "tests", "fixtures")

RESULTS: list[tuple[str, str, str]] = []  # (gate, status PASS|FAIL|SKIP, detail)


def record(gate: str, status: str, detail: str = "") -> None:
    RESULTS.append((gate, status, detail))
    mark = {"PASS": "ok  ", "FAIL": "FAIL", "SKIP": "skip"}[status]
    print(f"  [{mark}] {gate}" + (f" — {detail}" if detail else ""))


# --------------------------------------------------------------------------- #
# gate 1 — contract validator (hermetic: --offline)
# --------------------------------------------------------------------------- #
def gate_validate(verbose: bool) -> None:
    script = os.path.join(ROOT, "scripts", "validate.py")
    if not os.path.isfile(script):
        record("contract validator", "SKIP", "scripts/validate.py not present")
        return
    proc = subprocess.run([sys.executable, script, "--offline"],
                          cwd=ROOT, capture_output=True, text=True)
    if verbose or proc.returncode != 0:
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
    record("contract validator", "PASS" if proc.returncode == 0 else "FAIL",
           (proc.stdout.strip().splitlines() or ["no output"])[-1])


# --------------------------------------------------------------------------- #
# gate 2 — tool unit tests
# --------------------------------------------------------------------------- #
def gate_unit_tests(verbose: bool) -> None:
    tests_dir = os.path.join(DRIFT, "tests")
    if not os.path.isdir(tests_dir):
        record("drift unit tests", "SKIP", "tools/drift/tests not present")
        return
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", tests_dir, "-v" if verbose else "-q"],
        cwd=ROOT, capture_output=True, text=True)
    if verbose or proc.returncode != 0:
        sys.stderr.write(proc.stderr)
    # unittest prints its summary to stderr
    last = (proc.stderr.strip().splitlines() or ["no output"])[-1]
    record("drift unit tests", "PASS" if proc.returncode == 0 else "FAIL", last)


# --------------------------------------------------------------------------- #
# gate 3 — end-to-end pipeline smoke on the committed fixture
# --------------------------------------------------------------------------- #
def gate_drift_pipeline(verbose: bool) -> None:
    composer = os.path.join(DRIFT, "drift.py")
    v1, v2 = os.path.join(FIX, "v1"), os.path.join(FIX, "v2")
    if not (os.path.isfile(composer) and os.path.isdir(v1) and os.path.isdir(v2)):
        record("drift pipeline smoke", "SKIP", "drift composer or fixtures not present")
        return
    sys.path.insert(0, DRIFT)
    try:
        import drift  # type: ignore
        report = drift.build_report(v1, v2)
    except Exception as e:  # import or run failure is a hard fail
        record("drift pipeline smoke", "FAIL", f"{type(e).__name__}: {e}")
        return

    checks = {
        "schema": report.get("schema") == "asterguard.drift/1",
        "offline mode": report.get("calibration", {}).get("mode") == "offline",
        "regression detected (direction worse)": report.get("aggregate", {}).get("direction") == "worse",
        "magnitude > 0": float(report.get("aggregate", {}).get("magnitude", 0)) > 0,
        "cause facets present": bool(report.get("causes")),
        "effect facets present": bool(report.get("effects")),
        "cause->effect link fired": bool(report.get("links_fired")),
        "narrative emitted": bool(report.get("narrative")),
    }
    failed = [name for name, ok in checks.items() if not ok]
    if verbose:
        agg = report.get("aggregate", {})
        print(f"       aggregate: {agg.get('direction')} / {agg.get('band')} / mag={agg.get('magnitude')}"
              f" · {len(report.get('links_fired', []))} link(s) fired")
    record("drift pipeline smoke", "PASS" if not failed else "FAIL",
           "all report invariants hold" if not failed else "broken: " + ", ".join(failed))


# --------------------------------------------------------------------------- #
def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Hermetic pre-push smoke for the skills pack.")
    ap.add_argument("-v", "--verbose", action="store_true", help="show each gate's full output")
    args = ap.parse_args(argv)

    print("smoke — hermetic gates (no model, no gateway, no network)\n")
    gate_validate(args.verbose)
    gate_unit_tests(args.verbose)
    gate_drift_pipeline(args.verbose)

    passed = [r for r in RESULTS if r[1] == "PASS"]
    failed = [r for r in RESULTS if r[1] == "FAIL"]
    skipped = [r for r in RESULTS if r[1] == "SKIP"]
    print(f"\n{len(passed)} passed, {len(failed)} failed, {len(skipped)} skipped")
    if failed:
        print("FAILED: " + ", ".join(g for g, _, _ in failed))
        return 1
    print("smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
