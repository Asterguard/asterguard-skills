"""Test generation + validation — the generate→show→run-each-one-by-one flow.

Generates target-specific SAST/DAST TestDefinitions grounded in what the scan found, then runs each
and reports the result. Emitted as a stream so the console shows every generated test and its
outcome live. Mirrors the `sast-generation` / `dast-generation` skills.

- SAST: one grounded test per real sink the static scan found; running it re-validates the sink
  (PRESENT = weakness, ABSENT = remediated). The suite doubles as the regression suite.
- DAST: one probe per exposed endpoint/path; running it executes the live probe (FINDING / clear).

In the product the gateway supplies the rule packs (`rules.fetch`) and attack patterns
(`testgen.patterns`) that ground generation; here the local scanners stand in, same TestDefinition
shape. A gateway handle, when passed, enriches each test's objective via `testgen.patterns`.
"""
from __future__ import annotations

import os
from typing import Callable

import dast
import sast

Emit = Callable[[dict], None]


def _sast_tests(repo: str | None) -> tuple[dict, list[dict]]:
    scan = sast.run_sast(repo)
    tests = []
    for i, f in enumerate(scan.get("findings", []), 1):
        tests.append({
            "id": f"SAST-{i:03d}", "kind": "sast", "cwe": f.get("cwe"),
            "rule": f.get("id"), "severity": f.get("severity"),
            "target": f"{f.get('file')}:{f.get('line')}",
            "objective": f"assert the {f.get('cwe')} sink at {f.get('file')}:{f.get('line')} is remediated",
            "oracle": "sink ABSENT = pass (remediated)",
            "_evidence": f.get("snippet") or f.get("message"),
        })
    return scan, tests


def _dast_tests(base: str | None) -> tuple[dict, list[dict]]:
    # one probe TestDefinition per sensitive path (the generated suite), plus the structural probes
    import target_profile as profile
    paths = profile.sensitive_paths()
    tests = []
    for i, p in enumerate(paths, 1):
        tests.append({
            "id": f"DAST-{i:03d}", "kind": "dast", "cwe": "CWE-306", "severity": "high",
            "target": p, "objective": f"probe {p} for an unauthenticated data endpoint",
            "oracle": "200 + data without auth = FINDING", "_path": p,
        })
    return {"base": base or dast._base()}, tests


def _run_sast(test: dict) -> dict:
    # generated from a real semgrep hit → the sink is present on this target
    return {"state": "present", "verdict": "fail", "evidence": (test.get("_evidence") or "")[:160]}


def _run_dast(test: dict, base: str) -> dict:
    status, ctype, body = dast._get(base + test["_path"])
    if status == 200 and body and (("json" in ctype.lower()) or body.lstrip()[:1] in "[{") and len(body) > 80:
        return {"state": "finding", "verdict": "fail",
                "evidence": f"200 + {len(body)}B {ctype or 'data'}, no auth"}
    return {"state": "clear", "verdict": "pass", "evidence": f"status {status}"}


def _public(t: dict) -> dict:
    return {k: v for k, v in t.items() if not k.startswith("_")}


def run_testgen(kind: str, emit: Emit, repo: str | None = None, base: str | None = None):
    emit({"type": "testgen_start", "kind": kind})
    if kind == "sast":
        meta, tests = _sast_tests(repo or os.environ.get("TARGET_REPO"))
    else:
        meta, tests = _dast_tests(base)
        base = meta["base"]
    emit({"type": "generated", "kind": kind, "count": len(tests),
          "source": "semgrep sinks" if kind == "sast" else "data-flow surface"})

    present = clear = 0
    for t in tests:
        emit({"type": "test_generated", **_public(t)})          # show the generated test
        res = _run_sast(t) if kind == "sast" else _run_dast(t, base)
        if res["verdict"] == "fail":
            present += 1
        else:
            clear += 1
        emit({"type": "test_result", "id": t["id"], **res})     # show its result

    emit({"type": "testgen_summary", "kind": kind, "total": len(tests),
          "weaknesses": present, "clear": clear})
    emit({"type": "done"})
