"""Shared contract for the drift toolkit.

Every comparator (prompt_drift, tool_drift, controls_drift, behavior_drift,
surface_drift, model_drift, sbom_drift, ...) returns the SAME typed `Delta`:

    {
      "facet":     "prompt|tools|controls|behavior|surface|model|sbom",
      "added":     [...],            # items present only in version B
      "removed":   [...],            # items present only in version A
      "changed":   [{"from":...,"to":...}, ...],
      "signals":   ["weakened_guardrail", ...],   # typed; defined in signals.yaml
      "direction": "worse|better|neutral",        # security-signed, from signals.yaml
      "magnitude": 0.0,                            # 0..1, summed signal weight
      "evidence":  [...]                           # inspectable per-signal detail
    }

The security meaning of each signal (direction + weight) lives ONLY in signals.yaml,
so adding a signal never touches a comparator. This module loads that SSOT and scores
a Delta (or a set of Deltas) against it. Stdlib-only: PyYAML is used when importable,
else a minimal built-in parser handles signals.yaml.
"""
from __future__ import annotations

import glob
import json
import os
from typing import Any, Dict, Iterable, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
SIGNALS_PATH = os.path.join(HERE, "signals.yaml")


# --------------------------------------------------------------------------- #
# SSOT loader
# --------------------------------------------------------------------------- #
def load_signals(path: str = SIGNALS_PATH) -> Dict[str, Any]:
    """Load signals.yaml as {signals, links, bands}. PyYAML if present, else fallback."""
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text)
    except Exception:
        return _mini_yaml(text)


def _strip_comment(line: str) -> str:
    out, in_str, q = [], False, ""
    for ch in line:
        if in_str:
            out.append(ch)
            if ch == q:
                in_str = False
        elif ch in ("'", '"'):
            in_str, q = True, ch
            out.append(ch)
        elif ch == "#":
            break
        else:
            out.append(ch)
    return "".join(out).rstrip()


def _scalar(tok: str) -> Any:
    tok = tok.strip()
    if tok == "" or tok == "~" or tok.lower() == "null":
        return None
    if tok.lower() in ("true", "false"):
        return tok.lower() == "true"
    if (tok[0] == tok[-1]) and tok[0] in ("'", '"') and len(tok) >= 2:
        return tok[1:-1]
    try:
        return int(tok)
    except ValueError:
        pass
    try:
        return float(tok)
    except ValueError:
        pass
    return tok


def _flow(tok: str) -> Any:
    """Parse an inline flow value: [a, b], {k: v, ...}, or a scalar."""
    tok = tok.strip()
    if tok.startswith("[") and tok.endswith("]"):
        inner = tok[1:-1].strip()
        return [_scalar(x) for x in _split_top(inner)] if inner else []
    if tok.startswith("{") and tok.endswith("}"):
        inner = tok[1:-1].strip()
        d: Dict[str, Any] = {}
        for part in _split_top(inner):
            k, _, v = part.partition(":")
            d[k.strip()] = _scalar(v)
        return d
    return _scalar(tok)


def _split_top(s: str) -> List[str]:
    """Split on top-level commas (ignoring commas inside quotes/brackets)."""
    parts, depth, buf, in_str, q = [], 0, [], False, ""
    for ch in s:
        if in_str:
            buf.append(ch)
            if ch == q:
                in_str = False
        elif ch in ("'", '"'):
            in_str, q = True, ch
            buf.append(ch)
        elif ch in "[{":
            depth += 1
            buf.append(ch)
        elif ch in "]}":
            depth -= 1
            buf.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if "".join(buf).strip():
        parts.append("".join(buf).strip())
    return parts


def _mini_yaml(text: str) -> Dict[str, Any]:
    """Parse the limited YAML subset used by signals.yaml (block maps/seqs + flow)."""
    rows: List[tuple] = []
    for raw in text.splitlines():
        s = _strip_comment(raw)
        if s.strip() == "":
            continue
        rows.append((len(s) - len(s.lstrip(" ")), s.strip()))

    def parse(i: int, indent: int):
        if rows[i][1].startswith("- "):  # sequence
            seq: List[Any] = []
            while i < len(rows) and rows[i][0] == indent and rows[i][1].startswith("- "):
                rest = rows[i][1][2:].strip()
                if ":" in rest and not rest.startswith(("[", "{")):
                    # mapping item: first key inline, remaining keys at indent+2
                    item: Dict[str, Any] = {}
                    k, _, v = rest.partition(":")
                    child = indent + 2
                    if v.strip():
                        item[k.strip()] = _flow(v)
                        i += 1
                    else:
                        i += 1
                        val, i = parse(i, child)
                        item[k.strip()] = val
                    while i < len(rows) and rows[i][0] == child and not rows[i][1].startswith("- "):
                        k2, _, v2 = rows[i][1].partition(":")
                        if v2.strip():
                            item[k2.strip()] = _flow(v2)
                            i += 1
                        else:
                            i += 1
                            val, i = parse(i, child + 2)
                            item[k2.strip()] = val
                    seq.append(item)
                else:
                    seq.append(_flow(rest))
                    i += 1
            return seq, i
        # mapping
        node: Dict[str, Any] = {}
        while i < len(rows) and rows[i][0] == indent and not rows[i][1].startswith("- "):
            k, _, v = rows[i][1].partition(":")
            if v.strip():
                node[k.strip()] = _flow(v)
                i += 1
            else:
                i += 1
                if i < len(rows) and rows[i][0] > indent:
                    val, i = parse(i, rows[i][0])
                    node[k.strip()] = val
                else:
                    node[k.strip()] = None
        return node, i

    result, _ = parse(0, 0)
    return result


# --------------------------------------------------------------------------- #
# Delta construction + scoring
# --------------------------------------------------------------------------- #
def make_delta(
    facet: str,
    *,
    added: Optional[List[Any]] = None,
    removed: Optional[List[Any]] = None,
    changed: Optional[List[Any]] = None,
    signals: Optional[List[str]] = None,
    evidence: Optional[List[Any]] = None,
    cfg: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a typed Delta and score its direction+magnitude from the SSOT."""
    cfg = cfg or load_signals()
    sig = signals or []
    direction, magnitude = score_signals(sig, cfg)
    return {
        "facet": facet,
        "added": added or [],
        "removed": removed or [],
        "changed": changed or [],
        "signals": sig,
        "direction": direction,
        "magnitude": round(magnitude, 3),
        "evidence": evidence or [],
    }


def score_signals(signals: Iterable[str], cfg: Dict[str, Any]) -> tuple:
    """direction = worst present (worse>better>neutral); magnitude = clamp(worse-better weights)."""
    table = cfg.get("signals", {})
    worse = better = 0.0
    seen_worse = seen_better = False
    for name in signals:
        meta = table.get(name)
        if not meta:
            continue
        d, w = meta.get("direction", "neutral"), float(meta.get("weight", 0.0))
        if d == "worse":
            worse += w
            seen_worse = True
        elif d == "better":
            better += w
            seen_better = True
    direction = "worse" if seen_worse else ("better" if seen_better else "neutral")
    magnitude = max(0.0, min(1.0, worse - better)) if seen_worse else min(1.0, better)
    return direction, magnitude


def band_for(direction: str, magnitude: float, cfg: Dict[str, Any]) -> str:
    """Map (direction, magnitude) to a verdict band per signals.yaml `bands` (first match)."""
    for rule in cfg.get("bands", []):
        w = rule.get("when", {})
        if w.get("direction") == direction and magnitude >= float(w.get("min_magnitude", 0.0)):
            return rule.get("band", "stable")
    return "stable"


def aggregate(deltas: List[Dict[str, Any]], cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Fold a set of per-facet Deltas into one overall direction/magnitude/band."""
    all_sigs: List[str] = []
    for d in deltas:
        all_sigs.extend(d.get("signals", []))
    direction, magnitude = score_signals(all_sigs, cfg)
    return {
        "direction": direction,
        "magnitude": round(magnitude, 3),
        "band": band_for(direction, magnitude, cfg),
        "signal_count": len(all_sigs),
    }


# --------------------------------------------------------------------------- #
# IO helpers
# --------------------------------------------------------------------------- #
def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_runs(path: str) -> List[Dict[str, Any]]:
    """Load a set of behavioral run-records from a dir of *.json or a single array file."""
    if os.path.isdir(path):
        out: List[Dict[str, Any]] = []
        for fp in sorted(glob.glob(os.path.join(path, "*.json"))):
            data = load_json(fp)
            out.extend(data if isinstance(data, list) else [data])
        return out
    data = load_json(path)
    return data if isinstance(data, list) else [data]


def read_version(path: str) -> Dict[str, Any]:
    """Load a version snapshot dir: profile.json, surface.json, sbom.json, runs/."""
    snap: Dict[str, Any] = {"path": path}
    for name in ("profile", "surface", "sbom"):
        fp = os.path.join(path, f"{name}.json")
        if os.path.isfile(fp):
            snap[name] = load_json(fp)
    runs_dir = os.path.join(path, "runs")
    if os.path.isdir(runs_dir):
        snap["runs"] = load_runs(runs_dir)
    return snap


def emit(obj: Any) -> None:
    print(json.dumps(obj, indent=2, sort_keys=False))
