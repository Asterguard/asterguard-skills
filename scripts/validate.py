#!/usr/bin/env python3
"""Contract validator for the AsterGuard skills pack — the release safety net.

Fast, hermetic, no model. Fails the build on anything structural so a new feature
cannot silently break the pack:

  - every skills/<name>/SKILL.md: frontmatter parses, `name` matches its dir,
    `description` present and sane, no duplicate skill names;
  - relative file links in a skill resolve on disk (references/, templates/, ...);
  - every playbook step `{skill: X}` names a real skill (`lens:` steps ignored);
  - every persona `related:` entry is a real skill or persona;
  - mcp.json is valid JSON; tools/drift/signals.yaml loads under BOTH PyYAML and the
    built-in fallback parser and agrees;
  - external links (incl. the README's film links) resolve — a WARNING by default,
    an ERROR under --strict.

Exit code: 1 if any ERROR (or any WARNING under --strict), else 0.

Usage:  python scripts/validate.py [--offline] [--strict]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import sys
import urllib.request
from typing import Dict, List, Tuple

# Verify TLS against certifi's CA bundle when available (macOS pythons often lack a
# system CA store), else the platform default. Never disables verification.
try:
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _SSL_CTX = ssl.create_default_context()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")
PLAYBOOKS = os.path.join(ROOT, "playbooks")
PERSONAS = os.path.join(ROOT, "personas")

ISSUES: List[Tuple[str, str, str]] = []  # (level, where, message)


def err(where: str, msg: str) -> None:
    ISSUES.append(("ERROR", where, msg))


def warn(where: str, msg: str) -> None:
    ISSUES.append(("WARN", where, msg))


# --------------------------------------------------------------------------- #
# frontmatter (no YAML dep — simple key: value, with folded continuations)
# --------------------------------------------------------------------------- #
def read_frontmatter(path: str) -> Dict[str, object]:
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    body = text[3:end].strip("\n")
    out: Dict[str, object] = {}
    key = None
    for line in body.splitlines():
        m = re.match(r"^([A-Za-z0-9_]+):\s?(.*)$", line)
        if m and not line.startswith(" ") and not line.startswith("\t"):
            key, val = m.group(1), m.group(2).strip()
            if val.startswith("- "):  # inline start of a list is unusual; treat as list
                out[key] = [val[2:].strip()]
            else:
                out[key] = val
        elif line.strip().startswith("- ") and key:
            out.setdefault(key, [])
            if isinstance(out[key], list):
                out[key].append(line.strip()[2:].strip())
            else:
                out[key] = [out[key], line.strip()[2:].strip()] if out[key] else [line.strip()[2:].strip()]
        elif key and line.strip() and isinstance(out.get(key), str):
            out[key] = (str(out[key]) + " " + line.strip()).strip()  # folded continuation
    return out


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #
def check_skills() -> set:
    names = set()
    seen: Dict[str, str] = {}
    for d in sorted(os.listdir(SKILLS)):
        sdir = os.path.join(SKILLS, d)
        if not os.path.isdir(sdir):
            continue
        skill_md = os.path.join(sdir, "SKILL.md")
        if not os.path.isfile(skill_md):
            err(f"skills/{d}", "missing SKILL.md")
            continue
        names.add(d)
        fm = read_frontmatter(skill_md)
        if not fm:
            err(f"skills/{d}/SKILL.md", "missing or malformed frontmatter")
            continue
        name = fm.get("name")
        if name != d:
            err(f"skills/{d}/SKILL.md", f"frontmatter name {name!r} != directory {d!r}")
        desc = str(fm.get("description", "") or "")
        if not desc:
            err(f"skills/{d}/SKILL.md", "frontmatter has no description")
        elif len(desc) < 20:
            warn(f"skills/{d}/SKILL.md", f"description very short ({len(desc)} chars)")
        elif len(desc) > 1024:
            warn(f"skills/{d}/SKILL.md", f"description very long ({len(desc)} chars)")
        if name in seen:
            err(f"skills/{d}/SKILL.md", f"duplicate skill name {name!r} (also skills/{seen[name]})")
        elif name:
            seen[str(name)] = d
        check_relative_links(skill_md, sdir)
    return names


_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def check_relative_links(md_path: str, base_dir: str) -> None:
    with open(md_path, "r", encoding="utf-8") as fh:
        text = fh.read()
    rel = os.path.relpath(md_path, ROOT)
    for target in _LINK.findall(text):
        t = target.strip().split()[0]  # drop any "title"
        if t.startswith(("http://", "https://", "#", "mailto:", "tel:")):
            continue
        t = t.split("#")[0].split("?")[0]
        if not t:
            continue
        cand = os.path.normpath(os.path.join(base_dir, t))
        cand_root = os.path.normpath(os.path.join(ROOT, t.lstrip("/")))
        if not (os.path.exists(cand) or os.path.exists(cand_root)):
            err(rel, f"broken relative link -> {t}")


def check_playbooks(skill_names: set, have_yaml: bool) -> None:
    if not os.path.isdir(PLAYBOOKS):
        return
    for f in sorted(os.listdir(PLAYBOOKS)):
        if not f.endswith((".yaml", ".yml")):
            continue
        path = os.path.join(PLAYBOOKS, f)
        if not have_yaml:
            warn(f"playbooks/{f}", "skipped skill-reference check (PyYAML not installed)")
            continue
        import yaml  # type: ignore
        try:
            with open(path, "r", encoding="utf-8") as fh:
                doc = yaml.safe_load(fh)
        except Exception as e:
            err(f"playbooks/{f}", f"YAML parse error: {e}")
            continue
        for step in (doc or {}).get("steps", []) or []:
            if isinstance(step, dict) and "skill" in step:
                s = step["skill"]
                if s not in skill_names:
                    err(f"playbooks/{f}", f"references unknown skill {s!r}")


def check_personas(skill_names: set) -> None:
    if not os.path.isdir(PERSONAS):
        return
    persona_names = {os.path.splitext(p)[0] for p in os.listdir(PERSONAS) if p.endswith(".md")}
    for p in sorted(os.listdir(PERSONAS)):
        if not p.endswith(".md"):
            continue
        fm = read_frontmatter(os.path.join(PERSONAS, p))
        related = fm.get("related", [])
        if isinstance(related, str):
            related = [related]
        for r in related or []:
            r = str(r).strip()
            if r and r not in skill_names and r not in persona_names:
                err(f"personas/{p}", f"related entry {r!r} is neither a skill nor a persona")


def check_mcp_json() -> None:
    path = os.path.join(ROOT, "mcp.json")
    if not os.path.isfile(path):
        warn("mcp.json", "not found")
        return
    try:
        with open(path, "r", encoding="utf-8") as fh:
            json.load(fh)
    except Exception as e:
        err("mcp.json", f"invalid JSON: {e}")


def check_signals_ssot(have_yaml: bool) -> None:
    sig_path = os.path.join(ROOT, "tools", "drift", "signals.yaml")
    if not os.path.isfile(sig_path):
        return  # drift toolkit not on this branch
    sys.path.insert(0, os.path.join(ROOT, "tools", "drift"))
    try:
        import common  # type: ignore
    except Exception as e:
        err("tools/drift/signals.yaml", f"cannot import common.py: {e}")
        return
    with open(sig_path, "r", encoding="utf-8") as fh:
        text = fh.read()
    mini = common._mini_yaml(text)
    for key in ("signals", "links", "bands"):
        if key not in mini:
            err("tools/drift/signals.yaml", f"fallback parser produced no {key!r}")
    if have_yaml:
        import yaml  # type: ignore
        real = yaml.safe_load(text)
        if len(real.get("signals", {})) != len(mini.get("signals", {})):
            err("tools/drift/signals.yaml",
                f"PyYAML and fallback disagree on signal count "
                f"({len(real.get('signals', {}))} vs {len(mini.get('signals', {}))})")


_URL = re.compile(r"https?://[^\s)\]\"'>]+")


def check_external_links(offline: bool) -> None:
    if offline:
        return
    readme = os.path.join(ROOT, "README.md")
    if not os.path.isfile(readme):
        return
    with open(readme, "r", encoding="utf-8") as fh:
        urls = sorted(set(_URL.findall(fh.read())))
    for url in urls:
        url = url.rstrip(".,")
        try:
            req = urllib.request.Request(
                url, method="HEAD", headers={"User-Agent": "asterguard-ci/1.0"})
            with urllib.request.urlopen(req, timeout=10, context=_SSL_CTX) as resp:
                if resp.status >= 400:
                    warn("README.md", f"link {url} -> HTTP {resp.status}")
        except Exception as e:
            warn("README.md", f"link {url} unreachable ({type(e).__name__})")


# --------------------------------------------------------------------------- #
def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Validate the skills pack contracts.")
    ap.add_argument("--offline", action="store_true", help="skip external link checks")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = ap.parse_args(argv)

    try:
        import yaml  # noqa: F401
        have_yaml = True
    except Exception:
        have_yaml = False

    skill_names = check_skills()
    check_playbooks(skill_names, have_yaml)
    check_personas(skill_names)
    check_mcp_json()
    check_signals_ssot(have_yaml)
    check_external_links(args.offline)

    errors = [i for i in ISSUES if i[0] == "ERROR"]
    warns = [i for i in ISSUES if i[0] == "WARN"]
    for level, where, msg in ISSUES:
        print(f"{level:5}  {where}: {msg}")
    print(f"\nvalidated {len(skill_names)} skills — {len(errors)} error(s), {len(warns)} warning(s)")
    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
