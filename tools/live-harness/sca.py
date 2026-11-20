"""SCA — real software-composition analysis of the target's declared dependencies.

Parses a requirements manifest and queries the OSV advisory database (https://osv.dev) for
each pinned `package==version`, returning the ACTUAL advisories OSV reports — no invented
CVEs, and no building/installing of the (often deliberately old, unbuildable) pins. OSV is
the same data source `pip-audit`/`osv-scanner` use; querying it directly is what lets us audit
a declared manifest without resolving it.

  TARGET_REQUIREMENTS   manifest to scan (default: the bundled demo manifest of vulnerable pins)

Network is required (the OSV API). If it's unreachable, the panel says so rather than guessing.
"""
from __future__ import annotations

import json
import os
import re
import ssl
import urllib.request
from pathlib import Path

import target_profile as profile

OSV_URL = "https://api.osv.dev/v1/query"

try:
    import certifi
    _SSL = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _SSL = ssl.create_default_context()

_PIN = re.compile(r"^\s*([A-Za-z0-9._-]+)\s*==\s*([A-Za-z0-9._+!-]+)\s*$")


def _parse(manifest: str) -> list[tuple[str, str]]:
    pins = []
    for line in Path(manifest).read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        m = _PIN.match(line)
        if m:
            pins.append((m.group(1), m.group(2)))
    return pins


def _osv(name: str, version: str) -> list[dict]:
    body = json.dumps({"version": version, "package": {"name": name, "ecosystem": "PyPI"}}).encode()
    req = urllib.request.Request(OSV_URL, data=body, headers={"content-type": "application/json"})
    data = json.loads(urllib.request.urlopen(req, timeout=20, context=_SSL).read().decode())
    out = []
    for v in data.get("vulns", []):
        fixes = []
        for aff in v.get("affected", []):
            for rng in aff.get("ranges", []):
                for ev in rng.get("events", []):
                    if ev.get("fixed"):
                        fixes.append(ev["fixed"])
        aliases = v.get("aliases", [])
        cve = next((a for a in aliases if a.startswith("CVE-")), v.get("id"))
        ds = v.get("database_specific") or {}
        band = {"CRITICAL": "critical", "HIGH": "high", "MODERATE": "medium",
                "MEDIUM": "medium", "LOW": "low"}.get(str(ds.get("severity") or "").upper(), "unknown")
        out.append({"package": name, "version": version, "id": cve,
                    "aliases": [a for a in aliases if a != cve],
                    "fix_versions": sorted(set(fixes)),
                    "severity": band, "cwes": ds.get("cwe_ids") or [],
                    "description": (v.get("summary") or v.get("details") or "")[:240]})
    return out


def run_sca(requirements: str | None = None) -> dict:
    manifest = requirements or profile.requirements()
    if not manifest:
        return {"ok": True, "scanner": "osv.dev", "package_count": 0, "findings": [],
                "note": "no dependency manifest configured (set TARGET_REQUIREMENTS or a target profile)"}
    if not Path(manifest).is_file():
        return {"ok": False, "reason": f"manifest not found: {manifest}", "findings": []}
    pins = _parse(manifest)
    if not pins:
        return {"ok": False, "reason": "no pinned (name==version) requirements to audit",
                "manifest": manifest, "findings": []}
    findings: list[dict] = []
    seen: set[tuple[str, str]] = set()
    try:
        for name, version in pins:
            for f in _osv(name, version):
                key = (f["package"], f["id"])
                if key in seen:
                    continue
                seen.add(key)
                findings.append(f)
    except Exception as e:
        return {"ok": False, "reason": f"OSV query failed ({e})", "manifest": manifest,
                "scanner": "osv.dev", "findings": []}
    findings.sort(key=lambda f: (f["package"], f["id"]))
    return {"ok": True, "manifest": manifest, "scanner": "osv.dev",
            "package_count": len(pins), "findings": findings}


if __name__ == "__main__":
    import sys
    print(json.dumps(run_sca(sys.argv[1] if len(sys.argv) > 1 else None), indent=2))
