#!/usr/bin/env bash
# Stand up a LOCAL AsterVault MCP gateway for a Claude Code demo — no IdP, no cloud, no Postgres.
# Generates a dev RSA keypair + a permissive dev policy + an 8h JWT, then prints the serve command
# and the .mcp.json block to paste into Claude Code. DEV ONLY — localhost, short-lived, no secrets.
#
# Usage:  ASTERVAULT_DIR=~/Nexcraft/astervault ./setup-dev-gateway.sh
set -euo pipefail
AV="${ASTERVAULT_DIR:-$HOME/Nexcraft/astervault}"
OUT="${OUT_DIR:-$PWD/.astervault-dev}"; mkdir -p "$OUT"
PORT="${PORT:-8080}"
ISS="https://auth.local"; AUD="https://astervault.local"

python3 - "$OUT" "$ISS" "$AUD" <<'PY'
import sys, datetime, jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
out, iss, aud = sys.argv[1], sys.argv[2], sys.argv[3]
k = rsa.generate_private_key(public_exponent=65537, key_size=2048)
priv = k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
pub = k.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
open(out+"/dev_pub.pem","w").write(pub)
open(out+"/dev_policy.yaml","w").write(
  'default_deny_reason: "dev-deny"\nrules:\n'
  '  - match: {operation: "secanalysis.*", resource: "secanalysis"}\n    effect: allow\n    mode: "B"\n'
  '  - match: {operation: "registry.*", resource: "registry"}\n    effect: allow\n    mode: "0"\n')
tok = jwt.encode({"sub":"agent-demo","aud":aud,"iss":iss,"groups":["security-agents"],
  "tenant":"demo","team":"sec",
  "exp":datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=8)}, priv, algorithm="RS256")
open(out+"/dev_jwt.txt","w").write(tok)
print("wrote dev_pub.pem, dev_policy.yaml, dev_jwt.txt to", out)
PY

JWT="$(cat "$OUT/dev_jwt.txt")"
cat > "$OUT/mcp.json" <<JSON
{
  "mcpServers": {
    "astervault": {
      "type": "http",
      "url": "http://localhost:${PORT}/mcp",
      "headers": { "Authorization": "Bearer ${JWT}" }
    }
  }
}
JSON

cat <<MSG

── 1. Start the gateway (leave running) ───────────────────────────────────────
cd "$AV"
ASTERVAULT_JWT_PUBLIC_KEY="\$(cat "$OUT/dev_pub.pem")" \\
ASTERVAULT_POLICY_PATH="$OUT/dev_policy.yaml" \\
ASTERVAULT_DEFAULT_BACKEND=none ASTERVAULT_PORT=$PORT \\
ASTERVAULT_RESOURCE_ID=$AUD ASTERVAULT_ISSUER=$ISS \\
python3 -c "import sys;sys.argv=['astervault','serve','--transport','streamable-http'];from astervault.cli import main;main()"

── 2. Point Claude Code at it ──────────────────────────────────────────────────
Copy $OUT/mcp.json into your project's .mcp.json (or merge the "astervault" entry).
Then in Claude Code: /mcp  → you should see the astervault server with 26 tools.

── 3. Drive the pipeline ───────────────────────────────────────────────────────
Install the skills (/plugin install asterguard-security@...) and ask:
  "resolve this finding, plant a canary and red-team the export path, then remediate."
MSG
