"""DAST — live dynamic probes against the running target (the free analysis tier).

Read-only probes against the target's HTTP surface: unauthenticated data endpoints, attack-surface
exposure via the OpenAPI doc, and error-based info leaks. Every finding is an actual observed
response (status + evidence), never inferred. Safe by construction — GETs plus one malformed POST;
no state-changing requests.

  TARGET_BASE_URL   base to probe (default: TARGET_INVOKE_URL with the path stripped)
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from urllib.parse import urlparse

import target_profile as profile


def _base() -> str:
    b = os.environ.get("TARGET_BASE_URL")
    if b:
        return b.rstrip("/")
    inv = os.environ.get("TARGET_INVOKE_URL", "http://127.0.0.1:8097/invoke")
    u = urlparse(inv)
    return f"{u.scheme}://{u.netloc}"


def _get(url: str, timeout: int = 6):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={"accept": "*/*"}), timeout=timeout)
        return r.status, r.headers.get("Content-Type", ""), r.read(20000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", "") if e.headers else "", ""
    except Exception:
        return None, "", ""


def run_dast(base: str | None = None) -> dict:
    base = (base or _base()).rstrip("/")
    paths = profile.sensitive_paths()
    findings = []

    # 1) unauthenticated data endpoints
    for path in paths:
        status, ctype, body = _get(base + path)
        if status == 200 and body:
            looks_data = ("json" in ctype.lower()) or body.lstrip()[:1] in "[{"
            if looks_data and len(body) > 80:
                findings.append({
                    "id": "dast.unauth-data-endpoint", "cwe": "CWE-306", "severity": "high",
                    "path": path, "status": 200,
                    "evidence": f"200 + {len(body)}B of {ctype or 'data'} with no auth",
                    "message": f"Unauthenticated data endpoint {path} returns data"})

    # 2) attack-surface exposure via OpenAPI
    status, ctype, body = _get(base + "/openapi.json")
    if status == 200 and body:
        try:
            paths = list((json.loads(body).get("paths") or {}).keys())
        except ValueError:
            paths = []
        risky = [p for p in paths if any(k in p.lower() for k in ("admin", "export", "debug", "internal"))]
        if risky:
            findings.append({
                "id": "dast.exposed-sensitive-routes", "cwe": "CWE-200", "severity": "medium",
                "path": "/openapi.json", "status": 200,
                "evidence": ", ".join(risky[:6]),
                "message": "OpenAPI advertises sensitive routes in the attack surface"})

    # 3) error-based info leak (one malformed POST to /invoke)
    inv = os.environ.get("TARGET_INVOKE_URL", base + "/invoke")
    try:
        req = urllib.request.Request(inv, data=b"{not-json", headers={"content-type": "application/json"})
        urllib.request.urlopen(req, timeout=6)
    except urllib.error.HTTPError as e:
        body = e.read(8000).decode("utf-8", "replace") if e.fp else ""
        if e.code >= 500 and ("Traceback" in body or "File \"" in body):
            findings.append({
                "id": "dast.error-stacktrace-leak", "cwe": "CWE-209", "severity": "medium",
                "path": urlparse(inv).path, "status": e.code,
                "evidence": "500 response includes a Python traceback",
                "message": "Server error leaks a stack trace to the client"})
    except Exception:
        pass

    sev = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings.sort(key=lambda f: sev.get(f["severity"], 9))
    reachable = any(_get(base + "/openapi.json")[0] is not None for _ in [0]) or bool(findings)
    return {"ok": True, "base": base, "reachable": reachable,
            "probes": len(paths) + 2, "findings": findings}


if __name__ == "__main__":
    import sys
    print(json.dumps(run_dast(sys.argv[1] if len(sys.argv) > 1 else None), indent=2))
