"""Artifacts — the engagement's evidence, aggregated from LOCAL scan data (nothing hand-entered).

Sources:
  - AI-BOM / Security-graph components : a scan of the AI system in use (models from the
        engagement store + env, frameworks detected in the runtime, gateway, agent, tools)
  - Supply chain                       : the installed Python distributions in the target runtime
  - Findings / Security-graph weaknesses: the live OSV SCA (component CVEs + CWEs) PLUS the
        behavioral findings persisted by the offensive runs (store.py / SQLite)
  - Archived reviews                   : every engagement the harness has run, from the store

  TARGET_TOOLS   optional comma list of the target agent's tool names (default: the demo's)
"""
from __future__ import annotations

import importlib.metadata
import os
from urllib.parse import urlparse

import dast
import sast
import sca
import store
import target_profile as profile

FRAMEWORK_PKGS = ["langgraph", "langchain-core", "langchain-openai", "openai",
                  "fastapi", "uvicorn", "pydantic", "langchain"]


def _host(url: str) -> str:
    try:
        return urlparse(url if "//" in url else "//" + url).hostname or url
    except ValueError:
        return url


def _frameworks() -> list[dict]:
    out = []
    for name in FRAMEWORK_PKGS:
        try:
            out.append({"name": name, "version": importlib.metadata.version(name)})
        except importlib.metadata.PackageNotFoundError:
            pass
    return out


def ai_bom(engagements: list[dict]) -> dict:
    last = engagements[0] if engagements else {}
    items: list[dict] = []
    dm = os.environ.get("DEFENDER_MODEL") or last.get("defender_model") or ""
    am = os.environ.get("ATTACKER_MODEL") or last.get("attacker_model") or ""
    if dm:
        items.append({"type": "model", "name": f"defender · {dm}"})
    if am:
        items.append({"type": "model", "name": f"attacker · {am}"})
    for f in _frameworks():
        items.append({"type": "framework", "name": f"{f['name']} {f['version']}"})
    items.append({"type": "agent", "name": _host(os.environ.get("TARGET_INVOKE_URL", "target"))})
    items.append({"type": "gateway", "name": _host(os.environ.get("ASTERVAULT_MCP_URL", "astervault"))})
    for t in profile.tools():
        items.append({"type": "tool", "name": t})
    return {"count": len(items), "items": items}


def supply_chain() -> dict:
    pkgs = sorted({d.metadata["Name"] for d in importlib.metadata.distributions()
                   if d.metadata.get("Name")})
    return {"count": len(pkgs), "packages": pkgs,
            "note": "installed Python distributions in the target runtime"}


def findings(engagements: list[dict], scan: dict, sast_res: dict, dast_res: dict) -> dict:
    sev = {"critical": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0}
    for src in (scan, sast_res, dast_res):
        for f in src.get("findings", []):
            b = f.get("severity", "unknown")
            sev[b] = sev.get(b, 0) + 1
    behavioral = []
    for e in engagements:
        if e.get("verdict") == "broke":
            band = (e.get("ars") or {}).get("band") or "high"
            sev[band] = sev.get(band, 0) + 1
            behavioral.append({"id": e["id"], "band": band,
                               "weakness": (e.get("weakness") or {}).get("weakness_id")})
    sca_n, sast_n, dast_n = (len(scan.get("findings", [])), len(sast_res.get("findings", [])),
                             len(dast_res.get("findings", [])))
    return {"crit": sev["critical"], "high": sev["high"], "medium": sev["medium"],
            "low": sev["low"], "unknown": sev["unknown"],
            "total": sca_n + sast_n + dast_n + len(behavioral),
            "sca": sca_n, "sast": sast_n, "dast": dast_n, "behavioral": len(behavioral),
            "by_severity": sev}


def security_graph(bom: dict, scan: dict, sast_res: dict, dast_res: dict, engagements: list[dict]) -> dict:
    cwes = set()
    for src in (scan, sast_res, dast_res):
        for f in src.get("findings", []):
            cwes.update(f.get("cwes", []) or ([f["cwe"]] if f.get("cwe") else []))
    runtime_weaknesses = sorted({(e.get("weakness") or {}).get("weakness_id")
                                 for e in engagements if (e.get("weakness") or {}).get("weakness_id")})
    return {"components": bom["count"] + 6,  # + the trifecta data-flow nodes
            "weaknesses": len(cwes) + len(runtime_weaknesses),
            "cwes": sorted(cwes), "runtime_weaknesses": runtime_weaknesses}


def archived_reviews(engagements: list[dict]) -> dict:
    return {"count": len(engagements),
            "items": [{"id": e["id"], "verdict": e.get("verdict"), "objective": e.get("objective"),
                       "asr": e.get("asr_value"), "attacker": e.get("attacker_model"),
                       "ts": e.get("ts")} for e in engagements[:25]]}


def summary() -> dict:
    eng = store.all_engagements()
    scan = sca.run_sca()
    sast_res = sast.run_sast()
    dast_res = dast.run_dast()
    bom = ai_bom(eng)
    return {
        "ai_bom": bom,
        "supply_chain": supply_chain(),
        "security_graph": security_graph(bom, scan, sast_res, dast_res, eng),
        "findings": findings(eng, scan, sast_res, dast_res),
        "archived_reviews": archived_reviews(eng),
        "sca_ok": scan.get("ok", False),
    }
