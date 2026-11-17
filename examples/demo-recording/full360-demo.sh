#!/usr/bin/env bash
# Narrated full-360 walkthrough for the demo recording (deterministic playback).
# Grounded in the real tool calls/outputs from examples/live-demo/demo-walk.py.
# Rendered to a GIF by full360.tape (VHS). Re-run the tape after changing this.
set -u

# ---- palette ----------------------------------------------------------------
R=$'\033[0m'; B=$'\033[1m'; D=$'\033[2m'
CY=$'\033[36m'; GR=$'\033[32m'; YL=$'\033[33m'; RD=$'\033[31m'; MG=$'\033[35m'; GY=$'\033[90m'
tick="${GR}✓${R}"; arr="${GY}→${R}"

p(){ printf '%b\n' "$1"; }
step(){ printf '\n%b\n' "${B}${MG}⬡ $1${R}  ${D}$2${R}"; sleep 0.5; }
tool(){ printf '   %b %-42s %b %s\n' "$tick" "$1" "$arr" "$2"; sleep 0.45; }
say(){ printf '   %b%s%b\n' "$D" "$1" "$R"; sleep 0.35; }

clear
p "${D}Claude Code · plugin ${R}${B}asterguard-security${R}${D}  ·  astervault MCP connected (18 security tools)${R}"
sleep 0.6
p ""
p "${CY}${B}❯${R} ${CY}Review support-agent for AppSec — scan it, red-team the risky paths, and${R}"
p "${CY}  recommend enforcement policies.${R}"
sleep 1.0
p ""
p "${B}AsterGuard${R} ${D}▸ security-engineer → ${R}${B}full-360${R}${D} playbook   ·   target: support-agent${R}"
sleep 0.8

step "recall + scope" "start informed, not cold"
tool "knowledge-recall · memory.recall" "0 prior memories ${D}(cold start)${R}"
tool "knowledge.patterns" "house rules: [PII→tokenize, egress-allowlist]"

step "scan + build the architecture" "local, client-side"
tool "local-scan ${D}(SAST·SCA·IaC·secrets·AI-BOM)${R}" "37 findings"
tool "sca-graph" "214 packages · 11 CVEs ${D}(deduped)${R}"
tool "weakness-graph" "weakness↔component + control crosswalk"
tool "agent-profiling" "1 tool over-privileged: ${YL}admin_export_records${R}"

step "resolve the lede finding" "finding → canonical weakness"
tool "registry.resolve" "${RD}llm_cfg_egress_no_dlp${R} · critical · data_exfiltration"
say "OWASP LLM02/LLM06 · reachable by an ${B}anonymous${R}${D} identity${R}"
tool "controls.map" "NIST:AC-4, SC-7 · ISO:A.8.12 · HIPAA:164.312(e)"

step "red-team the risky path" "attacker ▸ defender ▸ judge"
tool "canary.mint · canary.plant" "sk-canary-livedemo-… ${D}planted in admin_export${R}"
tool "canary.scan ${D}(attacker exfiltrates, base64)${R}" "${RD}HIT${R} via base64 encoding"
tool "canary.verify" "fired=${B}true${R}  ⇒  ${RD}${B}PROVEN PII exfiltration${R} ${D}(not a guess)${R}"

step "remediate — fix as a PR" "asterguard-remediation SSOT"
tool "remediation.from_episode → to_pr" "3 control gaps → policy-as-code PR"
say "branch ${GY}fix/support-agent-egress-dlp${R}${D} · egress allowlist + tokenize + deny anon export${R}"

step "enforce — gateway applies it" "review-gated"
tool "policy.apply ${D}(approved=false)${R}" "review_required=${YL}true${R}"
tool "policy.apply ${D}(approved=true)${R}"  "applied=${GR}true${R} · egress=[api.stripe.com]"

step "report + remember" "close the loop"
tool "risk-report" "${B}./.asterguard/report.html${R} ${D}(SCA · attack path · red-team · policies)${R}"
tool "memory.capture" "mem_7f3c captured ${D}{tenant:demo, team:sec}${R}"
tool "memory.recall ${D}(warm)${R}" "1 memory: \"anon admin export forbidden; tokenize + allowlist\""

sleep 0.4
p ""
p "${GR}${B}✓ Loop closed.${R}${D} The team now knows support-agent better than it did 60 seconds ago.${R}"
sleep 1.6
