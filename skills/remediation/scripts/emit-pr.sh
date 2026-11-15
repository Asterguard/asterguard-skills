#!/usr/bin/env bash
# Open a remediation PR from an `asterguard_remediation.to_pr(...)` bundle (JSON on stdin or $1).
# Writes each file into the target repo, commits on a branch, and opens a PR via gh.
# The PR review IS the approval gate — nothing is enforced until it merges.
#
# Usage:
#   asterguard_remediation ...to_pr(...) | emit-pr.sh --repo /path/to/repo
#   emit-pr.sh --repo /path/to/repo bundle.json
set -euo pipefail

repo="."
bundle=""
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) repo="$2"; shift 2 ;;
    *) bundle="$1"; shift ;;
  esac
done
json="$( [ -n "$bundle" ] && cat "$bundle" || cat )"

command -v jq >/dev/null || { echo "jq required" >&2; exit 2; }
command -v gh >/dev/null || { echo "gh (GitHub CLI) required" >&2; exit 2; }

branch="$(printf '%s' "$json" | jq -r '.branch')"
title="$(printf '%s' "$json" | jq -r '.title')"
body="$(printf '%s' "$json" | jq -r '.body')"

cd "$repo"
base="$(git rev-parse --abbrev-ref HEAD)"
git switch -c "$branch"

# write each file at its path
printf '%s' "$json" | jq -c '.files[]' | while read -r f; do
  path="$(printf '%s' "$f" | jq -r '.path')"
  mkdir -p "$(dirname "$path")"
  printf '%s' "$f" | jq -r '.content' > "$path"
  git add "$path"
done

git commit -q -m "$title"
git push -q -u origin "$branch"
gh pr create --base "$base" --head "$branch" --title "$title" --body "$body"
echo "opened PR: $title  ($branch -> $base)"
