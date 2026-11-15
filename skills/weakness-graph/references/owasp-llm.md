# OWASP-LLM Top 10 — mapping reference

Every weakness carries `owasp_llm_refs`. Use this table to roll weaknesses up to the OWASP-LLM
framework for reporting and benchmarking. `risk_weight` is the platform's benchmark weighting.

| ID | Name | What it covers | risk_weight |
|---|---|---|---|
| LLM01 | Prompt Injection | Direct and indirect prompt injection | 0.14 |
| LLM02 | Insecure Output Handling | Unvalidated model output passed downstream | 0.12 |
| LLM03 | Training Data Poisoning | Manipulation of training / fine-tune data | 0.10 |
| LLM04 | Model Denial of Service | Resource exhaustion via crafted inputs | 0.08 |
| LLM05 | Supply Chain Vulnerabilities | Compromised components in the LLM pipeline | 0.12 |
| LLM06 | Sensitive Information Disclosure | PII / secrets in model outputs | 0.12 |
| LLM07 | Insecure Plugin Design | Unsafe tool / plugin integrations | 0.10 |
| LLM08 | Excessive Agency | LLM taking unintended high-impact actions | 0.10 |
| LLM09 | Overreliance | Treating output as authoritative without validation | 0.06 |
| LLM10 | Model Theft | Extraction of proprietary model parameters | 0.06 |

## Usage

- A weakness may map to several LLM ids (e.g. `llm_cfg_egress_no_dlp` → LLM02 + LLM06). Count it
  under each for coverage, but dedupe by `weakness_id` for the finding count.
- The OWASP rollup is a **reporting lens**, not the primary key — the `weakness_id` is. Map up for
  the OWASP benchmark view; keep the registry id on the node.
