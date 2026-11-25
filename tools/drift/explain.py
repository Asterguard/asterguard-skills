"""explain — turn a bag of per-facet drift signals into a cause -> effect narrative.

The value of drift is not "ARS went up" but "THIS edit caused THAT regression". This
module reads the `links` in signals.yaml (cause-signals -> predicted effect-signal) and
fires a link when all of its cause-signals AND its effect-signal are present in the same
drift run. Each fired link yields one narrative line binding the real evidence.

Pure, deterministic, and dependency-free. Connected runs can hand the same signals to the
AsterVault gateway `drift.compare` for a calibrated index; the narrative stays identical.
"""
from __future__ import annotations

from typing import Any, Dict, List

try:
    from common import load_signals
except ImportError:
    from tools.drift.common import load_signals


def _signal_facets(deltas: List[Dict[str, Any]]) -> Dict[str, str]:
    """signal -> facet, for attributing a narrative line to where it came from."""
    out = {}
    for d in deltas:
        for s in d.get("signals", []):
            out[s] = d.get("facet", "")
    return out


def correlate(deltas: List[Dict[str, Any]], cfg: Dict[str, Any] = None) -> Dict[str, Any]:
    cfg = cfg or load_signals()
    present = set()
    for d in deltas:
        present.update(d.get("signals", []))

    fired: List[Dict[str, Any]] = []
    for link in cfg.get("links", []):
        causes = link.get("cause", []) or []
        effect = link.get("effect")
        if all(c in present for c in causes) and effect in present:
            fired.append({
                "cause": causes,
                "effect": effect,
                "kind": link.get("kind"),
                "narrative": link.get("narrative", ""),
            })
    return {"links_fired": fired, "narrative": [_sentence(l["narrative"]) for l in fired]}


def _sentence(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    return text[0].upper() + text[1:] + ("" if text.endswith(".") else ".")


def summarize(deltas: List[Dict[str, Any]], aggregate: Dict[str, Any], cfg: Dict[str, Any] = None) -> str:
    """One human-readable paragraph: the headline band + the strongest cause->effect lines."""
    cfg = cfg or load_signals()
    corr = correlate(deltas, cfg)
    band = aggregate.get("band", "stable")
    head = {
        "critical-regression": "Critical regression between versions.",
        "regression": "Posture regressed between versions.",
        "minor-regression": "Minor regression between versions.",
        "hardening": "Posture hardened between versions.",
        "stable": "No material drift between versions.",
    }.get(band, "Drift measured between versions.")
    lines = [head]
    lines.extend(corr["narrative"])
    if not corr["narrative"] and band != "stable":
        # no cause->effect link fired, but signals exist — report the facets that moved
        moved = [f"{d['facet']} ({d['direction']})" for d in deltas if d.get("signals")]
        if moved:
            lines.append("Facets that moved: " + ", ".join(moved) + ".")
    return " ".join(lines)
