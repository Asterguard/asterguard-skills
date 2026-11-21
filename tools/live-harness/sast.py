"""SAST — static analysis of the target repo (the free analysis tier).

Prefers **semgrep** with the bundled local ruleset (`semgrep-rules.yaml`, no registry/login needed);
falls back to a dependency-free grounded regex ruleset with the same finding shape. Every hit is an
actual match in the code (file:line + CWE); nothing is invented. In the product the gateway serves
framework-profiled semgrep packs via `rules.fetch` and the engine runs those identically.

  TARGET_REPO   path to the repo to scan (default: current dir)
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

SKIP_DIRS = {".venv", ".git", "__pycache__", "node_modules", ".asterguard", "dist", "build"}
SEMGREP_RULES = Path(__file__).resolve().parent / "semgrep-rules.yaml"
_SEV = {"ERROR": "high", "WARNING": "medium", "INFO": "low"}

GROUNDED_RULES = [
    {"id": "py.sqli.string-concat", "cwe": "CWE-89", "severity": "high",
     "re": re.compile(r"(?i)\b(SELECT|INSERT|UPDATE|DELETE|WHERE|LIKE)\b.*(\"\s*\+|\+\s*\"|'\s*\+|\+\s*')"),
     "msg": "SQL built with string concatenation — injection risk"},
    {"id": "py.exec.dynamic", "cwe": "CWE-95", "severity": "critical",
     "re": re.compile(r"\b(eval|exec)\s*\("), "msg": "Dynamic code execution (eval/exec)"},
    {"id": "py.subprocess.shell", "cwe": "CWE-78", "severity": "high",
     "re": re.compile(r"subprocess\.\w+\([^)]*shell\s*=\s*True"), "msg": "Command injection risk (shell=True)"},
    {"id": "py.tls.verify-disabled", "cwe": "CWE-295", "severity": "medium",
     "re": re.compile(r"\bverify\s*=\s*False\b"), "msg": "TLS certificate verification disabled"},
    {"id": "agent.pii-masking-off", "cwe": "CWE-359", "severity": "high",
     "re": re.compile(r"mask_pii\s*[:=][^=].*False"), "msg": "PII masking disabled on tool results"},
    {"id": "agent.tool-approval-off", "cwe": "CWE-862", "severity": "medium",
     "re": re.compile(r"require_tool_approval\s*[:=][^=].*False"), "msg": "Human approval gate disabled"},
    {"id": "web.route.unauth-sensitive", "cwe": "CWE-306", "severity": "high",
     "re": re.compile(r"""@\w+\.(?:get|post|route)\(\s*["'][^"']*(?:admin|export|debug|dump|internal)""", re.I),
     "msg": "Sensitive route — confirm authentication/authorization"},
    {"id": "egress.unbounded-post", "cwe": "CWE-200", "severity": "medium",
     "re": re.compile(r"requests\.(post|put)\("), "msg": "Outbound POST/PUT — confirm egress allowlist"},
]
_SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _cwe(md: dict) -> str:
    c = md.get("cwe")
    if isinstance(c, list):
        c = c[0] if c else ""
    return str(c or "").split(":")[0].strip()


def _semgrep(root: Path) -> dict | None:
    exe = shutil.which("semgrep")
    if not exe or not SEMGREP_RULES.is_file():
        return None
    try:
        proc = subprocess.run(
            [exe, "--config", str(SEMGREP_RULES), "--json", "--quiet", "--disable-version-check", str(root)],
            capture_output=True, text=True, timeout=240)
        data = json.loads(proc.stdout or "{}")
    except Exception:
        return None
    findings = []
    for r in data.get("results", []):
        e = r.get("extra", {})
        try:
            rel = str(Path(r.get("path", "")).resolve().relative_to(root.resolve()))
        except ValueError:
            rel = r.get("path", "")
        ln = (r.get("start") or {}).get("line")
        # semgrep redacts matched lines to "requires login" without an account — read the file instead
        snippet = (e.get("lines") or "").strip()
        if not snippet or snippet == "requires login":
            try:
                snippet = Path(r.get("path", "")).read_text(errors="replace").splitlines()[ln - 1].strip()
            except Exception:
                snippet = (e.get("message") or "").strip()
        findings.append({"id": r.get("check_id", "").split(".")[-1],
                         "cwe": _cwe(e.get("metadata", {})),
                         "severity": _SEV.get(e.get("severity", "WARNING"), "medium"),
                         "file": rel, "line": ln,
                         "message": (e.get("message") or "").strip()[:160],
                         "snippet": snippet[:160]})
    findings.sort(key=lambda f: (_SEV_ORDER.get(f["severity"], 9), f["file"], f["line"] or 0))
    scanned = len((data.get("paths") or {}).get("scanned") or [])
    return {"ok": True, "scanner": "semgrep", "root": str(root),
            "files_scanned": scanned, "findings": findings}


def _grounded(root: Path) -> dict:
    findings, files = [], 0
    for p in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        files += 1
        try:
            lines = p.read_text(errors="replace").splitlines()
        except OSError:
            continue
        rel = str(p.relative_to(root))
        for i, line in enumerate(lines, 1):
            if line.lstrip().startswith("#"):
                continue
            for rule in GROUNDED_RULES:
                if rule["re"].search(line):
                    findings.append({"id": rule["id"], "cwe": rule["cwe"], "severity": rule["severity"],
                                     "file": rel, "line": i, "message": rule["msg"],
                                     "snippet": line.strip()[:160]})
    findings.sort(key=lambda f: (_SEV_ORDER.get(f["severity"], 9), f["file"], f["line"]))
    return {"ok": True, "scanner": "grounded-rules", "root": str(root),
            "files_scanned": files, "findings": findings}


def run_sast(repo: str | None = None) -> dict:
    root = Path(repo or os.environ.get("TARGET_REPO") or ".")
    if not root.exists():
        return {"ok": False, "reason": f"repo not found: {root}", "findings": []}
    return _semgrep(root) or _grounded(root)


if __name__ == "__main__":
    import sys
    print(json.dumps(run_sast(sys.argv[1] if len(sys.argv) > 1 else None), indent=2))
