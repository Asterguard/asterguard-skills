#!/usr/bin/env bash
# Emit the Codex target from the same skill source. Claude Code reads skills/ directly via the
# marketplace; Codex consumes an AGENTS.md + the skill bodies. One source, two targets.
# Output: ./dist/codex/  (drop into a Codex project, or point Codex's skills path at it)
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
out="$root/dist/codex"
rm -rf "$out"; mkdir -p "$out/skills"

# 1) copy skill bodies (SKILL.md + references, minus any scripts that are Claude-specific)
for d in "$root"/skills/*/; do
  name="$(basename "$d")"
  mkdir -p "$out/skills/$name"
  cp "$d/SKILL.md" "$out/skills/$name/"
  [ -d "$d/references" ] && cp -R "$d/references" "$out/skills/$name/" || true
done
cp -R "$root/docs" "$out/docs"

# 2) synthesize AGENTS.md as the Codex entrypoint from each skill's frontmatter
agents="$out/AGENTS.md"
{
  echo "# AsterGuard Security — agent instructions (Codex target)"
  echo
  echo "Local, agent-native AppSec. Connect to the AsterVault MCP gateway for all proprietary"
  echo "analysis (registry.resolve, controls.map, graph.enrich, risk.score, testgen.patterns,"
  echo "scan.plan). Perform scans locally; build graphs to docs/graph-schema.md. Activate a skill"
  echo "below when its trigger matches."
  echo
  for f in "$out"/skills/*/SKILL.md; do
    name="$(awk -F': ' '/^name:/{print $2; exit}' "$f")"
    desc="$(awk -F': ' '/^description:/{sub(/^description: /,""); print; exit}' "$f")"
    echo "## $name"
    echo "$desc"
    echo "See skills/$name/SKILL.md"
    echo
  done
} > "$agents"

echo "built Codex target → $out"
echo "  skills: $(ls "$out/skills" | wc -l | tr -d ' ')   AGENTS.md: $(wc -l < "$agents") lines"
