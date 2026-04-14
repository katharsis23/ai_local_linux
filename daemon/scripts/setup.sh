#!/usr/bin/env bash
# =============================================================================
# Setup script for ai_local_daemon
# =============================================================================

set -euo pipefail  # Strict mode: exit on error, undefined vars, pipe failures

# ====================== Colors ======================
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'  # No Color

# ====================== Logging Functions ======================
log_info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ====================== Variables ======================
SOCK_DIR="/run/user/$(id -u)/ai_local_daemon"
SOCK_PATH="$SOCK_DIR/app.sock"

# ====================== Main Setup ======================

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   ai_local_daemon Setup Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo

log_info "Starting setup..."

# 1. Create socket directory
log_info "Creating socket directory: $SOCK_DIR"
if [ ! -d "$SOCK_DIR" ]; then
    mkdir -p "$SOCK_DIR"
    log_success "Socket directory created"
else
    log_info "Socket directory already exists"
fi

# 2. Check and install system dependencies (Arch Linux)
log_info "Checking system dependencies..."
if ! command -v poetry >/dev/null 2>&1; then
    log_info "Installing Poetry and python-dotenv via pacman..."
    sudo pacman -S --needed python-poetry python-dotenv
    log_success "System packages installed"
else
    log_info "Poetry is already installed"
fi

# 3. Install Python dependencies
log_info "Installing project dependencies with Poetry..."
if poetry install --no-root; then
    log_success "Dependencies installed successfully"
else
    log_error "Failed to install dependencies"
    exit 1
fi

# 4. Optional: Run linting / checks before starting
read -p "Run linting and checks before starting? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Running code checks..."
    if poetry run inv dev.check 2>/dev/null || poetry run inv check 2>/dev/null; then
        log_success "All checks passed"
    else
        log_warning "Some checks failed. Continuing anyway..."
    fi
fi

# 5. Start the daemon
log_info "Starting the development daemon..."
echo -e "${BLUE}────────────────────────────────────────${NC}"

# Run the dev server
poetry run inv dev.server || poetry run inv dev

echo
log_success "Setup completed successfully!"
log_info "Daemon should now be running on socket: $SOCK_PATH"

# Optional: Show useful next commands
echo
echo -e "${BLUE}Useful commands:${NC}"
echo "  poetry run inv --list          → Show all available tasks"
echo "  poetry run inv dev.server      → Start daemon"
echo "  poetry run inv test            → Run tests"
echo "  poetry run inv dev.lint        → Run linter"

exit 0