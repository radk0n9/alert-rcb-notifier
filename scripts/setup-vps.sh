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

# ── Checks ────────────────────────────────────

if [ "$EUID" -eq 0 ]; then
    error "Do not run this script as root. Use a regular user with sudo access."
fi

if ! command -v sudo &>/dev/null; then
    error "sudo is required but not installed."
fi

info "Starting alert-rcb VPS setup..."

# ── System update ─────────────────────────────

info "Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

# ── Docker ────────────────────────────────────

if command -v docker &>/dev/null; then
    warn "Docker already installed: $(docker --version)"
else
    info "Installing Docker..."
    sudo apt-get install -y ca-certificates curl gnupg

    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/ubuntu \
        $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
        | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

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

if ! docker compose version &>/dev/null; then
    info "Docker Compose plugin not found. Installing..."
    sudo apt-get install -y docker-compose-plugin
fi
info "Docker Compose available: $(docker compose version)"

# ── App setup ─────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"

info "App directory: $APP_DIR"

# Create persistent data directories
mkdir -p "$APP_DIR/app/db"
mkdir -p "$APP_DIR/logs"
info "Created data directories."

# ── .env setup ────────────────────────────────

if [ -f "$APP_DIR/.env" ]; then
    warn ".env already exists, skipping."
else
    if [ -f "$APP_DIR/.env.example" ]; then
        cp "$APP_DIR/.env.example" "$APP_DIR/.env"
        warn ".env created from .env.example — fill in your credentials before starting:"
        warn "  nano $APP_DIR/.env"
    else
        error ".env.example not found. Cannot create .env."
    fi
fi

# ── Check .env is configured ──────────────────

if grep -q "your_bot_token_here" "$APP_DIR/.env" 2>/dev/null; then
    warn "⚠  .env still contains placeholder values."
    warn "   Edit $APP_DIR/.env before running 'docker compose up'."
    echo ""
    echo "  nano $APP_DIR/.env"
    echo ""
    exit 0
fi

# ── Build and start container ─────────────────

info "Building Docker image..."
docker compose -f "$APP_DIR/docker-compose.yml" build

info "Starting container..."
newgrp docker <<NEWGRP
    docker compose -f "$APP_DIR/docker-compose.yml" up -d
NEWGRP

info "Container started. Useful commands:"
echo ""
echo "  docker compose logs -f        # follow logs"
echo "  docker compose ps             # check status"
echo "  docker compose down           # stop"
echo "  docker compose up -d --build  # rebuild and restart"
echo ""
info "Setup complete."
