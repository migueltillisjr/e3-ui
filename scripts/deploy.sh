#!/bin/bash
# Convenience wrapper — runs the full cicd pipeline for e3
# Usage: ./scripts/deploy.sh <release>
#   e.g. ./scripts/deploy.sh main
#   e.g. ./scripts/deploy.sh release-1.0.1
set -euo pipefail

RELEASE=${1:?Usage: ./scripts/deploy.sh <release>}

cd "$(dirname "$0")/../cicd"
./deploy.sh e3 "$RELEASE"
