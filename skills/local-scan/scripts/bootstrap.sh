#!/usr/bin/env bash
# Deliver the raw collectors the local-scan skill shells out to. Open-source tools only — no
# AsterGuard knowledge is installed here (that lives behind the AsterVault MCP gateway).
# Usage: bootstrap.sh [grype|syft|checkov|trufflehog|all]
set -euo pipefail
want="${1:-all}"

have() { command -v "$1" >/dev/null 2>&1; }

install_grype()      { have grype      || { have brew && brew install grype      || curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b "$HOME/.local/bin"; }; }
install_syft()       { have syft       || { have brew && brew install syft       || curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh  | sh -s -- -b "$HOME/.local/bin"; }; }
install_checkov()    { have checkov    || { have pipx && pipx install checkov    || pip install --user checkov; }; }
install_trufflehog() { have trufflehog || { have brew && brew install trufflehog  || curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b "$HOME/.local/bin"; }; }

case "$want" in
  grype) install_grype ;;
  syft) install_syft ;;
  checkov) install_checkov ;;
  trufflehog) install_trufflehog ;;
  all) install_syft; install_grype; install_checkov; install_trufflehog ;;
  *) echo "unknown collector: $want" >&2; exit 2 ;;
esac

echo "collectors present:"
for t in syft grype checkov trufflehog; do printf "  %-12s %s\n" "$t" "$(have "$t" && command -v "$t" || echo MISSING)"; done
