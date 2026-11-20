"""Target profile — describes the app under test, so the harness is a generic library.

Nothing about a specific application is baked into the engines. A target is described by a JSON
profile (its tool list, data-flow graph, how to plant a canary, which manifest to scan, which paths
to probe). The library ships neutral generic defaults; point TARGET_PROFILE at a profile to describe
your app. The bundled `targets/support-agent-demo.json` is one example profile, not a default.

Machine-specific LOCATIONS stay in the environment (invoke URL, DB path, repo path, egress log,
bearer, gateway URL) — the profile is the app's STRUCTURE, the env is where it runs.

  TARGET_PROFILE   path to a target profile JSON (optional)
"""
from __future__ import annotations

import json
import os
from pathlib import Path

# A generic trifecta skeleton used when no profile is supplied — the shape applies to any agent.
GENERIC_DATAFLOW = {
    "nodes": [
        {"id": "turn", "label": "untrusted turn", "sub": "user / tool input", "kind": "source"},
        {"id": "data", "label": "private data", "sub": "records + canary", "kind": "source"},
        {"id": "agent", "label": "agent", "sub": "model + tools", "kind": "agent"},
        {"id": "tool", "label": "tool", "sub": "reads private data", "kind": "tool"},
        {"id": "sink", "label": "external sink", "sub": "egress", "kind": "sink"},
    ],
    "edges": [
        {"from": "turn", "to": "agent", "label": "instructs", "leg": "untrusted-input"},
        {"from": "data", "to": "tool", "label": "reads", "leg": "private-data"},
        {"from": "agent", "to": "tool", "label": "calls"},
        {"from": "tool", "to": "sink", "label": "sends", "leg": "egress"},
    ],
}
GENERIC_SENSITIVE_PATHS = ["/admin", "/admin/export", "/debug", "/export", "/dump",
                           "/internal", "/.env", "/actuator/env"]


def load() -> dict:
    p = os.environ.get("TARGET_PROFILE")
    if p and Path(p).is_file():
        try:
            return json.loads(Path(p).read_text())
        except (ValueError, OSError):
            pass
    return {}


PROFILE = load()


def get(key: str, default=None):
    return PROFILE.get(key, default)


def tools() -> list[str]:
    env = os.environ.get("TARGET_TOOLS")
    if env:
        return [t.strip() for t in env.split(",") if t.strip()]
    return list(PROFILE.get("tools") or [])


def dataflow() -> dict:
    p = os.environ.get("TARGET_DATAFLOW")
    if p and Path(p).is_file():
        try:
            return json.loads(Path(p).read_text())
        except (ValueError, OSError):
            pass
    return PROFILE.get("dataflow") or GENERIC_DATAFLOW


def sensitive_paths() -> list[str]:
    return list(PROFILE.get("sensitive_paths") or GENERIC_SENSITIVE_PATHS)


def plant_config() -> dict:
    """{kind, table, column, row_id}. kind 'none' = canary registered at the gateway only."""
    cfg = dict(PROFILE.get("plant") or {})
    cfg.setdefault("kind", "sqlite" if os.environ.get("TARGET_DB") else "none")
    cfg.setdefault("table", os.environ.get("TARGET_PLANT_TABLE", "customers"))
    cfg.setdefault("column", os.environ.get("TARGET_PLANT_COLUMN", "bank_account"))
    cfg.setdefault("row_id", os.environ.get("TARGET_PLANT_ROW_ID", "1"))
    return cfg


def requirements() -> str | None:
    """Manifest to scan for SCA: env, else profile, else the target repo's own requirements.txt."""
    env = os.environ.get("TARGET_REQUIREMENTS")
    if env:
        return env
    if PROFILE.get("requirements"):
        base = Path(os.environ["TARGET_PROFILE"]).resolve().parent if os.environ.get("TARGET_PROFILE") else Path(".")
        cand = (base / PROFILE["requirements"])
        return str(cand if cand.is_file() else PROFILE["requirements"])
    repo = os.environ.get("TARGET_REPO")
    if repo and (Path(repo) / "requirements.txt").is_file():
        return str(Path(repo) / "requirements.txt")
    return None
