#!/bin/sh
# Create the team-memory vector collections in Qdrant from collections.json (idempotent).
# Usage: QDRANT_URL=http://localhost:6333 ASTERGUARD_EMBED_DIM=1536 sh create-collections.sh
set -eu

QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
DIM="${ASTERGUARD_EMBED_DIM:-1536}"
DIST="Cosine"

# No jq in the init image — the collection set is small and fixed, so declare it inline here and keep
# collections.json as the human-readable spec of record. Edit both together if you add a collection.
create() {
  name="$1"
  # PUT is create-or-noop in Qdrant; tolerate "already exists".
  code=$(curl -s -o /tmp/resp -w '%{http_code}' -X PUT "$QDRANT_URL/collections/$name" \
    -H 'Content-Type: application/json' \
    -d "{\"vectors\":{\"size\":$DIM,\"distance\":\"$DIST\"}}" || true)
  if [ "$code" = "200" ] || [ "$code" = "409" ]; then
    echo "collection '$name' ready ($code)"
  else
    echo "collection '$name' -> HTTP $code: $(cat /tmp/resp 2>/dev/null)"
  fi
}

index() {
  name="$1"; field="$2"; schema="$3"
  curl -s -o /dev/null -X PUT "$QDRANT_URL/collections/$name/index" \
    -H 'Content-Type: application/json' \
    -d "{\"field_name\":\"$field\",\"field_schema\":\"$schema\"}" || true
}

echo "Creating AsterGuard team-memory collections at $QDRANT_URL (dim=$DIM) ..."

create "security_memory"
for f in tenant team app weakness_id kind memory_id; do index "security_memory" "$f" "keyword"; done
index "security_memory" "promoted" "bool"

create "engagement_context"
for f in tenant team app engagement_id; do index "engagement_context" "$f" "keyword"; done

echo "Done. (The MCP server populates vectors; these are empty collections with the correct schema.)"
