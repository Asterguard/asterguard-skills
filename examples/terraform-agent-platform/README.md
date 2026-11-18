# Worked example — AppSec on a vulnerable Terraform agent platform

A full, step-by-step analysis of **`CoMatrixlabs/terraform-agent-platform-demo`** @ `cbae078` —
a deliberately vulnerable infrastructure-as-code fixture — run through two AsterGuard skills:

| Skill | What it does here | Report | Watch |
|---|---|---|---|
| [`/local-scan`](../../skills/local-scan) | fast, client-side, four-lane scanner pass | [`report-local-scan.md`](report-local-scan.md) | [▶ 36s run](https://agenticrisklabs.io/videos/terraform-agent-platform/local-scan-walkthrough.mp4) |
| [`/security-engineer`](../../skills/security-engineer) | full-360 assessment → weaknesses, controls, risk, attack paths, fixes | [`report-security-engineer.md`](report-security-engineer.md) | [▶ 40s run](https://agenticrisklabs.io/videos/terraform-agent-platform/security-engineer-walkthrough.mp4) |

This README walks the *app itself*, layer by layer. The two **reports** are the full markdown
deliverables (rendered on GitHub); the **Watch** links are short screen-recordings of each run
(hosted — click to play in your browser).

> **Nothing here is proven by a live test.** The target is static Terraform — there is no running
> agent to drive — so every attack path below is **theoretical**: reachable as written, not
> canary-confirmed. The same pipeline marks a finding *proven* only when a canary or a live red-team
> episode fires. See [Method & coverage notes](#method--coverage-notes).

---

## 0. The app under test

A **SupportAgent LLM platform** defined entirely in Terraform (7 files, 6 of them `.tf`; no application
code, no package manifests). It stands up, on AWS:

- An **LLM support agent** behind a public API, backed by a **SPIFFE/SPIRE** workload-identity plane.
- Four regulated data stores: an **S3 `customer-records`** bucket (PII + PCI), an **S3
  `ticket-transcripts`** bucket (PII), an **RDS `support-agent-db`** (PII), and a **DynamoDB
  `accounts`** table (PII + PCI).
- IAM roles that let the agent reach that data, plus a **SPIRE server** that issues the agent its
  identity and **federates** that identity into AWS via OIDC.

Because it's pure IaC, the right lens is *infrastructure* — so both skills classify it that way and
skip SCA/SBOM, SAST and AI-BOM (there's nothing for those to chew on).

```
Internet ──▶ Agent API :443 ──▶ SupportAgent (pods, ns=agents)
                                      │ issued SVID (admin  OR  support-agent)
                                      ▼
                             SPIRE  ──▶ OIDC federation ──▶ AWS IAM role
                                                                 │ Resource:*
                                   ┌─────────────┬───────────────┼───────────────┐
                                   ▼             ▼               ▼               ▼
                          S3 customer-records  S3 ticket-   RDS support-   DynamoDB
                             [PII+PCI]         transcripts   agent-db        accounts
                                                 [PII]        [PII]         [PII+PCI]
```

---

## 1. Reproduce it

```bash
# clone the fixture
git clone git@github.com:CoMatrixlabs/terraform-agent-platform-demo.git
cd terraform-agent-platform-demo        # pinned at commit cbae078

# fast first look — four lanes, all local, nothing uploaded
/local-scan .

# full assessment — scan → weaknesses → controls → risk → attack paths → fixes
/security-engineer .
```

`/local-scan` tells you in seconds *where* the risk is. `/security-engineer` tells you *what it means
and how to fix it*. The sections below follow the second, deeper pass.

---

## 2. `/local-scan` — the four-lane first look

Four open-source lanes run in parallel on your machine. Only one fires.

| Lane | Tool(s) | Result |
|---|---|---|
| Dependencies (SCA) | syft 1.57.2 + grype 0.122.0 | **0 packages, 0 CVEs** — no manifests or lockfiles |
| Infrastructure (IaC) | checkov 3.4.5 | **53 failed / 47 passed** across 18 Terraform resources |
| Secrets | trufflehog 3.99.9 | **0 verified secrets** |
| AI assets (AI-BOM) | ai-bom | **0 models / datasets** — no app code |

**Read it right:** the empty lanes are *answers*, not misses. There is no dependency surface and no
git-history secret. The app's entire risk surface is in the **infrastructure** lane. (The hardcoded
RDS password *does* exist — but it lives in a Terraform variable, so it surfaces as an IaC/secret
finding in the full pass, not as a committed credential trufflehog would catch.) Nothing is uploaded;
the commit (`cbae078`) is recorded so the scan is reproducible.

---

## 3. `/security-engineer` — step-by-step analysis of the app

The full pass runs the scanners, **then reviews what the scanners can't see**, maps everything to
weaknesses and controls, scores it, and traces the attack paths. Here is the app, layer by layer.

### 3.1 Data layer — two stores reachable with no identity

| Sev | Store | Problem | Where |
|---|---|---|---|
| **critical** | S3 `customer-records` [PII+PCI] | `public-read` ACL, **no** public-access block, no SSE-KMS, no logging, no versioning | `data.tf:7` |
| **critical** | RDS `support-agent-db` [PII] | `publicly_accessible = true`, **master password committed** (`ChangeMe123!`), no IAM auth, storage unencrypted | `data.tf:53`, pw at `data.tf:59` |
| medium | S3 `ticket-transcripts` [PII] | no SSE-KMS, no versioning, no access logging | `data.tf:18` |
| medium | DynamoDB `accounts` [PII+PCI] | no customer-managed KMS key, no point-in-time recovery | `data.tf:41` |
| high | KMS `data` key | key policy `Principal:*`, rotation disabled | `data.tf:24` |

Two of these — the customer-records bucket and the support database — are reachable **from the
internet with no identity at all**. That's the lede of the whole assessment.

### 3.2 IAM layer — the agent (and a static key) can own the account

- **`agent_exec_role`** carries `s3:*` / `dynamodb:*` / `kms:*` **plus `AdministratorAccess`**
  (`iam.tf:9`, `iam.tf:51`), and its `agent_data_grant` reads every store via `Resource:*` with
  `dynamodb:Scan` (`agent_access.tf:41`).
- The role can **escalate itself** — `PassRole`, `AttachRolePolicy`, `PutRolePolicy` are in scope.
- **`agent_deployer`** is a long-lived IAM **user with a static access key** (`iam.tf:57`), granted
  `Action:* / Resource:*` (`iam.tf:65`), whose secret is written into Terraform state.
- The exec role trusts the **account root**, so any principal allowed `sts:AssumeRole` reaches it.

### 3.3 Workload-identity layer (SPIFFE/SPIRE) — the part checkov never sees

checkov cannot parse SPIRE config embedded in a Kubernetes ConfigMap, so **a manual review of
`spire.tf` / `agent_access.tf` / `network.tf` found 10 gaps checkov missed**:

| Sev | Finding | Where |
|---|---|---|
| **critical** | the **admin SVID is handed to every pod** in `ns:agents` — the registration selector is namespace-only | `spire.tf:87` |
| high | OIDC trust is `StringLike sub spiffe://agents.internal/*` — **any** SVID (incl. admin) can assume the data role; no `aud` condition | `agent_access.tf:30` |
| high | the `support-agent` SVID is shared across LLM, tools and deployer (no per-tool identity) | `spire.tf:79` |
| high | `join_token` node attestation with no `k8s_psat` / `aws_iid` platform binding | `spire.tf:42` |
| high | `UpstreamAuthority "disk"` — the trust-domain CA key sits **unencrypted** on the container FS | `spire.tf:33` |
| high | SPIRE server **port 8081 open to `0.0.0.0/0`** (checkov flags 22, not 8081) | `network.tf:20` |
| medium | SVID TTL 168h / registration 604800s / CA 8760h — **leaked SVIDs outlive their pods by days** | `spire.tf:24` |
| medium | `audit_log_enabled = false` — no record of registration or attestation | `spire.tf:27` |
| medium | federation uses `https_web` instead of `https_spiffe`; bundle endpoint bound to `0.0.0.0` | `spire.tf:49` |
| low | OIDC thumbprint is all zeros and the issuer host is private, so STS can't fetch JWKS as written | `agent_access.tf:12` |

### 3.4 Network layer — open in, open out

- Security group allows ingress from `0.0.0.0/0` (port 22 flagged; **8081 not**), and **egress
  `0.0.0.0/0` on all protocols** with no allowlist or DLP (`network.tf:5`).
- No ALB/WAF in front of the agent API.

---

## 4. Attack paths

Computed locally from the security graph (17 components, 19 edges). All **theoretical** (static IaC).

1. **Anonymous read of customer records** — `Internet → S3 customer-records` [PII+PCI]. *(1 hop)*
2. **Direct login to the support database** — `Internet → RDS support-agent-db` with the committed
   password. *(1 hop)*
3. **Prompt-injected agent reads every regulated store** — `Internet → Agent API → SupportAgent →
   admin SVID → OIDC sub=…/* → IAM workload role → S3 + S3 + DynamoDB → unrestricted egress`. *(7 hops)*
4. **Leaked deployer key owns the account** — `static key → *:* → AdministratorAccess exec role → all
   data, KMS, IAM`. *(credential theft)*
5. **Workload-identity plane exposed** — `Internet → SPIRE :8081 → join-token attestation → mint any
   SVID in agents.internal`. *(identity forgery)*

Paths 1 and 2 need **no identity**. Path 3 is the full agent-abuse chain. Paths 4 and 5 are
account-level compromise.

---

## 5. Findings, weaknesses & controls

- **Raw:** 53 checkov failures (47 passed) across 18 resources + 10 manual identity gaps + 1 semgrep
  secret (hardcoded RDS password, CWE-522/798 — checkov's secrets framework missed it).
- **Resolved:** 7 weaknesses map cleanly to the AsterVault registry and their controls —
  over-privileged agent, excessive agency, PII/PCI trust-zone downgrade, encryption-at-rest removed,
  access-approval removed, egress-without-DLP. Controls span **SOC 2, NIST 800-53, GDPR, PCI-DSS**
  plus SCF crosswalk families.
- **Honestly keyed to CWE:** hardcoded credentials, SPIFFE identity misbinding, and network exposure
  have **no IaC-native registry entry**, so they stay keyed to CWE rather than force-fit to an
  unrelated LLM weakness.
- **Verdict:** `risk.score` returns an **ARS floor of 9.0 (critical)** → **Gate: BLOCK**.

---

## 6. Fixes (in order of blast radius removed)

Each is scoped to the least-privilege allow-set the graph shows the agent actually needs.
**Fixes 1–3 together break every path above.**

1. **Bind the AWS trust to one SPIFFE subject** — exact-match `sub` + `aud`; admin/tool SVIDs can no
   longer assume the data role. *(breaks path 3)*
2. **Scope the data grant** — no `Scan`, no wildcard resources; card data moves behind a separate,
   approval-gated identity. *(breaks the wildcard read in path 3)*
3. **Fix SPIRE registration & attestation** — pin each workload by service account + image digest,
   delete the admin entry from `ns:agents`, move to `k8s_psat` + KMS-backed CA, short TTLs. *(breaks
   paths 3 and 5)*
4. **Remove admin from the agent role, retire the static key** — detach `AdministratorAccess` and the
   self-escalation actions, add a permissions boundary, trust only workload federation, replace the
   deployer user with CI OIDC. *(breaks path 4)*
5. **Close public data exposure & encrypt** — public-access block + SSE-KMS on the buckets, key
   rotation, `publicly_accessible = false` + encryption + IAM auth on RDS, CMK + PITR on DynamoDB.
   *(breaks paths 1 and 2)*
6. **Default-deny the network** — drop the `0.0.0.0/0` rules on 22 and 8081, put the API behind an
   ALB/WAF, send egress only to allowlisted hosts through a DLP proxy.

---

## 7. The resulting reports

Each skill ends in a markdown deliverable — both in this folder, rendered on GitHub:

- **[`report-local-scan.md`](report-local-scan.md)** — the four-lane scan summary: the lane table, the
  53 checkov failures grouped by resource, and the method/commit/tooling notes. Says *where* the risk
  is and stops.
- **[`report-security-engineer.md`](report-security-engineer.md)** — the full assessment: verdict
  (**BLOCK**, ARS floor 9.0), the 5 attack paths, the kill-chain diagram, findings by layer (IaC + the
  10 identity gaps), the weakness→control map, the 6 ranked fixes, and the coverage notes. Says *what it
  means and how to fix it*.

Read them in order: `local-scan` is the 10-second triage, `security-engineer` is the assessment you hand
to an engineer. Both are produced in **client mode** — generated on your machine by the skill running in
your coding agent; the AsterVault MCP supplies only grounding (weakness registry, control crosswalk,
risk floor), never your source or findings.

Prefer to watch? The step-by-step runs are linked at the top —
[▶ `/security-engineer` (40s)](https://agenticrisklabs.io/videos/terraform-agent-platform/security-engineer-walkthrough.mp4) ·
[▶ `/local-scan` (36s)](https://agenticrisklabs.io/videos/terraform-agent-platform/local-scan-walkthrough.mp4).

---

## Method & coverage notes

What the pipeline got right, and where it was honest about its own limits:

- **Collectors.** checkov 3.4.5 (terraform, secrets) + semgrep `p/terraform` ran fresh on the clone;
  the fixture's committed `out/` results were not reused. SCA/SBOM, AI-BOM and SAST don't apply (no
  packages, no app code).
- **Registry resolution was noisy.** `registry.resolve` keyword matching mapped 5/8 IaC findings to
  **unrelated** LLM weaknesses (password → `code_active_debug_code`; SPIRE registration →
  `cascading_hallucination`; security group → SSN exfiltration). Those were **rejected** and
  re-searched directly.
- **`graph.enrich` returned no paths** and dropped both PII+PCI stores (probably the compound
  data-class label), so the paths were computed locally from the same graph.
- **AWS defaults would blunt two findings at apply time.** New S3 buckets enforce Block Public Access;
  RDS gets the VPC default security group. The posture is still non-compliant — each default is one
  change away from real exposure.
- **One README claim is overstated.** Federation uses `https_web` (Web-PKI authenticated), not
  unauthenticated — rated medium, not critical. The bundle endpoint on 8443 isn't opened by the SG.
- **Not run:** DAST, behavioral red-team, canary episodes. There's no live agent endpoint to drive,
  so **nothing is marked proven**.

---

*Produced by the AsterGuard skill pack (client mode). The grounding for this example is the real run's
output: `scan.plan → checkov/semgrep → graph (asterguard.graph/v1) → registry.resolve + controls.map →
risk.score → local path analysis`.*
