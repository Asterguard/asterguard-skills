# Positioning — vs native agent security

Claude Code and Codex already reason about security well: read a diff, spot an injection, explain a
CVE, suggest a fix. These skills do **not** compete with that. They provide the five things the model's
context structurally cannot hold — turning good-but-ungrounded reasoning into something grounded,
auditable, proven, enforced, and compounding.

## Complement, don't compete

| The model lacks (in context) | The MCP / skills provide | Why a better model won't close it |
|---|---|---|
| **Your org's specifics** | the app's security graph, your control crosswalk, approved patterns, prior decisions/waivers (memory) | it has never seen your systems or history — this is retrieval, not reasoning |
| **Determinism / auditability** | `registry.resolve`, `controls.map`, policy-as-code (asterguard-remediation) | a *guessed* GDPR article is useless for compliance; these are retrieved and defensible |
| **Evidence, not opinion** | canary `verify → fired`, gateway egress detection + tamper-evident audit | the model reasons about likelihood; a canary **proves** exfil happened |
| **Enforcement** | AsterVault applies egress allowlists / scoped creds / tokenization | a model advises; it cannot gate production traffic — a capability, not knowledge |
| **Compounding + cross-harness** | memory shared across sessions, teammates, Claude↔Codex | the base model forgets each session; this makes a lesson persist and spread |

**One line:** native agent security is a smart reviewer with amnesia and no ground truth about your
org; this stack gives it the org brain, the proof, and the runtime.

## The honest limits

- **Knowledge is thin today** — the registry/crosswalk/scoring are solid but not exhaustive; no live
  CSPM yet; the lake only covers onboarded apps. For a *solo one-off* ("is this file vulnerable?"),
  native Claude/Codex already delivers most of the value; our marginal add is the standardized framing +
  visuals + the system-wide graph.
- **The value is team/org-shaped** — it compounds with memory accumulation, enterprise scoring, and
  enforcement. Strongest for a security engineer scaling across an org; weakest for a hobbyist one-off.

## Why "custom models on the MCP later" is the right bet

It strengthens the one axis where we differ — **knowledge/calibration** — while leaving reasoning to the
frontier model (which keeps improving for free). Fine-tuned risk models, org-specific weakness
classifiers, a calibration learned from the org's own decisions — all plug in behind the same MCP
contract, and every skill gets smarter with **no client change**. The model-standardizes-knowledge /
skills-are-views architecture is precisely what makes that drop-in possible.

**Bottom line:** a grounding, proof, enforcement, and memory layer *around* whatever model is driving —
lean into what only the MCP can own (your graph, your controls, canary evidence, enforcement, memory);
don't re-implement the model's reasoning.
