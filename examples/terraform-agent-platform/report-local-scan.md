# Report — `/local-scan` · terraform-agent-platform-demo

**Target:** `CoMatrixlabs/terraform-agent-platform-demo` @ `cbae078` · 7 files (6 Terraform) · scanned
on-host, **nothing uploaded**
**Result:** `53 IaC findings` · `0 CVEs` · `0 secrets` · `0 AI assets` · **1 of 4 lanes fired**

| | |
|---|---|
| checkov checks failed | **53** (47 passed) across 18 Terraform resources |
| packages / CVEs | **0** — no manifests or lockfiles |
| verified secrets (trufflehog) | **0** |
| models / datasets (AI-BOM) | **0** — no app code |

---

## Lanes — what each scanner found

Four open-source lanes ran in parallel, all on-host. Three came back empty — correctly, given a
pure-IaC repo — and the infrastructure lane carries the whole risk surface.

| Lane | Tool | Result |
|---|---|---|
| Dependencies (SCA) | syft 1.57.2 + grype 0.122.0 | **0 packages · 0 CVEs** — no manifests/lockfiles |
| Infrastructure (IaC) | checkov 3.4.5 | **53 failed · 47 passed** across 18 resources |
| Secrets | trufflehog 3.99.9 | **0 verified** — the RDS password lives in Terraform → IaC lane |
| AI assets (AI-BOM) | ai-bom | **0 models / datasets** — no app code |

**Read it right:** the empty lanes are *answers*, not misses. There's no dependency surface and no
git-history secret. The app's entire risk surface is in the **infrastructure** lane — the raw material
the full [`/security-engineer`](report-security-engineer.md) pass turns into named weaknesses, mapped
controls and attack paths.

---

## Infrastructure lane — 53 failed checks, grouped by resource

53 failures fall under 12 of the 18 resources scanned. Severity is the assessment's rating for that
resource; the check IDs are checkov's.

<details><summary><b>🔴 critical</b> · <code>aws_db_instance.support_db</code> · <code>data.tf:53</code> · 11 checks</summary>

- `CKV_AWS_161` RDS has IAM authentication enabled
- `CKV_AWS_293` database instances have deletion protection enabled
- `CKV_AWS_353` RDS instances have performance insights enabled
- `CKV_AWS_157` RDS instances have Multi-AZ enabled
- `CKV_AWS_129` RDS logs are enabled
- `CKV_AWS_226` DB instance gets all minor upgrades automatically
- `CKV_AWS_17` all data stored in RDS is not publicly accessible
- `CKV_AWS_118` enhanced monitoring is enabled for RDS
- `CKV_AWS_16` all data stored in RDS is securely encrypted at rest
- `CKV2_AWS_60` RDS instance copies tags to snapshots
- `CKV2_AWS_30` Postgres RDS has Query Logging enabled
</details>

<details><summary><b>🔴 critical</b> · <code>aws_iam_user_policy.agent_deployer</code> · <code>iam.tf:65</code> · 10 checks</summary>

- `CKV_AWS_288` IAM policies do not allow data exfiltration
- `CKV_AWS_290` IAM policies do not allow write access without constraints
- `CKV_AWS_287` IAM policies do not allow credentials exposure
- `CKV_AWS_63` no IAM policy allows `*` as a statement's actions
- `CKV_AWS_289` IAM policies do not allow permissions management / resource exposure without constraints
- `CKV_AWS_62` IAM policies do not allow full `*-*` administrative privileges
- `CKV_AWS_40` IAM policies are attached only to groups or roles
- `CKV_AWS_355` no IAM policy allows `*` as a statement's resource for restrictable actions
- `CKV_AWS_286` IAM policies do not allow privilege escalation
- `CKV2_AWS_40` IAM policy does not allow full IAM privileges
</details>

<details><summary><b>🔴 critical</b> · <code>aws_s3_bucket.customer_records</code> · <code>data.tf:7</code> · 8 checks</summary>

- `CKV2_AWS_62` S3 bucket has event notifications enabled
- `CKV2_AWS_6` S3 bucket has a Public Access block
- `CKV2_AWS_61` S3 bucket has a lifecycle configuration
- `CKV_AWS_18` S3 bucket has access logging enabled
- `CKV_AWS_145` S3 bucket is encrypted with KMS by default
- `CKV_AWS_20` **S3 bucket ACL allows public READ access**
- `CKV_AWS_21` S3 bucket has versioning enabled
- `CKV_AWS_144` S3 bucket has cross-region replication enabled
</details>

<details><summary><b>🔴 critical</b> · <code>aws_iam_role_policy.agent_inline</code> · <code>iam.tf:27</code> · 4 checks</summary>

- `CKV_AWS_288` IAM policies do not allow data exfiltration
- `CKV_AWS_290` IAM policies do not allow write access without constraints
- `CKV_AWS_289` IAM policies do not allow permissions management / resource exposure without constraints
- `CKV_AWS_355` no IAM policy allows `*` as a statement's resource for restrictable actions
</details>

<details><summary><b>🔴 critical</b> · <code>aws_iam_role_policy_attachment.agent_admin</code> · <code>iam.tf:51</code> · 1 check</summary>

- `CKV_AWS_274` disallow IAM roles/users/groups from using the AWS `AdministratorAccess` policy
</details>

<details><summary><b>🟠 high</b> · <code>aws_security_group.agent_svc</code> · <code>network.tf:5</code> · 4 checks</summary>

- `CKV_AWS_24` no security group allows ingress from `0.0.0.0/0` to port 22
- `CKV_AWS_23` every security group and rule has a description
- `CKV_AWS_382` no security group allows egress from `0.0.0.0/0` to port -1
- `CKV2_AWS_5` security groups are attached to another resource
</details>

<details><summary><b>🟠 high</b> · <code>aws_iam_role_policy.agent_data_grant</code> · <code>agent_access.tf:41</code> · 2 checks</summary>

- `CKV_AWS_288` IAM policies do not allow data exfiltration
- `CKV_AWS_355` no IAM policy allows `*` as a statement's resource for restrictable actions
</details>

<details><summary><b>🟠 high</b> · <code>aws_kms_key.data</code> · <code>data.tf:24</code> · 2 checks</summary>

- `CKV_AWS_33` KMS key policy does not contain a wildcard (`*`) principal
- `CKV_AWS_7` rotation for customer-created CMKs is enabled
</details>

<details><summary><b>🟠 high</b> · <code>aws_iam_role.agent_exec_role</code> · <code>iam.tf:9</code> · 1 check</summary>

- `CKV_AWS_61` IAM policy does not allow assume-role across all services
</details>

<details><summary><b>🟡 medium</b> · <code>aws_s3_bucket.ticket_transcripts</code> · <code>data.tf:18</code> · 7 checks</summary>

- `CKV2_AWS_62` S3 bucket has event notifications enabled
- `CKV2_AWS_6` S3 bucket has a Public Access block
- `CKV2_AWS_61` S3 bucket has a lifecycle configuration
- `CKV_AWS_18` S3 bucket has access logging enabled
- `CKV_AWS_145` S3 bucket is encrypted with KMS by default
- `CKV_AWS_21` S3 bucket has versioning enabled
- `CKV_AWS_144` S3 bucket has cross-region replication enabled
</details>

<details><summary><b>🟡 medium</b> · <code>aws_dynamodb_table.accounts</code> · <code>data.tf:41</code> · 2 checks</summary>

- `CKV_AWS_28` DynamoDB point-in-time recovery (backup) is enabled
- `CKV_AWS_119` DynamoDB tables are encrypted with a KMS CMK
</details>

<details><summary><b>🟡 medium</b> · <code>aws_iam_user.agent_deployer</code> · <code>iam.tf:57</code> · 1 check</summary>

- `CKV_AWS_273` access is controlled through SSO, not IAM-defined users
</details>

---

## Method

- **Commit pinned.** Scanned at `cbae078` (unchanged since the earlier assessment) — reproducible.
- **Tools.** syft 1.57.2, grype 0.122.0 and trufflehog 3.99.9 via Homebrew; checkov 3.4.5 from the
  scratchpad virtualenv.
- **Local-only.** Every lane ran on-host. **Nothing was uploaded** — no source, no findings, no SBOM.
- **Empty lanes are answers.** No manifests → no SCA surface; no app code → no AI-BOM. The hardcoded
  RDS password is real but lives in a Terraform variable, so it surfaces in the IaC lane (and semgrep
  during the full pass), not as a git-history secret.

→ Next: the full assessment — weaknesses, controls, attack paths and fixes — in
[`report-security-engineer.md`](report-security-engineer.md) (verdict **BLOCK**, ARS floor 9.0).
