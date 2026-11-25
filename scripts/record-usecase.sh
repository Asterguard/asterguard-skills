#!/usr/bin/env bash
# Record an offensive use-case video — the capture scaffold.
#
# The s1–s4 scenario videos are the PROOF the skills work: a real authorized pentest run of
# the `pentest` playbook to a canary-proven break. This helper sets up the capture and prints
# the scenario's beats so the recording stays on-script. It does NOT commit anything: the
# finished .mp4 is uploaded to the video host (agenticrisklabs.io/videos/) and referenced from
# the docs — the repo never carries the binary (no binary churn in history).
#
# Usage:  scripts/record-usecase.sh <s1|s2|s3|s4>
set -euo pipefail
cd "$(dirname "$0")/.."

SID="${1:-}"
case "$SID" in
  s1|s2|s3|s4) ;;
  *) echo "usage: scripts/record-usecase.sh <s1|s2|s3|s4>" >&2; exit 1;;
esac

DOC="$(ls use-cases/${SID}-*.md 2>/dev/null | head -1 || true)"
[ -n "$DOC" ] || { echo "no scenario doc use-cases/${SID}-*.md" >&2; exit 1; }

OUT_DIR="use-cases/media/.local"     # gitignored — captures never get committed
mkdir -p "$OUT_DIR"
OUT="${OUT_DIR}/${SID}.mp4"

echo "=== Recording ${SID} ==="
echo "scenario doc : ${DOC}"
echo "local output : ${OUT}  (gitignored; upload, don't commit)"
echo
echo "--- The beats to follow (from the doc's Video section) ---"
awk '/^## Video/{f=1} f{print}  /^## /{if(f && !/^## Video/) exit}' "$DOC" | sed 's/^/  /'
echo
echo "--- Prerequisites (see use-cases/README.md) ---"
echo "  • offensive tier deployed + ASTERGUARD_OFFENSIVE_TOKEN minted"
echo "  • demo agents stood up (/opt/asterix/demo-apps) and reachable over the tunnel"
echo "  • asterguard-security plugin installed in Claude Code, connected to the gateway"
echo

# Prefer a screen capture of the real Claude Code session. On macOS, screencapture can record
# a region to video; ffmpeg (avfoundation) is the scriptable alternative. Terminal-only beats
# can use `vhs` if a tape exists.
if [ -f "use-cases/media/tapes/${SID}.tape" ] && command -v vhs >/dev/null 2>&1; then
  echo "==> vhs tape found — rendering use-cases/media/tapes/${SID}.tape"
  vhs "use-cases/media/tapes/${SID}.tape" -o "$OUT"
elif command -v ffmpeg >/dev/null 2>&1 && [ "$(uname)" = "Darwin" ]; then
  echo "==> ffmpeg available. To record the main display (⌃C to stop):"
  echo "    ffmpeg -f avfoundation -framerate 30 -i \"1:none\" -pix_fmt yuv420p \"$OUT\""
  echo "    (list devices: ffmpeg -f avfoundation -list_devices true -i \"\")"
else
  echo "==> No scripted recorder found. Capture the Claude Code session manually:"
  echo "    macOS: ⇧⌘5 → Record Selected Portion → save, then export/transcode to ${OUT}"
fi

echo
echo "--- After recording ---"
echo "  1. upload ${OUT} to the video host as:  videos/${SID}.mp4"
echo "  2. the doc already points at https://agenticrisklabs.io/videos/${SID}.mp4"
echo "  3. fill the doc's Result section with the real ASR + the canary hit (the proof)"
