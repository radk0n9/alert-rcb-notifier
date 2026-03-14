#!/bin/bash
set -euo pipefail

# ─────────────────────────────────────────────
# alert-rcb run script
# Usage: ./scripts/run.sh [--test]
# ─────────────────────────────────────────────

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

run_spinner() {
    local label="$1"; shift
    local tmpfile; tmpfile=$(mktemp)
    "$@" >"$tmpfile" 2>&1 &
    local pid=$! frames='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏' i=0
    while kill -0 "$pid" 2>/dev/null; do
        printf "\r  \e[36m${frames:$i:1}\e[0m  %s" "$label"
        i=$(( (i + 1) % 10 ))
        sleep 0.1
    done
    wait "$pid"
    local code=$?
    if [ $code -eq 0 ]; then
        printf "\r${GREEN}[INFO]${NC}  %s\n" "$label"
    else
        printf "\r${RED}[ERROR]${NC} %s failed:\n" "$label"
        cat "$tmpfile"
        rm -f "$tmpfile"
        exit $code
    fi
    rm -f "$tmpfile"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE="sudo docker compose -f $APP_DIR/docker-compose.yml"

TEST_MODE=false
if [[ "${1:-}" == "--test" ]]; then
    TEST_MODE=true
fi

# ── Checks ────────────────────────────────────

if [ ! -f "$APP_DIR/.env" ]; then
    error ".env not found. Run scripts/setup-vps.sh first or copy .env.example to .env."
fi

if grep -q "your_bot_token_here\|your_group_id_here" "$APP_DIR/.env" 2>/dev/null; then
    error ".env still contains placeholder values. Edit $APP_DIR/.env before running."
fi

# ── Build ─────────────────────────────────────

run_spinner "Building Docker image..." $COMPOSE build

# ── Run ───────────────────────────────────────

if $TEST_MODE; then
    run_spinner "Starting test service..." $COMPOSE --profile test up -d test
    info "Test container running."
    echo ""
    echo "  docker compose logs -f test                      # follow logs"
    echo "  docker compose --profile test down               # stop"
    echo ""
else
    run_spinner "Starting app service..." $COMPOSE up -d app
    info "Container running."
    echo ""
    echo "  docker compose logs -f                           # follow logs"
    echo "  docker compose down                              # stop"
    echo ""
fi

$COMPOSE ps
