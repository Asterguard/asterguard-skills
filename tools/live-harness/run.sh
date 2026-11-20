#!/usr/bin/env bash
# Launch the live offensive harness server.
#
# Expects the gateway + target configured in the environment (see README.md):
#   ASTERVAULT_MCP_URL, ASTERVAULT_BEARER or ASTERVAULT_BEARER_FILE
#   TARGET_INVOKE_URL  (and optionally TARGET_DB / TARGET_EGRESS_LOG / TARGET_REQUIREMENTS)
# Optional adaptive model attacker (adds per-move reasoning):
#   ATTACKER_API_BASE, ATTACKER_API_KEY, ATTACKER_MODEL
#
# Then open http://127.0.0.1:${PORT:-8777}
set -euo pipefail
cd "$(dirname "$0")"
PORT="${PORT:-8777}"
: "${ASTERVAULT_BEARER:=}"; : "${ASTERVAULT_BEARER_FILE:=}"
if [ -z "$ASTERVAULT_BEARER" ] && [ -z "$ASTERVAULT_BEARER_FILE" ]; then
  echo "ERROR: set ASTERVAULT_BEARER or ASTERVAULT_BEARER_FILE (gateway bearer JWT)"; exit 1
fi
echo "live-harness on http://127.0.0.1:${PORT}  (attacker: ${ATTACKER_API_BASE:+model ${ATTACKER_MODEL:-?}}${ATTACKER_API_BASE:-gateway deterministic})"
exec uvicorn server:app --host 127.0.0.1 --port "$PORT"
