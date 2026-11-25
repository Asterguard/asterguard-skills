#!/usr/bin/env bash
# Cut a release — guarded, idempotent, and never a surprise.
#
# Runs the same sequence we follow by hand, with every gate enforced:
#   1. on master, clean tree, up to date with origin/master
#   2. the hermetic smoke gate passes (scripts/smoke.py)
#   3. roll CHANGELOG.md [Unreleased] -> [X.Y.Z] - <today>, open a fresh Unreleased, fix links
#   4. commit the changelog, tag vX.Y.Z (annotated), push master + tag
#   5. create the GitHub release with auto-generated notes
#
# Nothing is pushed until every gate passes. --dry-run does everything except commit/push/release.
#
# Usage:  scripts/release.sh <X.Y.Z | vX.Y.Z> [--dry-run]
set -euo pipefail

REPO_SLUG="Asterguard/asterguard-skills"
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

die() { echo "release: $*" >&2; exit 1; }

# ---- args -------------------------------------------------------------------
[ $# -ge 1 ] || die "usage: scripts/release.sh <X.Y.Z|vX.Y.Z> [--dry-run]"
RAW="$1"; shift
DRY_RUN=0
for a in "$@"; do case "$a" in --dry-run) DRY_RUN=1;; *) die "unknown arg: $a";; esac; done

VERSION="${RAW#v}"
echo "$VERSION" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+([-.][0-9A-Za-z.]+)?$' \
  || die "version must look like X.Y.Z (got '$RAW')"
TAG="v${VERSION}"
TODAY="$(date -u +%Y-%m-%d)"   # UTC — matches GitHub tag/release timestamps and keeps the changelog monotonic

echo "==> releasing ${TAG}  (dry-run=${DRY_RUN})"

# ---- tooling ----------------------------------------------------------------
command -v git >/dev/null || die "git not found"
command -v gh  >/dev/null || die "gh (GitHub CLI) not found"
command -v python3 >/dev/null || die "python3 not found"

# ---- gate 1: clean, current master -----------------------------------------
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
[ "$BRANCH" = "master" ] || die "must be on master (on '$BRANCH')"
[ -z "$(git status --porcelain)" ] || die "working tree is dirty — commit or stash first"
git fetch --quiet origin master
[ "$(git rev-parse HEAD)" = "$(git rev-parse origin/master)" ] \
  || die "local master is not in sync with origin/master — pull/push first"
if git rev-parse "$TAG" >/dev/null 2>&1 || git ls-remote --exit-code --tags origin "$TAG" >/dev/null 2>&1; then
  die "tag ${TAG} already exists (local or remote)"
fi

# ---- gate 2: hermetic smoke -------------------------------------------------
echo "==> smoke"
python3 scripts/smoke.py || die "smoke failed — not releasing"

# ---- gate 3: roll the changelog --------------------------------------------
[ -f CHANGELOG.md ] || die "CHANGELOG.md not found"
echo "==> rolling CHANGELOG.md: [Unreleased] -> [${VERSION}] - ${TODAY}"
python3 - "$VERSION" "$TODAY" "$REPO_SLUG" <<'PY' || die "changelog roll failed"
import re, sys, io
version, today, slug = sys.argv[1], sys.argv[2], sys.argv[3]
p = "CHANGELOG.md"
text = open(p, encoding="utf-8").read()

m = re.search(r"^## \[Unreleased\]\s*\n(.*?)(?=^## \[|\Z)", text, re.S | re.M)
if not m:
    sys.exit("no [Unreleased] section found")
body = m.group(1).strip()
# a section with only empty subheads counts as empty
stripped = re.sub(r"^###.*$", "", body, flags=re.M).strip()
if not stripped:
    sys.exit("[Unreleased] has no entries to release")

fresh_unreleased = "## [Unreleased]\n\n"
released = f"## [{version}] - {today}\n\n{body}\n\n"
text = text[:m.start()] + fresh_unreleased + released + text[m.end():]

# refresh the link refs at the bottom
text = re.sub(r"^\[Unreleased\]:.*$",
              f"[Unreleased]: https://github.com/{slug}/compare/v{version}...HEAD",
              text, flags=re.M)
if f"[{version}]:" not in text:
    text = text.rstrip() + f"\n[{version}]: https://github.com/{slug}/releases/tag/v{version}\n"
open(p, "w", encoding="utf-8").write(text)
print(f"  changelog: released {version} ({today})")
PY

if [ "$DRY_RUN" -eq 1 ]; then
  echo "==> dry-run: would commit CHANGELOG.md, tag ${TAG}, push, and create the GitHub release"
  echo "--- CHANGELOG.md diff ---"
  git --no-pager diff -- CHANGELOG.md || true
  git checkout -- CHANGELOG.md
  echo "==> dry-run complete (no changes kept)"
  exit 0
fi

# ---- gate 4: commit, tag, push ---------------------------------------------
echo "==> commit + tag + push"
git add CHANGELOG.md
git commit -m "chore(release): ${TAG}

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
git tag -a "$TAG" -m "${TAG}"
git push origin master
git push origin "$TAG"

# ---- gate 5: GitHub release -------------------------------------------------
echo "==> gh release create ${TAG}"
gh release create "$TAG" --repo "$REPO_SLUG" --title "$TAG" --generate-notes

echo "==> done: https://github.com/${REPO_SLUG}/releases/tag/${TAG}"
