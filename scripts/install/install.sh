#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Enterprise NGFW v2.0 - Automated Installation Script
# ═══════════════════════════════════════════════════════════════════
#
# Features:
# - Multi-OS support (Ubuntu 20.04+, Debian 11+, CentOS 8+, RHEL 8+)
# - Automatic dependency detection and installation
# - eBPF/XDP kernel support verification
# - Python 3.9+ with virtual environment
# - System optimization for high-performance networking
# - Systemd service creation
# - Dynamic configuration generation
# - Health checks and validation
# - Rollback support on failure
#
# Author: Enterprise NGFW Team
# Version: 2.0.0
# License: MIT
# ═══════════════════════════════════════════════════════════════════

set -e

# ==================== Colors and Formatting ====================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ==================== Configuration ====================
LOCAL_APP_DIR="~/enterprise_ngfw" 
INSTALL_DIR="/opt/enterprise-ngfw"
CONFIG_DIR="/etc/enterprise-ngfw"
DATA_DIR="/var/lib/enterprise-ngfw"
LOG_DIR="/var/log/enterprise-ngfw"
VENV_DIR="$INSTALL_DIR/venv"
SERVICE_NAME="enterprise-ngfw"
SERVICE_USER="ngfw"
SERVICE_GROUP="ngfw"

PYTHON_MIN_VERSION="3.9"
KERNEL_MIN_VERSION="5.3"  # For eBPF/XDP support

# GitHub repository (adjust if needed)
REPO_URL="https://github.com/waheeb71/enterprise-ngfw"
ARCHIVE_URL="$REPO_URL/archive/refs/tags/v2.0.0.tar.gz"

# ==================== Banner ====================

print_banner() {
    clear
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                                   ║${NC}"
    echo -e "${CYAN}║      ${BOLD}🛡️  Enterprise Next-Generation Firewall v2.0${NC}${CYAN}             ║${NC}"
    echo -e "${CYAN}║                                                                   ║${NC}"
    echo -e "${CYAN}║      ${GREEN}✓${NC} Multi-Proxy Modes    ${GREEN}✓${NC} eBPF XDP Acceleration        ${CYAN}║${NC}"
    echo -e "${CYAN}║      ${GREEN}✓${NC} SSL Inspection       ${GREEN}✓${NC} Smart Blocker               ${CYAN}║${NC}"
    echo -e "${CYAN}║      ${GREEN}✓${NC} Deep Packet Inspect. ${GREEN}✓${NC} Threat Intelligence         ${CYAN}║${NC}"
    echo -e "${CYAN}║                                                                   ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# ==================== Logging ====================

INSTALL_LOG="$HOME/ngfw-install-$(date +%Y%m%d-%H%M%S).log"

log() {
    echo -e "$1" | tee -a "$INSTALL_LOG"
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_success() {
    log "${GREEN}[✓]${NC} $1"
}

log_warning() {
    log "${YELLOW}[!]${NC} $1"
}

log_error() {
    log "${RED}[✗]${NC} $1"
}

log_step() {
    log "\n${CYAN}${BOLD}[STEP $1/$2]${NC} $3"
}

# ==================== System Checks ====================

check_root() {
    if [ "$EUID" -ne 0 ]; then 
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
    log_success "Running as root"
}

detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
        OS_PRETTY=$PRETTY_NAME
    else
        log_error "Cannot detect OS (missing /etc/os-release)"
        exit 1
    fi
    
    log_success "Detected OS: $OS_PRETTY"
    
    # Validate supported OS
       case "$OS" in
        ubuntu|debian|kali)
             apt-get install -y python3 python3-pip build-essential libssl-dev libffi-dev libpcap-dev
            ;;
        centos|rhel|rocky|almalinux)
            yum install -y python3 python3-pip gcc gcc-c++ libffi-devel openssl-devel libpcap-devel
            ;;
        *)
            log_warning "OS '$OS' is not officially tested"
            read -p "Continue anyway? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
            ;;
    esac
}

check_kernel_version() {
    KERNEL_VERSION=$(uname -r | cut -d'-' -f1)
    log_info "Kernel version: $KERNEL_VERSION"
    
    if [ "$(printf '%s\n' "$KERNEL_MIN_VERSION" "$KERNEL_VERSION" | sort -V | head -n1)" != "$KERNEL_MIN_VERSION" ]; then
        log_error "Kernel version $KERNEL_VERSION is too old (need >= $KERNEL_MIN_VERSION for eBPF)"
        log_warning "eBPF/XDP features will be DISABLED"
        EBPF_SUPPORTED=false
    else
        log_success "Kernel supports eBPF/XDP"
        EBPF_SUPPORTED=true
    fi
}

check_python_version() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 not found"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    log_info "Python version: $PYTHON_VERSION"
    
    if [ "$(printf '%s\n' "$PYTHON_MIN_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$PYTHON_MIN_VERSION" ]; then
        log_error "Python version $PYTHON_VERSION is too old (need >= $PYTHON_MIN_VERSION)"
        exit 1
    fi
    
    log_success "Python version is compatible"
}

check_network_interfaces() {
    log_info "Detecting network interfaces..."
    
    # Get all non-loopback interfaces
    INTERFACES=($(ip -o link show | awk -F': ' '{print $2}' | grep -v '^lo$'))
    
    if [ ${#INTERFACES[@]} -eq 0 ]; then
        log_error "No network interfaces found"
        exit 1
    fi
    
    log_success "Found ${#INTERFACES[@]} network interface(s): ${INTERFACES[*]}"
    
    # Auto-select primary interface
    PRIMARY_INTERFACE=$(ip route | grep default | awk '{print $5}' | head -n1)
    if [ -z "$PRIMARY_INTERFACE" ]; then
        PRIMARY_INTERFACE=${INTERFACES[0]}
    fi
    
    log_info "Primary interface: $PRIMARY_INTERFACE"
}
copy_local_application() {
    log_info "Copying Enterprise NGFW files from local directory..."
    
    if [ ! -d "$LOCAL_APP_DIR" ]; then
        log_error "Local application directory $LOCAL_APP_DIR does not exist"
        exit 1
    fi
    
    mkdir -p "$INSTALL_DIR"
    
    cp -r "$LOCAL_APP_DIR/"* "$INSTALL_DIR/"
    chown -R $SERVICE_USER:$SERVICE_GROUP "$INSTALL_DIR"
    
    log_success "Application files copied to $INSTALL_DIR"
}

# ==================== Dependency Installation ====================

install_dependencies_debian() {
    log_info "Installing dependencies for Debian/Ubuntu..."
    
    export DEBIAN_FRONTEND=noninteractive
    
    
    apt-get update || true 
    
    # Core dependencies - إضافة --fix-missing
    apt-get install -y --fix-missing \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        git \
        curl \
        wget \
        net-tools \
        iptables \
        ipset \
        iproute2 \
        tcpdump
    
    # eBPF/XDP dependencies
    if [ "$EBPF_SUPPORTED" = true ]; then
        apt-get install -y -qq \
            clang \
            llvm \
            libbpf-dev \
            linux-headers-$(uname -r) \
            bpfcc-tools \
            python3-bpfcc
    fi
    
    # SSL/Crypto dependencies
    apt-get install -y -qq \
        libssl-dev \
        libffi-dev \
        ca-certificates
    
    # GeoIP dependencies
    apt-get install -y -qq \
        libmaxminddb0 \
        libmaxminddb-dev \
        mmdb-bin
    
    # Optional: PCAP for packet capture
    apt-get install -y -qq \
        libpcap-dev \
        python3-pcapy
    
    log_success "Dependencies installed successfully"
}

install_dependencies_rhel() {
    log_info "Installing dependencies for RHEL/CentOS..."
    
    # Enable EPEL repository
    if ! yum repolist | grep -q epel; then
        yum install -y epel-release
    fi
    
    # Core dependencies
    yum install -y \
        python3 \
        python3-pip \
        python3-devel \
        gcc \
        gcc-c++ \
        make \
        git \
        curl \
        wget \
        net-tools \
        iptables \
        ipset \
        iproute \
        tcpdump
    
    # eBPF/XDP dependencies
    if [ "$EBPF_SUPPORTED" = true ]; then
        yum install -y \
            clang \
            llvm \
            libbpf-devel \
            kernel-devel-$(uname -r) \
            bcc-tools \
            python3-bcc
    fi
    
    # SSL dependencies
    yum install -y \
        openssl-devel \
        libffi-devel \
        ca-certificates
    
    # GeoIP
    yum install -y \
        libmaxminddb \
        libmaxminddb-devel
    
    log_success "Dependencies installed successfully"
}

install_system_dependencies() {
    case "$OS" in
        ubuntu|debian|kali)
            install_dependencies_debian
            ;;
        centos|rhel|rocky|almalinux)
            install_dependencies_rhel
            ;;
        *)
            log_error "Unsupported OS for automatic dependency installation"
            exit 1
            ;;
    esac
}

# ==================== Application Installation ====================

create_user_and_directories() {
    log_info "Creating system user and directories..."
    
    # Create user
    if ! id -u $SERVICE_USER &>/dev/null; then
        useradd --system --no-create-home --shell /bin/false $SERVICE_USER
        log_success "Created user: $SERVICE_USER"
    else
        log_info "User $SERVICE_USER already exists"
    fi
    
    # Create directories
    mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$DATA_DIR" "$LOG_DIR"
    mkdir -p "$CONFIG_DIR/certs" "$CONFIG_DIR/defaults" "$CONFIG_DIR/policies"
    mkdir -p "$DATA_DIR/geoip" "$DATA_DIR/reputation" "$DATA_DIR/logs"
    
    # Set permissions
    chown -R $SERVICE_USER:$SERVICE_GROUP "$INSTALL_DIR" "$CONFIG_DIR" "$DATA_DIR" "$LOG_DIR"
    chmod 750 "$CONFIG_DIR" "$DATA_DIR" "$LOG_DIR"
    chmod 700 "$CONFIG_DIR/certs"
    
    log_success "Directories created and secured"
}

download_application() {
    log_info "Downloading Enterprise NGFW v2.0..."
    
    cd /tmp
    
    # If archive URL is available, download it
    if [ -n "$ARCHIVE_URL" ]; then
        wget -q --show-progress "$ARCHIVE_URL" -O ngfw-v2.0.tar.gz
        tar -xzf ngfw-v2.0.tar.gz -C "$INSTALL_DIR" --strip-components=1
        rm -f ngfw-v2.0.tar.gz
    else
        # Clone from git (development mode)
        if [ -d "$INSTALL_DIR/.git" ]; then
            log_info "Git repository already exists, pulling latest..."
            cd "$INSTALL_DIR"
            git pull
        else
            git clone "$REPO_URL" "$INSTALL_DIR"
        fi
    fi
    
    log_success "Application downloaded"
}

setup_python_environment() {
    log_info "Setting up Python virtual environment..."
    
    cd "$INSTALL_DIR"
    
    # Create virtual environment
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --quiet --upgrade pip setuptools wheel
    
    # Install Python dependencies
    if [ -f "requirements/base.txt" ]; then
        pip install --quiet -r requirements/base.txt
    fi
    
    if [ -f "requirements/production.txt" ]; then
        pip install --quiet -r requirements/production.txt
    fi
    
    # Install optional eBPF dependencies
    if [ "$EBPF_SUPPORTED" = true ]; then
        pip install --quiet bcc pyroute2 || log_warning "Failed to install eBPF Python packages"
    fi
    
    deactivate
    
    log_success "Python environment configured"
}

generate_configuration() {
    log_info "Deploying configuration from repository..."
    
    # Copy default config
    if [ -f "$INSTALL_DIR/config/defaults/base.yaml" ]; then
        cp "$INSTALL_DIR/config/defaults/base.yaml" "$CONFIG_DIR/config.yaml"
        log_success "Created configuration from base.yaml"
    else
        log_error "Base configuration file not found at $INSTALL_DIR/config/defaults/base.yaml!"
        exit 1
    fi
    
    # Apply dynamic environment-specific settings via sed
    # Update network interface
    if grep -q "primary_interface:" "$CONFIG_DIR/config.yaml"; then
        sed -i "s/primary_interface: .*/primary_interface: \"$PRIMARY_INTERFACE\"/g" "$CONFIG_DIR/config.yaml"
    fi
    
    # Update management IP
    MGMT_IP=$(ip -4 addr show $PRIMARY_INTERFACE | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
    if [ -n "$MGMT_IP" ] && grep -q "management_ip:" "$CONFIG_DIR/config.yaml"; then
        sed -i "s/management_ip: .*/management_ip: \"$MGMT_IP\"/g" "$CONFIG_DIR/config.yaml"
    fi
    
    # Set permissions
    chmod 640 "$CONFIG_DIR/config.yaml"
    chown $SERVICE_USER:$SERVICE_GROUP "$CONFIG_DIR/config.yaml"
    
    log_success "Configuration deployed successfully: $CONFIG_DIR/config.yaml"
}

generate_ca_certificates() {
    log_info "Generating CA certificates for SSL inspection..."
    
    cd "$CONFIG_DIR/certs"
    
    # Generate Root CA private key
    openssl genrsa -out ca.key 4096
    
    # Generate Root CA certificate
    openssl req -new -x509 -days 3650 -key ca.key -out ca.crt \
        -subj "/C=US/ST=State/L=City/O=Enterprise NGFW/OU=Security/CN=Enterprise NGFW Root CA"
    
    # Set permissions
    chmod 600 ca.key
    chmod 644 ca.crt
    chown $SERVICE_USER:$SERVICE_GROUP ca.key ca.crt
    
    log_success "CA certificates generated"
    log_warning "Install CA certificate on clients: $CONFIG_DIR/certs/ca.crt"
}

# ==================== Systemd Service ====================

create_systemd_service() {
    log_info "Creating systemd service from repository..."
    
    if [ -f "$INSTALL_DIR/systemd/ngfw.service" ]; then
        cp "$INSTALL_DIR/systemd/ngfw.service" "/etc/systemd/system/${SERVICE_NAME}.service"
        
        # Apply dynamic paths via sed
        sed -i "s|WorkingDirectory=.*|WorkingDirectory=$INSTALL_DIR|g" "/etc/systemd/system/${SERVICE_NAME}.service"
        sed -i "s|User=.*|User=$SERVICE_USER|g" "/etc/systemd/system/${SERVICE_NAME}.service"
        sed -i "s|Group=.*|Group=$SERVICE_GROUP|g" "/etc/systemd/system/${SERVICE_NAME}.service"
        sed -i "s|ExecStart=/usr/bin/python3 main.py.*|ExecStart=$VENV_DIR/bin/python main.py -c $CONFIG_DIR/config.yaml|g" "/etc/systemd/system/${SERVICE_NAME}.service"
        sed -i "s|ReadWritePaths=.*|ReadWritePaths=$DATA_DIR $LOG_DIR $CONFIG_DIR/certs|g" "/etc/systemd/system/${SERVICE_NAME}.service"
        sed -i "s|Environment=\"NGFW_CONFIG=.*|Environment=\"PATH=$VENV_DIR/bin:\$PATH\"|g" "/etc/systemd/system/${SERVICE_NAME}.service"
        sed -i "s|SyslogIdentifier=.*|SyslogIdentifier=$SERVICE_NAME|g" "/etc/systemd/system/${SERVICE_NAME}.service"
        
        systemctl daemon-reload
        log_success "Systemd service deployed and reloaded"
    else
        log_error "Service file template not found at $INSTALL_DIR/systemd/ngfw.service!"
        exit 1
    fi
}

# ==================== System Optimization ====================

optimize_system() {
    log_info "Optimizing system for high-performance networking..."
    
    if [ -f "$INSTALL_DIR/config/sysctl-optimization.conf" ]; then
        cp "$INSTALL_DIR/config/sysctl-optimization.conf" "/etc/sysctl.d/99-ngfw-optimization.conf"
        sysctl -p /etc/sysctl.d/99-ngfw-optimization.conf > /dev/null 2>&1
        log_success "System optimized"
    else
        log_warning "sysctl-optimization.conf not found. Skipping optimizations."
    fi
}

# ==================== Health Checks ====================

verify_installation() {
    log_info "Verifying installation..."
    
    # Check files exist
    [ -f "$INSTALL_DIR/main.py" ] || { log_error "main.py not found"; return 1; }
    [ -f "$CONFIG_DIR/config.yaml" ] || { log_error "config.yaml not found"; return 1; }
    [ -f "$CONFIG_DIR/certs/ca.crt" ] || { log_error "CA certificate not found"; return 1; }
    
    # Check Python environment
    if [ ! -f "$VENV_DIR/bin/python" ]; then
        log_error "Virtual environment not found"
        return 1
    fi
    
    # Test import
    cd "$INSTALL_DIR"
    if ! $VENV_DIR/bin/python -c "import core.router" 2>/dev/null; then
        log_error "Python imports failed"
        return 1
    fi
    
    log_success "Installation verified"
    return 0
}

# ==================== Post-Installation ====================

print_summary() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                   ║${NC}"
    echo -e "${GREEN}║               ✅ Installation Completed Successfully!             ║${NC}"
    echo -e "${GREEN}║                                                                   ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}${BOLD}Installation Details:${NC}"
    echo -e "  Install Directory:  ${YELLOW}$INSTALL_DIR${NC}"
    echo -e "  Config Directory:   ${YELLOW}$CONFIG_DIR${NC}"
    echo -e "  Data Directory:     ${YELLOW}$DATA_DIR${NC}"
    echo -e "  Log Directory:      ${YELLOW}$LOG_DIR${NC}"
    echo -e "  CA Certificate:     ${YELLOW}$CONFIG_DIR/certs/ca.crt${NC}"
    echo ""
    echo -e "${CYAN}${BOLD}Service Management:${NC}"
    echo -e "  ${GREEN}Start:${NC}   sudo systemctl start $SERVICE_NAME"
    echo -e "  ${YELLOW}Stop:${NC}    sudo systemctl stop $SERVICE_NAME"
    echo -e "  ${BLUE}Status:${NC}  sudo systemctl status $SERVICE_NAME"
    echo -e "  ${CYAN}Logs:${NC}    sudo journalctl -u $SERVICE_NAME -f"
    echo ""
    echo -e "${CYAN}${BOLD}Next Steps:${NC}"
    echo -e "  ${BOLD}1.${NC} Export CA certificate for clients:"
    echo -e "     ${YELLOW}sudo $INSTALL_DIR/deployment/export-ca.sh${NC}"
    echo ""
    echo -e "  ${BOLD}2.${NC} Configure transparent proxy (if needed):"
    echo -e "     ${YELLOW}sudo $INSTALL_DIR/deployment/setup-transparent-proxy.sh${NC}"
    echo ""
    echo -e "  ${BOLD}3.${NC} Start the service:"
    echo -e "     ${YELLOW}sudo systemctl start $SERVICE_NAME${NC}"
    echo -e "     ${YELLOW}sudo systemctl enable $SERVICE_NAME${NC}"
    echo ""
    echo -e "  ${BOLD}4.${NC} View logs:"
    echo -e "     ${YELLOW}sudo tail -f $LOG_DIR/ngfw.log${NC}"
    echo ""
    echo -e "${GREEN}Installation log saved to: ${YELLOW}$INSTALL_LOG${NC}"
    echo ""
}

# ==================== Main Installation Flow ====================

main() {
    print_banner
    
    log_info "Starting installation at $(date)"
    log_info "Installation log: $INSTALL_LOG"
    
    # Step 1: System Checks
    log_step 1 8 "System Checks"
    check_root
    detect_os
    check_kernel_version
    check_python_version
    check_network_interfaces
    
    # Step 2: Install Dependencies
    log_step 2 8 "Installing System Dependencies"
    install_system_dependencies
    
    # Step 3: Create User and Directories
    log_step 3 8 "Creating User and Directories"
    create_user_and_directories
    
    # Step 4: Download Application
    log_step 4 8 "Downloading Application"
    # download_application  # Uncomment when repository is ready
    log_warning "Skipping download (using local files)"
    # Option 2: Copy from local files
    copy_local_application

    # Step 5: Setup Python Environment
    log_step 5 8 "Setting Up Python Environment"
    setup_python_environment
    
    # Step 6: Generate Configuration
    log_step 6 8 "Generating Configuration"
    generate_configuration
    generate_ca_certificates
    
    # Step 7: Create Systemd Service
    log_step 7 8 "Creating Systemd Service"
    create_systemd_service
    
    # Step 8: System Optimization
    log_step 8 8 "Optimizing System"
    optimize_system
    
    # Verify Installation
    if ! verify_installation; then
        log_error "Installation verification failed!"
        exit 1
    fi
    
    # Print Summary
    print_summary
    
    log_success "Installation completed at $(date)"
}

# ==================== Error Handling ====================

trap 'log_error "Installation failed at line $LINENO"; exit 1' ERR

# Run main installation
main

exit 0