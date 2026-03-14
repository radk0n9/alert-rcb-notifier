#!/bin/bash
set -euo pipefail

# ─────────────────────────────────────────────
# alert-rcb VPS setup script — Ubuntu
# Run as a non-root user with sudo access
# ─────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()    { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

ask() {
    # ask <question> — returns 0 (yes) or 1 (no)
    local prompt="$1"
    while true; do
        read -rp "$(echo -e "${YELLOW}[?]${NC}    $prompt [y/n]: ")" answer
        case "$answer" in
            [Yy]*) return 0 ;;
            [Nn]*) return 1 ;;
            *) echo "  Please answer y or n." ;;
        esac
    done
}

run_spinner() {
    # run_spinner <label> <cmd> [args...]
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

# ── Checks ────────────────────────────────────

if [ "$EUID" -eq 0 ]; then
    error "Do not run this script as root. Use a regular user with sudo access."
fi

if ! command -v sudo &>/dev/null; then
    error "sudo is required but not installed."
fi

info "Starting alert-rcb VPS setup..."

# ── System update ─────────────────────────────

run_spinner "Updating package lists..." sudo apt-get update -qq
if ask "Run full system upgrade? (recommended on fresh VPS)"; then
    run_spinner "Upgrading system packages..." sudo apt-get upgrade -qq -y
else
    info "Skipping system upgrade."
fi

# ── Docker ────────────────────────────────────

if command -v docker &>/dev/null; then
    warn "Docker already installed: $(docker --version)"
else
    run_spinner "Installing dependencies..." sudo apt-get install -qq -y ca-certificates curl gnupg

    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/ubuntu \
        $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
        | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    run_spinner "Installing Docker..." sudo apt-get install -qq -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    info "Docker installed: $(docker --version)"
fi

# ── Docker group ──────────────────────────────

if groups "$USER" | grep -q docker; then
    warn "User $USER is already in the docker group."
else
    info "Adding $USER to the docker group..."
    sudo usermod -aG docker "$USER"
    warn "Group change requires logout/login to take effect. Use 'newgrp docker' for this session."
fi

# ── Verify Docker Compose ─────────────────────

if ! sudo docker compose version &>/dev/null; then
    run_spinner "Installing Docker Compose plugin..." sudo apt-get install -qq -y docker-compose-plugin
fi
info "Docker Compose available: $(sudo docker compose version)"

# ── App setup ─────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"

info "App directory: $APP_DIR"

# Create persistent data directories
mkdir -p "$APP_DIR/app/db"
mkdir -p "$APP_DIR/logs"
info "Created data directories."

# ── .env setup ────────────────────────────────

if [ ! -f "$APP_DIR/.env" ]; then
    if [ ! -f "$APP_DIR/.env.example" ]; then
        error ".env.example not found. Cannot create .env."
    fi
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    info ".env created from .env.example."
fi

# ── Check .env is configured ──────────────────

env_configured() {
    ! grep -q "your_bot_token_here\|your_group_id_here" "$APP_DIR/.env" 2>/dev/null
}

while ! env_configured; do
    warn ".env still contains placeholder values — credentials must be set before starting."
    if ask "Open .env in nano now?"; then
        nano "$APP_DIR/.env"
    else
        warn "Skipping .env edit. You can edit it later:"
        echo ""
        echo "  nano $APP_DIR/.env"
        echo "  sudo docker compose -f $APP_DIR/docker-compose.yml up -d"
        echo ""
        exit 0
    fi
done

info ".env looks configured."

warn "Log out and back in (or run 'newgrp docker') to use docker without sudo."
info "Setup complete. To start the app run:"
echo ""
echo "  ./scripts/run.sh          # production"
echo "  ./scripts/run.sh --test   # test mode"
echo ""
