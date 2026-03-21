#!/bin/bash
set -euo pipefail

# Exit if no argument is provided
if [ -z "$1" ]; then
  echo "Error: Missing app name argument."
  echo "Usage: $0 <app_name> <release>"
  exit 1
fi

# Exit if no argument is provided
if [ -z "$2" ]; then
  echo "Error: Missing release argument."
  echo "Usage: $0 <app_name> <release>"
  exit 1
fi

APP="$1"
RELEASE="$2"
# Sanitize release name for use in filenames (replace / with -)
RELEASE_SAFE="${RELEASE//\//-}"
STATE_DIR=".deploy_state"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${STATE_DIR}/${APP}_${RELEASE_SAFE}_${TIMESTAMP}.log"

# Create state directory if it doesn't exist
mkdir -p "$STATE_DIR"

# Function to log with timestamp
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Function to check if a step was completed
step_completed() {
  local step_name="$1"
  local marker_file="${STATE_DIR}/${APP}_${RELEASE_SAFE}_${step_name}.done"
  [[ -f "$marker_file" ]]
}

# Function to mark a step as completed
mark_step_completed() {
  local step_name="$1"
  local marker_file="${STATE_DIR}/${APP}_${RELEASE_SAFE}_${step_name}.done"
  touch "$marker_file"
  log "✅ Step '$step_name' completed"
}

# Start deployment
log "🚀 Starting deployment: app=$APP, release=$RELEASE"

# Step 1: Target Group Deployment (idempotent by design)
if step_completed "target_group"; then
  log "⏭️  Skipping target group deployment (already completed)"
else
  log "📦 Deploying target group..."
  python ./tools/target_group_deploy.py -c "$APP/$APP.yaml" --non-interactive 2>&1 | tee -a "$LOG_FILE"
  mark_step_completed "target_group"
fi

# Step 2: Networking Deployment (idempotent by design)
if step_completed "networking"; then
  log "⏭️  Skipping networking deployment (already completed)"
else
  log "🌐 Deploying networking rules..."
  python ./tools/networking_deploy.py "$APP/$APP.yaml" 2>&1 | tee -a "$LOG_FILE"
  mark_step_completed "networking"
fi

# Step 3: Code Deployment
if step_completed "code"; then
  log "⏭️  Skipping code deployment (already completed)"
else
  log "💻 Deploying code..."
  ./tools/code_deploy.sh "$APP" "$RELEASE" 2>&1 | tee -a "$LOG_FILE"
  mark_step_completed "code"
fi

log "✅ Deployment completed successfully!"
log "📄 Log file: $LOG_FILE"

# Optional: Clean up old state markers (keep only last 5 deployments)
ls -t "${STATE_DIR}/${APP}_"*".done" 2>/dev/null | tail -n +16 | xargs rm -f 2>/dev/null || true