"""Fleet scan — run the free static tier (SCA + SAST) across many repos, then roll up.

The static tier scales: a repo doesn't need to be running to be scanned, so one agent can sweep an
org's repos, score each, and rank them by realized risk. The behavioral tier (subscription) runs only
on the subset that's actually deployed — so a fleet sweep produces static assurance everywhere plus a
shortlist of *which* agents warrant a live red-team.

Enumerate from a GitHub org (`gh repo list`), a file of URLs, a comma list, or local paths.

  python fleet.py Asterguard                 # an org (needs `gh` auth)
  python fleet.py repos.txt                   # one URL/path per line
  python fleet.py /path/a,/path/b             # local checkouts
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

import sast
import sca

Emit = Callable[[dict], None]
_SEV = ("critical", "high", "medium", "low", "unknown")


def enumerate_repos(spec: str) -> list[str]:
    if Path(spec).is_file():
        return [l.strip() for l in Path(spec).read_text().splitlines() if l.strip() and not l.startswith("#")]
    if "," in spec or spec.startswith(("http", "/", ".", "~")):
        return [r.strip() for r in spec.split(",") if r.strip()]
    # bare token → treat as a GitHub org and list via gh
    try:
        out = subprocess.run(["gh", "repo", "list", spec, "--limit", "200", "--json", "url",
                              "-q", ".[].url"], capture_output=True, text=True, timeout=90)
        urls = [l.strip() for l in out.stdout.splitlines() if l.strip()]
        if urls:
            return urls
    except Exception:
        pass
    return [spec]


def _sev_counts(*finding_lists) -> dict:
    sev = {k: 0 for k in _SEV}
    for fl in finding_lists:
        for f in fl or []:
            b = f.get("severity", "unknown")
            sev[b] = sev.get(b, 0) + 1
    return sev


def scan_repo(url_or_path: str, emit: Emit) -> dict | None:
    tmp = None
    repo = url_or_path
    if url_or_path.startswith("http") or url_or_path.endswith(".git"):
        tmp = tempfile.mkdtemp(prefix="fleet-")
        r = subprocess.run(["git", "clone", "--depth", "1", url_or_path, tmp],
                           capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            emit({"type": "repo_error", "repo": url_or_path, "error": r.stderr.strip()[:140]})
            shutil.rmtree(tmp, ignore_errors=True)
            return None
        repo = tmp
    name = url_or_path.rstrip("/").split("/")[-1].replace(".git", "")
    emit({"type": "repo_start", "repo": name})

    req = next((str(Path(repo) / c) for c in ("requirements.txt", "requirements/base.txt")
                if (Path(repo) / c).is_file()), None)
    sca_res = sca.run_sca(req) if req else {"findings": []}
    sast_res = sast.run_sast(repo)
    sev = _sev_counts(sca_res.get("findings"), sast_res.get("findings"))
    rec = {"repo": name, "url": url_or_path,
           "sca": len(sca_res.get("findings", [])), "sast": len(sast_res.get("findings", [])),
           "total": len(sca_res.get("findings", [])) + len(sast_res.get("findings", [])),
           "by_severity": sev,
           "top_sast": [{"cwe": f.get("cwe"), "at": f"{f.get('file')}:{f.get('line')}"}
                        for f in sast_res.get("findings", [])[:5]]}
    emit({"type": "repo_done", "repo": name, "total": rec["total"], "by_severity": sev})
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)
    return rec


def run_fleet(spec: str, emit: Emit) -> list[dict]:
    repos = enumerate_repos(spec)
    emit({"type": "fleet_start", "count": len(repos)})
    results = [r for u in repos if (r := scan_repo(u, emit))]
    results.sort(key=lambda r: (r["by_severity"]["critical"], r["by_severity"]["high"], r["total"]),
                 reverse=True)
    totals = {k: sum(r["by_severity"][k] for r in results) for k in _SEV}
    emit({"type": "fleet_summary", "repos": len(results),
          "findings": sum(r["total"] for r in results), "by_severity": totals,
          "top_risk": [{"repo": r["repo"], "crit": r["by_severity"]["critical"],
                        "high": r["by_severity"]["high"], "total": r["total"]} for r in results[:10]]})
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: fleet.py <org | file | url1,url2 | path1,path2>", file=sys.stderr)
        sys.exit(2)
    out = run_fleet(sys.argv[1], lambda ev: print(json.dumps(ev)))
    Path("fleet-report.json").write_text(json.dumps(out, indent=2))
    print(f"\nfleet-report.json written ({len(out)} repos)", file=sys.stderr)
