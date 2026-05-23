#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${PIPELINE_DATA_DIR:-/mnt/hermes-free/lead-pipeline}"
BATCH_ID="${SMOKE_BATCH_ID:-smoke-test}"
INPUT_CSV="${ROOT_DIR}/data/sample-batch.csv"
EXPORT_DIR="${DATA_DIR}/exports"
LOG_DIR="${DATA_DIR}/logs"
EXPORT_CSV="${EXPORT_DIR}/${BATCH_ID}.csv"
LOG_FILE="${LOG_DIR}/smoke-test.log"

fail() {
  echo "SMOKE FAIL: $1" >&2
  exit 1
}

run_step() {
  echo "+ $*" | tee -a "$LOG_FILE"
  "$@" >>"$LOG_FILE" 2>&1
}

mkdir -p "$EXPORT_DIR" "$LOG_DIR"
: >"$LOG_FILE"

cd "$ROOT_DIR"

command -v leadpipe >/dev/null 2>&1 || fail "brak komendy leadpipe w PATH; uruchom pip install -e . albo aktywuj .venv"
test -f "$INPUT_CSV" || fail "brak fixture CSV: $INPUT_CSV"

run_step leadpipe import "$INPUT_CSV" --source smoke-test
run_step leadpipe scan --batch "$BATCH_ID" --layers t0,t1,t0_5 --concurrency 10
run_step leadpipe decide --batch "$BATCH_ID"
run_step leadpipe export --batch "$BATCH_ID" --format csv

if [[ ! -f "$EXPORT_CSV" ]]; then
  FOUND_EXPORT="$(find "$EXPORT_DIR" -maxdepth 1 -type f -name "*${BATCH_ID}*.csv" | head -n 1 || true)"
  [[ -n "$FOUND_EXPORT" ]] || fail "nie znaleziono eksportu CSV w $EXPORT_DIR"
  EXPORT_CSV="$FOUND_EXPORT"
fi

LINE_COUNT="$(wc -l <"$EXPORT_CSV" | tr -d ' ')"
if [[ "$LINE_COUNT" -lt 2 ]]; then
  fail "CSV eksportu nie ma leadow: $EXPORT_CSV"
fi

echo "SMOKE OK"
echo "CSV: $EXPORT_CSV"
echo "Log: $LOG_FILE"
