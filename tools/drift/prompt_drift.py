"""prompt_drift — clause-level drift between two system prompts / instruction sets.

Not a raw text diff: it segments each prompt into instruction clauses, matches them
across versions by similarity, and classifies each as added / removed / weakened /
strengthened. Dropped guardrails and new injectable surface become typed signals.

CLI:  python prompt_drift.py A/profile.json B/profile.json
      (also accepts two raw .txt prompt files)
"""
from __future__ import annotations

import difflib
import re
import sys
from typing import Dict, List

try:
    from common import load_signals, make_delta
except ImportError:  # run from repo root
    from tools.drift.common import load_signals, make_delta

# A clause is a guardrail if it asserts a refusal/boundary.
_GUARD = re.compile(
    r"\b(never|do not|don't|must not|must never|refuse|not allowed|forbidden|"
    r"under no circumstances|decline|always require|require approval|do not reveal|"
    r"do not disclose|do not execute)\b",
    re.I,
)
# A clause widens injectable surface if it tells the agent to obey/execute context.
_INJECT = re.compile(
    r"\b(follow (the )?(user|their|any) instructions|obey|do whatever|execute (any|the) "
    r"(instructions|commands)|trust (the )?(context|user input|retrieved)|act on (the )?"
    r"(content|context|instructions in))\b",
    re.I,
)
_MATCH = 0.72  # SequenceMatcher ratio above which two clauses are "the same" clause


def _prompt_text(path: str) -> str:
    if path.endswith(".json"):
        try:
            from common import load_json
        except ImportError:
            from tools.drift.common import load_json
        prof = load_json(path)
        return prof.get("system_prompt", "") or ""
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _clauses(text: str) -> List[str]:
    # split on sentence enders and newlines/bullets; keep non-trivial clauses
    raw = re.split(r"(?<=[.!?])\s+|\n+|•|^\s*[-*]\s+", text, flags=re.M)
    return [c.strip() for c in raw if c and len(c.strip()) > 3]


def _match(a: str, b_list: List[str]) -> int:
    best_i, best_r = -1, 0.0
    for i, b in enumerate(b_list):
        r = difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()
        if r > best_r:
            best_i, best_r = i, r
    return best_i if best_r >= _MATCH else -1


def compare(prompt_a: str, prompt_b: str, cfg=None) -> Dict:
    cfg = cfg or load_signals()
    ca, cb = _clauses(prompt_a), _clauses(prompt_b)
    used_b = set()
    added, removed, changed, signals, evidence = [], [], [], [], []

    for a in ca:
        j = _match(a, cb)
        if j < 0 or j in used_b:
            removed.append(a)
            if _GUARD.search(a):
                signals.append("weakened_guardrail")
                evidence.append({"signal": "weakened_guardrail", "removed_clause": a})
        else:
            used_b.add(j)
            b = cb[j]
            if a.lower() != b.lower():
                changed.append({"from": a, "to": b})
                # a guardrail that lost its guard words = weakened
                if _GUARD.search(a) and not _GUARD.search(b):
                    signals.append("weakened_guardrail")
                    evidence.append({"signal": "weakened_guardrail", "from": a, "to": b})

    for j, b in enumerate(cb):
        if j in used_b:
            continue
        added.append(b)
        if _GUARD.search(b):
            signals.append("guardrail_added")
            evidence.append({"signal": "guardrail_added", "added_clause": b})
        if _INJECT.search(b):
            signals.append("new_injectable_surface")
            evidence.append({"signal": "new_injectable_surface", "added_clause": b})

    return make_delta(
        "prompt",
        added=added,
        removed=removed,
        changed=changed,
        signals=sorted(set(signals)),
        evidence=evidence,
        cfg=cfg,
    )


def main(argv: List[str]) -> int:
    if len(argv) != 2:
        print("usage: prompt_drift.py <A.json|A.txt> <B.json|B.txt>", file=sys.stderr)
        return 2
    try:
        from common import emit
    except ImportError:
        from tools.drift.common import emit
    emit(compare(_prompt_text(argv[0]), _prompt_text(argv[1])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
