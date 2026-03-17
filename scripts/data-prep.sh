#!/bin/bash
# =============================================================================
# Data Preparation Pipeline (e3-ui)
# =============================================================================

set -euo pipefail

# -- Logging helpers ----------------------------------------------------------
LOG_FILE="storage/data-prep-$(date +%Y%m%d_%H%M%S).log"
STEP=0
FAILED=0
PASSED=0
PIPELINE_START=$(date +%s)

# Test data lives in the e3 repo (sibling directory)
E3_DATA_DIR="../e3/storage/data"

log()  { local ts; ts=$(date '+%Y-%m-%d %H:%M:%S'); printf "[%s] %s\n" "$ts" "$*" | tee -a "$LOG_FILE"; }
info() { log "INFO  $*"; }
warn() { log "WARN  $*"; }
err()  { log "ERROR $*"; }

run_step() {
  STEP=$((STEP + 1))
  local label="$1"; shift
  local step_start; step_start=$(date +%s)

  info "── Step $STEP: $label ──"

  if "$@" >> "$LOG_FILE" 2>&1; then
    local elapsed=$(( $(date +%s) - step_start ))
    info "✅ Step $STEP passed (${elapsed}s)"
    PASSED=$((PASSED + 1))
  else
    local elapsed=$(( $(date +%s) - step_start ))
    err  "❌ Step $STEP FAILED (${elapsed}s) — command: $*"
    FAILED=$((FAILED + 1))
  fi
  echo "" | tee -a "$LOG_FILE"
}

# -- Pre-flight ---------------------------------------------------------------
mkdir -p storage/contacts
mkdir -p storage/database
mkdir -p "$(dirname "$LOG_FILE")"
info "Pipeline started — log: $LOG_FILE"
echo ""

# -- Steps --------------------------------------------------------------------

run_step "Clean existing contacts" \
  rm -f storage/contacts/*

run_step "Create DB schema" \
  python -m agents.NaturalLanguageDatabase.initializedb

run_step "Load original contacts (27k export)" \
  python -m agents.NaturalLanguageDatabase.tsv_to_db_original_contacts \
  "$E3_DATA_DIR/master_contact_lists"

run_step "Import validated contacts (TSV)" \
  python -m agents.NaturalLanguageDatabase.tsv_to_db_validated_contacts tsv \
  "$E3_DATA_DIR/prod/dbload_validated/tsv"

run_step "Import validated contacts (CSV)" \
  python -m agents.NaturalLanguageDatabase.tsv_to_db_validated_contacts csv \
  "$E3_DATA_DIR/prod/dbload_validated/csv"

run_step "Validate NLDB responses" \
  python -m agents.NaturalLanguageDatabase.query

run_step "NLDB query + TSV generation" \
  python -m agents.NaturalLanguageDatabase "return all validated contacts"

# Verify the export file exists
if [ -f "$PWD/storage/contacts/contacts.tsv" ]; then
  info "  ↳ contacts.tsv exists ($(wc -l < "$PWD/storage/contacts/contacts.tsv") lines)"
else
  warn "  ↳ contacts.tsv not found after export"
fi

run_step "Fetch email metrics" \
  python -m agents.NaturalLanguageEmailer_Mailgun metrics

if [ -f "$PWD/storage/metrics/email_metrics_current.png" ]; then
  info "  ↳ email_metrics_current.png present"
else
  warn "  ↳ email_metrics_current.png not found"
fi

TEST_EMAIL="christopher.poznanski@csd15.net"

run_step "Gather contacts subset for validation" \
  python -m agents.NaturalLanguageDatabase \
  "return contact with email ${TEST_EMAIL} that is not valid"

run_step "Run email validation" \
  python -m agents.NaturalLanguageContactsValidator \
  "validate the contact with email ${TEST_EMAIL}"

# -- Post-validation DB checks ------------------------------------------------
info "── Post-validation checks ──"

validated_row=$(python -c '
import sqlite3, json
conn = sqlite3.connect("storage/database/crm.db")
conn.row_factory = sqlite3.Row
row = conn.execute("SELECT * FROM crm_contacts WHERE email = ?",
                    ("migueltillisjr@gmail.com",)).fetchone()
print(json.dumps(dict(row)) if row else "")
' 2>>"$LOG_FILE")

if [ -n "$validated_row" ]; then
  info "  ↳ Validated contact found: $validated_row"
else
  warn "  ↳ Validated contact (migueltillisjr@gmail.com) not found in DB"
fi

invalid_row=$(python -c "
import sqlite3, json
conn = sqlite3.connect('storage/database/crm.db')
conn.row_factory = sqlite3.Row
row = conn.execute('SELECT * FROM crm_contacts WHERE email = ?',
                    ('${TEST_EMAIL}',)).fetchone()
print(json.dumps(dict(row)) if row else '')
" 2>>"$LOG_FILE")

if [ -z "$invalid_row" ]; then
  info "  ✅ Invalid contact (${TEST_EMAIL}) correctly removed"
else
  err  "  ❌ Invalid contact still in DB: $invalid_row"
  FAILED=$((FAILED + 1))
fi

# -- Summary ------------------------------------------------------------------
TOTAL_ELAPSED=$(( $(date +%s) - PIPELINE_START ))
echo "" | tee -a "$LOG_FILE"
info "================================================"
info "Pipeline finished in ${TOTAL_ELAPSED}s"
info "  Steps passed : $PASSED"
info "  Steps failed : $FAILED"
info "  Log file     : $LOG_FILE"
info "================================================"

if [ "$FAILED" -gt 0 ]; then
  exit 1
fi
