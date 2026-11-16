# Attacker-model selection + governance

The attacker is driven by a model. Which model is a **selectable, governed** choice — not hardcoded.

## The config

```jsonc
attacker_model = {
  "provider": "harness | openai | deepseek | anthropic | …",  // default: "harness"
  "model":    "<model id>",                                    // e.g. deepseek-chat, gpt-4o-mini
  "base_url": "…",        // optional; resolved from the provider registry when omitted
  "api_key_env": "…",     // optional; the env var holding the key (never the key itself)
  "less_restricted": false // a research model with looser safety; sensitive — see governance
}
```

**Default = `harness`** — the model already running this skill (Claude / Codex / whatever drives it).
No config needed for the common case; the harness model plays the attacker.

## Resolution — reuse, don't invent

Resolve the choice through the existing provider abstraction, never a new layer:
- Client/harness side: the harness model, or a provider resolved like
  `~/Nexcraft/Astherixguard/api/services/llm_providers.py` `provider_client(provider, model, …)`
  (registry already covers `openai`, `deepseek`, `nvidia`, `llama3`, `anthropic`).
- Engine side (forge): `OpenAICompatBackend` in
  `~/Nexcraft/asterguard-workforce/src/asterguard_workforce/backends.py` (the attacker role already takes
  a backend); the forge's optional `make_attacker_backend()` honors the same env/selection.

## Governance (dual-use — non-negotiable)

Selecting a non-default or `less_restricted` attacker model is sensitive. Every run:

1. **Authorized only** — the elicited engagement brief is the authorization; a less-restricted attacker
   needs explicit authorization in that brief.
2. **Record it** — write `attacker_model` into the run artifact (`tests.behavioral.json` / `runs/`).
3. **Audit it** — the choice rides through the AsterVault gateway, which stamps every call with an
   `audit_id`; the attacker model used is in the trail.
4. **Report it with ASR** — always "ASR@N with attacker=`<provider>/<model>`". A success rate without the
   attacker model (and budget) is meaningless and non-reproducible.
5. **Gate it** — a less-restricted attacker is an enterprise/authorized capability; default to the
   harness model and require explicit opt-in.

Accountability by construction: who ran which attacker model, against what, when — all in the audit.
