#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Enterprise NGFW v2.0 - Automated Update Script
# ═══════════════════════════════════════════════════════════════════
#
# This script updates the active Enterprise NGFW installation by:
# 1. Stopping the systemd service
# 2. Syncing new code from a local directory or git repository
# 3. Updating Python dependencies
# 4. Running database migrations (Alembic)
# 5. Restarting the systemd service
#
# Usage: sudo ./update.sh
# ═══════════════════════════════════════════════════════════════════

set -e

# ==================== Colors and Formatting ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ==================== Configuration ====================
# Directory where new code is placed (e.g., via SCP, Shared Folder)
LOCAL_APP_DIR="$HOME/enterprise_ngfw" 
# Installation directory on the VM
INSTALL_DIR="/opt/enterprise-ngfw"
VENV_DIR="$INSTALL_DIR/venv"
SERVICE_NAME="enterprise-ngfw"
SERVICE_USER="ngfw"
SERVICE_GROUP="ngfw"

# GitHub repository (if updating directly from GitHub)
REPO_URL="https://github.com/waheeb71/enterprise-ngfw"

# ==================== Logging ====================
UPDATE_LOG="/var/log/enterprise-ngfw/update-$(date +%Y%m%d-%H%M%S).log"

log() { echo -e "$1" | tee -a "$UPDATE_LOG"; }
log_info() { log "${BLUE}[INFO]${NC} $1"; }
log_success() { log "${GREEN}[✓]${NC} $1"; }
log_warning() { log "${YELLOW}[!]${NC} $1"; }
log_error() { log "${RED}[✗]${NC} $1"; }
log_step() { log "\n${CYAN}${BOLD}[STEP $1/$2]${NC} $3"; }

# ==================== Main Update Flow ====================

clear
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     ${BOLD}🔄 Enterprise NGFW v2.0 - System Updater${NC}${CYAN}                    ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check root permissions
if [ "$EUID" -ne 0 ]; then 
    log_error "This script must be run as root (use sudo)"
    exit 1
fi

log_info "Starting update at $(date)"

# STEP 1: Stop Service
log_step 1 5 "Stopping $SERVICE_NAME service..."
if systemctl is-active --quiet "$SERVICE_NAME"; then
    systemctl stop "$SERVICE_NAME"
    log_success "Service stopped"
else
    log_warning "Service is not currently running"
fi

# STEP 2: Sync Code
log_step 2 5 "Syncing new source code..."
if [ -d "$LOCAL_APP_DIR" ]; then
    log_info "Syncing files from local directory: $LOCAL_APP_DIR to $INSTALL_DIR"
    # Sync keeping permissions but excluding the venv, .git, and config generated folders
    rsync -avq --exclude='venv/' --exclude='.git/' --exclude='config.yaml' "$LOCAL_APP_DIR/" "$INSTALL_DIR/"
    chown -R $SERVICE_USER:$SERVICE_GROUP "$INSTALL_DIR"
    log_success "New code synced successfully from local folder"
elif [ -d "$INSTALL_DIR/.git" ]; then
    log_info "Local application folder ($LOCAL_APP_DIR) not found."
    log_info "Attempting to pull latest changes from Git..."
    cd "$INSTALL_DIR"
    git reset --hard HEAD
    git pull
    chown -R $SERVICE_USER:$SERVICE_GROUP "$INSTALL_DIR"
    log_success "Source code updated from Git repository"
else
    log_error "Cannot find local source code ($LOCAL_APP_DIR) or Git repository in $INSTALL_DIR"
    log_error "Update aborted!"
    systemctl start "$SERVICE_NAME"
    exit 1
fi

# STEP 3: Update Dependencies
log_step 3 5 "Updating Python Dependencies..."
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
    if [ -f "$INSTALL_DIR/requirements/base.txt" ]; then
        pip install --quiet -r "$INSTALL_DIR/requirements/base.txt"
    fi
    if [ -f "$INSTALL_DIR/requirements/production.txt" ]; then
        pip install --quiet -r "$INSTALL_DIR/requirements/production.txt"
    fi
    deactivate
    log_success "Dependencies updated"
else
    log_warning "Virtual environment not found at $VENV_DIR. Skipping dependencies update."
fi

# STEP 4: Database Migrations
log_step 4 5 "Running Database Migrations..."
if [ -f "$INSTALL_DIR/alembic.ini" ]; then
    cd "$INSTALL_DIR"
    source "$VENV_DIR/bin/activate"
    alembic upgrade head || log_warning "Alembic migrations returned an error. Check logs if this is unexpected."
    deactivate
    log_success "Database schema is up to date"
else
    log_warning "Alembic config not found. Skipping auto-migrations."
fi

# STEP 5: Restart Service
log_step 5 5 "Restarting Service..."
systemctl daemon-reload
systemctl start "$SERVICE_NAME"

sleep 2
if systemctl is-active --quiet "$SERVICE_NAME"; then
    log_success "Service started successfully"
else
    log_error "Service failed to start. Please check the logs:"
    log_error "journalctl -u $SERVICE_NAME -f"
    exit 1
fi

echo ""
echo -e "${GREEN}✓ Update completed successfully at $(date)!${NC}"
echo -e "You can view the logs at: ${YELLOW}$UPDATE_LOG${NC}"
echo ""

exit 0
