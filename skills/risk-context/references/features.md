# Risk features — what each means, why it matters, how evidence maps to it

The risk picture is twelve features. This reference explains each one and **how tests and findings map
to it** so an agent (or engineer) can reason to a judgment — the **free tier**. The calibrated weights
and the single ARS number are the **enterprise** model; everything here works without them.

> **Free:** these explanations + the feature values from your own scan + your own reasoning.
> **Enterprise:** adds the weighted ARS (0–10) + band + the four scoring heads (the calibration).

## The twelve features

| Feature | What it is | Why it matters | Evidence that raises it |
|---|---|---|---|
| **severity_weight** | the scanner's severity | the **floor** — risk never reads below it | SAST/SCA/IaC severity on the finding |
| **owasp_weight** | OWASP-LLM category | some classes are inherently worse: injection (LLM01), disclosure (LLM06), excessive agency (LLM08) | the weakness's OWASP-LLM mapping |
| **data_class** | sensitivity of data on the path | what's at stake — public → internal → PII → PCI/PHI → regulated | data-flow `data_classes`; a canary document's class; fields like ssn/card |
| **kev** | known-exploited (CISA KEV) | active, in-the-wild exploitation ⇒ urgent regardless of score | the CVE appears in the KEV catalog |
| **epss** | exploit **probability** (0–1) | likelihood someone *will* exploit it soon | the CVE's EPSS percentile |
| **reachability** | runtime · reachable · build-only · unreachable | **the biggest lever** — an unreachable critical is rarely the top fix | the component sits on a reachable path in the graph; a proven break |
| **tool_authority** | can it **act** (effectful tool / agency / exfil / rce) | the difference between "exists" and "can cause harm" | agent-profiling shows an effectful tool on the path; weakness keywords (tool/exfil/command/sql/ssrf) |
| **blast_ctx** | blast radius (single resource → tenant → account → org) | how far the damage spreads | what the identity/tool can reach in the graph |
| **business_criticality** | business importance of the app | value at risk | org/inventory context |
| **asset_criticality** | importance of the specific asset | criticality of the thing hit | inventory / data-store criticality |
| **external_facing** | internet-reachable | gives an attacker access at all | endpoint exposure in the graph |
| **auth_anon** | reachable **anonymously** | no barrier to exploit — the strongest exposure signal | the endpoint/path has no auth (e.g. an anonymous `/admin/export`) |

## How tests map to features (LLM-reasoned)

The agent maps each test/finding's evidence to the features it moves — this is reasoning, not a lookup:

- **A canary `verify → fired`** ⇒ `reachability = runtime` (it actually ran), `data_class` = the canary's
  class (secret/PII), `auth_anon` high if the leak path had no auth, `tool_authority` high if it left via
  an effectful tool.
- **A behavioral break (prompt-injection, excessive agency)** ⇒ `reachability = reachable`,
  `tool_authority` high, `owasp_weight` for LLM01/LLM08.
- **An information-flow violation (store → external sink)** ⇒ `data_class` from the store, `blast_ctx`
  from the sink's reach, `external_facing` if the sink is internet-bound.
- **An SCA CVE** ⇒ `severity_weight`, `kev`/`epss` from the CVE, `reachability` from whether the package
  is on a runtime path (not just in the image).
- **An IaC/identity finding** ⇒ `auth_anon`/`external_facing`/`blast_ctx` from the exposure it reveals.

State the mapping out loud: *"the canary proved exfil ⇒ runtime-reachable + anonymous + PII ⇒ top-tier,
regardless of the base CVE severity."* That reasoning **is** the risk judgment in the free tier.

## Reading the picture (free tier)

1. Start at the **floor** (severity) — risk is at least this.
2. Raise it for **exploitation** (kev, epss, a proven break) and **exposure** (reachability, external,
   anonymous).
3. Weight by **stakes** (data_class) and **spread** (blast, tool_authority).
4. Lead with the dominant two or three features; name the lever that would lower it (usually
   reachability or a passing control).

Enterprise collapses the same features into one calibrated ARS; free keeps them legible so a team
reasons — and calibrates — to its own appetite.
