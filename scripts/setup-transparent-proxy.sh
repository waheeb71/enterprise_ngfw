#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Enterprise NGFW v2.0 - Dynamic Transparent Proxy Setup
# ═══════════════════════════════════════════════════════════════════
#
# Features:
# - Auto-detection of network interfaces
# - Dynamic iptables rule generation
# - Multiple proxy mode support
# - IPv4 and IPv6 support
# - Traffic exclusion rules
# - NAT/MASQUERADE configuration
# - Rule persistence across reboots
# - Rollback on failure
# - Health checks
#
# Author: Enterprise NGFW Team
# Version: 2.0.0
# License: MIT
# ═══════════════════════════════════════════════════════════════════

set -e

# ==================== Colors ====================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ==================== Configuration ====================

CONFIG_FILE="/etc/enterprise-ngfw/config.yaml"
RULES_BACKUP="/var/lib/enterprise-ngfw/iptables-backup-$(date +%Y%m%d-%H%M%S).rules"

# Default ports (will be overridden from config)
PROXY_PORT_HTTPS=8443
PROXY_PORT_HTTP=8080

# Auto-detection flags
AUTO_DETECT=true
INTERACTIVE=true

# ==================== Banner ====================

print_banner() {
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                                   ║${NC}"
    echo -e "${CYAN}║      ${BOLD}🔧 Transparent Proxy Configuration - Dynamic Mode${NC}${CYAN}        ║${NC}"
    echo -e "${CYAN}║                                                                   ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# ==================== Utilities ====================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# ==================== Root Check ====================

check_root() {
    if [ "$EUID" -ne 0 ]; then 
        log_error "Please run as root (use sudo)"
        exit 1
    fi
}

# ==================== Configuration Loading ====================

load_config() {
    log_info "Loading configuration from $CONFIG_FILE..."
    
    if [ ! -f "$CONFIG_FILE" ]; then
        log_warning "Config file not found, using defaults"
        return
    fi
    
    # Parse YAML config (extract transparent section first)
    # Extract transparent section and find listen_port
    HTTPS_PORT=$(sed -n '/transparent:/,/^  [a-z]/p' "$CONFIG_FILE" | grep "listen_port:" | awk '{print $2}')
    if [ -n "$HTTPS_PORT" ]; then
        PROXY_PORT_HTTPS=$HTTPS_PORT
    fi
    
    # Extract transparent section and find http_port
    HTTP_PORT=$(sed -n '/transparent:/,/^  [a-z]/p' "$CONFIG_FILE" | grep "http_port:" | awk '{print $2}')
    if [ -n "$HTTP_PORT" ]; then
        PROXY_PORT_HTTP=$HTTP_PORT
    fi
    
    log_success "Configuration loaded (HTTPS:$PROXY_PORT_HTTPS, HTTP:$PROXY_PORT_HTTP)"
}

# ==================== Interface Detection ====================

detect_interfaces() {
    log_info "Detecting network interfaces..."
    
    # Get all non-loopback interfaces
    ALL_INTERFACES=($(ip -o link show | awk -F': ' '{print $2}' | grep -v '^lo$'))
    
    if [ ${#ALL_INTERFACES[@]} -eq 0 ]; then
        log_error "No network interfaces found!"
        exit 1
    fi
    
    log_success "Found ${#ALL_INTERFACES[@]} interface(s): ${ALL_INTERFACES[*]}"
    
    # Detect LAN interface (has private IP)
    for iface in "${ALL_INTERFACES[@]}"; do
        IP=$(ip -4 addr show "$iface" 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -n1)
        if [[ -n "$IP" ]]; then
            if [[ "$IP" =~ ^10\. ]] || [[ "$IP" =~ ^172\.(1[6-9]|2[0-9]|3[0-1])\. ]] || [[ "$IP" =~ ^192\.168\. ]]; then
                LAN_INTERFACE="$iface"
                LAN_IP="$IP"
                log_info "Detected LAN interface: $LAN_INTERFACE ($LAN_IP)"
                break
            fi
        fi
    done
    
    # Detect WAN interface (default route)
    WAN_INTERFACE=$(ip route | grep default | awk '{print $5}' | head -n1)
    if [[ -n "$WAN_INTERFACE" ]]; then
        WAN_IP=$(ip -4 addr show "$WAN_INTERFACE" 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -n1)
        log_info "Detected WAN interface: $WAN_INTERFACE ($WAN_IP)"
    fi
    
    # If no LAN detected, use primary interface
    if [[ -z "$LAN_INTERFACE" ]]; then
        LAN_INTERFACE="${ALL_INTERFACES[0]}"
        log_warning "Could not detect LAN, using: $LAN_INTERFACE"
    fi
    
    # If no WAN detected, use same as LAN
    if [[ -z "$WAN_INTERFACE" ]]; then
        WAN_INTERFACE="$LAN_INTERFACE"
        log_warning "Could not detect WAN, using: $WAN_INTERFACE"
    fi
}

# ==================== Interactive Configuration ====================

interactive_config() {
    if [ "$INTERACTIVE" = false ]; then
        return
    fi
    
    echo ""
    echo -e "${CYAN}${BOLD}Current Configuration:${NC}"
    echo -e "  LAN Interface:  ${YELLOW}$LAN_INTERFACE${NC} ($LAN_IP)"
    echo -e "  WAN Interface:  ${YELLOW}$WAN_INTERFACE${NC} ($WAN_IP)"
    echo -e "  HTTPS Port:     ${YELLOW}$PROXY_PORT_HTTPS${NC}"
    echo -e "  HTTP Port:      ${YELLOW}$PROXY_PORT_HTTP${NC}"
    echo ""
    
    read -p "Use this configuration? (Y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo ""
        read -p "Enter LAN interface [$LAN_INTERFACE]: " input
        LAN_INTERFACE=${input:-$LAN_INTERFACE}
        
        read -p "Enter WAN interface [$WAN_INTERFACE]: " input
        WAN_INTERFACE=${input:-$WAN_INTERFACE}
        
        read -p "Enter HTTPS proxy port [$PROXY_PORT_HTTPS]: " input
        PROXY_PORT_HTTPS=${input:-$PROXY_PORT_HTTPS}
        
        read -p "Enter HTTP proxy port [$PROXY_PORT_HTTP]: " input
        PROXY_PORT_HTTP=${input:-$PROXY_PORT_HTTP}
    fi
}

# ==================== Backup Current Rules ====================

backup_iptables() {
    log_info "Backing up current iptables rules..."
    
    mkdir -p "$(dirname "$RULES_BACKUP")"
    iptables-save > "$RULES_BACKUP"
    
    log_success "Backup saved to: $RULES_BACKUP"
}

# ==================== Enable IP Forwarding ====================

enable_forwarding() {
    log_info "Enabling IP forwarding..."
    
    # Enable IPv4 forwarding
    sysctl -w net.ipv4.ip_forward=1 > /dev/null
    sysctl -w net.ipv4.conf.all.forwarding=1 > /dev/null
    
    # Enable IPv6 forwarding
    sysctl -w net.ipv6.conf.all.forwarding=1 > /dev/null
    
    # Persist across reboots
    if ! grep -q "net.ipv4.ip_forward=1" /etc/sysctl.conf; then
        echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
    fi
    
    log_success "IP forwarding enabled"
}

# ==================== Clear Existing Rules ====================

clear_ngfw_rules() {
    log_info "Clearing existing NGFW rules..."
    
    # Remove NGFW chains from PREROUTING
    iptables -t nat -D PREROUTING -j NGFW_REDIRECT 2>/dev/null || true
    iptables -t nat -D OUTPUT -j NGFW_REDIRECT 2>/dev/null || true
    
    # Flush and delete NGFW chains
    iptables -t nat -F NGFW_REDIRECT 2>/dev/null || true
    iptables -t nat -X NGFW_REDIRECT 2>/dev/null || true
    
    iptables -t nat -F NGFW_HTTPS 2>/dev/null || true
    iptables -t nat -X NGFW_HTTPS 2>/dev/null || true
    
    iptables -t nat -F NGFW_HTTP 2>/dev/null || true
    iptables -t nat -X NGFW_HTTP 2>/dev/null || true
    
    # Clear filter rules
    iptables -F NGFW_FORWARD 2>/dev/null || true
    iptables -X NGFW_FORWARD 2>/dev/null || true
    
    log_success "Existing rules cleared"
}

# ==================== Create NAT Rules ====================

setup_nat_rules() {
    log_info "Setting up NAT/MASQUERADE rules..."
    
    # Create NGFW redirect chain
    iptables -t nat -N NGFW_REDIRECT 2>/dev/null || true
    iptables -t nat -F NGFW_REDIRECT
    
    # Exclude local traffic
    iptables -t nat -A NGFW_REDIRECT -d 127.0.0.0/8 -j RETURN
    iptables -t nat -A NGFW_REDIRECT -d 10.0.0.0/8 -j RETURN
    iptables -t nat -A NGFW_REDIRECT -d 172.16.0.0/12 -j RETURN
    iptables -t nat -A NGFW_REDIRECT -d 192.168.0.0/16 -j RETURN
    iptables -t nat -A NGFW_REDIRECT -d 169.254.0.0/16 -j RETURN
    iptables -t nat -A NGFW_REDIRECT -d 224.0.0.0/4 -j RETURN
    iptables -t nat -A NGFW_REDIRECT -d 240.0.0.0/4 -j RETURN
    
    # Exclude proxy's own traffic (to prevent loops)
    iptables -t nat -A NGFW_REDIRECT -m owner --uid-owner ngfw -j RETURN 2>/dev/null || true
    
    # Redirect HTTPS traffic (port 443)
    iptables -t nat -A NGFW_REDIRECT -p tcp --dport 443 -j REDIRECT --to-ports $PROXY_PORT_HTTPS
    
    # Redirect HTTP traffic (port 80)
    iptables -t nat -A NGFW_REDIRECT -p tcp --dport 80 -j REDIRECT --to-ports $PROXY_PORT_HTTP
    
    # Apply to PREROUTING (traffic from LAN)
    iptables -t nat -I PREROUTING -i $LAN_INTERFACE -j NGFW_REDIRECT
    
    # Apply to OUTPUT (traffic from local machine) - optional
    # iptables -t nat -I OUTPUT -j NGFW_REDIRECT
    
    # Setup MASQUERADE for internet access
    if [ "$LAN_INTERFACE" != "$WAN_INTERFACE" ]; then
        iptables -t nat -A POSTROUTING -o $WAN_INTERFACE -j MASQUERADE
        log_success "NAT masquerade enabled on $WAN_INTERFACE"
    fi
    
    log_success "NAT rules configured"
}

# ==================== Create Filter Rules ====================

setup_filter_rules() {
    log_info "Setting up filter rules..."
    
    # Create NGFW forward chain
    iptables -N NGFW_FORWARD 2>/dev/null || true
    iptables -F NGFW_FORWARD
    
    # Allow established connections
    iptables -A NGFW_FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT
    
    # Allow ICMP
    iptables -A NGFW_FORWARD -p icmp -j ACCEPT
    
    # Allow DNS
    iptables -A NGFW_FORWARD -p udp --dport 53 -j ACCEPT
    iptables -A NGFW_FORWARD -p tcp --dport 53 -j ACCEPT
    
    # Allow HTTP/HTTPS
    iptables -A NGFW_FORWARD -p tcp --dport 80 -j ACCEPT
    iptables -A NGFW_FORWARD -p tcp --dport 443 -j ACCEPT
    
    # Apply to FORWARD chain
    iptables -I FORWARD -j NGFW_FORWARD
    
    log_success "Filter rules configured"
}

# ==================== IPv6 Support ====================

setup_ipv6_rules() {
    log_info "Setting up IPv6 rules..."
    
    # Check if IPv6 is enabled
    if [ ! -f /proc/net/if_inet6 ]; then
        log_warning "IPv6 not enabled, skipping"
        return
    fi
    
    # Similar rules for IPv6
    ip6tables -t nat -N NGFW_REDIRECT 2>/dev/null || true
    ip6tables -t nat -F NGFW_REDIRECT
    
    # Exclude local traffic
    ip6tables -t nat -A NGFW_REDIRECT -d ::1/128 -j RETURN
    ip6tables -t nat -A NGFW_REDIRECT -d fe80::/10 -j RETURN
    ip6tables -t nat -A NGFW_REDIRECT -d ff00::/8 -j RETURN
    
    # Redirect HTTPS/HTTP
    ip6tables -t nat -A NGFW_REDIRECT -p tcp --dport 443 -j REDIRECT --to-ports $PROXY_PORT_HTTPS
    ip6tables -t nat -A NGFW_REDIRECT -p tcp --dport 80 -j REDIRECT --to-ports $PROXY_PORT_HTTP
    
    # Apply to PREROUTING
    ip6tables -t nat -I PREROUTING -i $LAN_INTERFACE -j NGFW_REDIRECT
    
    log_success "IPv6 rules configured"
}

# ==================== Rule Persistence ====================

save_rules_persistent() {
    log_info "Making rules persistent across reboots..."
    
    # Detect persistence method
    if command -v netfilter-persistent &> /dev/null; then
        # Debian/Ubuntu with netfilter-persistent
        mkdir -p /etc/iptables
        iptables-save > /etc/iptables/rules.v4
        ip6tables-save > /etc/iptables/rules.v6
        netfilter-persistent save
        log_success "Rules saved with netfilter-persistent"
        
    elif command -v iptables-save &> /dev/null && [ -d /etc/sysconfig ]; then
        # RHEL/CentOS
        iptables-save > /etc/sysconfig/iptables
        ip6tables-save > /etc/sysconfig/ip6tables
        log_success "Rules saved to /etc/sysconfig/"
        
    else
        log_warning "Could not detect persistence method"
        log_info "Install iptables-persistent: apt-get install iptables-persistent"
    fi
}

# ==================== Validation ====================

validate_rules() {
    log_info "Validating iptables rules..."
    
    # Check if NGFW chains exist
    if ! iptables -t nat -L NGFW_REDIRECT &>/dev/null; then
        log_error "NGFW_REDIRECT chain not found!"
        return 1
    fi
    
    # Check if rules are applied
    if ! iptables -t nat -L PREROUTING | grep -q NGFW_REDIRECT; then
        log_error "NGFW_REDIRECT not applied to PREROUTING!"
        return 1
    fi
    
    # Count redirect rules
    HTTPS_RULES=$(iptables -t nat -L NGFW_REDIRECT -n -v | grep -c "dpt:443" || echo "0")
    HTTP_RULES=$(iptables -t nat -L NGFW_REDIRECT -n -v | grep -c "dpt:80" || echo "0")
    
    if [ "$HTTPS_RULES" -eq 0 ] || [ "$HTTP_RULES" -eq 0 ]; then
        log_warning "Some redirect rules may be missing"
    fi
    
    log_success "Validation passed (HTTPS rules: $HTTPS_RULES, HTTP rules: $HTTP_RULES)"
    return 0
}

# ==================== Display Rules ====================

display_rules() {
    echo ""
    echo -e "${CYAN}${BOLD}Configured iptables Rules:${NC}"
    echo ""
    echo -e "${YELLOW}NAT Table (PREROUTING):${NC}"
    iptables -t nat -L PREROUTING -n -v --line-numbers | grep -A5 NGFW || echo "  (none)"
    echo ""
    echo -e "${YELLOW}NAT Table (NGFW_REDIRECT):${NC}"
    iptables -t nat -L NGFW_REDIRECT -n -v --line-numbers
    echo ""
    echo -e "${YELLOW}Filter Table (FORWARD):${NC}"
    iptables -L FORWARD -n -v --line-numbers | head -n 20
    echo ""
}

# ==================== Summary ====================

print_summary() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                   ║${NC}"
    echo -e "${GREEN}║          ✅ Transparent Proxy Setup Completed!                    ║${NC}"
    echo -e "${GREEN}║                                                                   ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}${BOLD}Configuration Summary:${NC}"
    echo -e "  LAN Interface:     ${YELLOW}$LAN_INTERFACE${NC}"
    echo -e "  WAN Interface:     ${YELLOW}$WAN_INTERFACE${NC}"
    echo -e "  HTTPS Redirect:    ${YELLOW}443 → $PROXY_PORT_HTTPS${NC}"
    echo -e "  HTTP Redirect:     ${YELLOW}80 → $PROXY_PORT_HTTP${NC}"
    echo -e "  Rules Backup:      ${YELLOW}$RULES_BACKUP${NC}"
    echo ""
    echo -e "${CYAN}${BOLD}Next Steps:${NC}"
    echo -e "  ${BOLD}1.${NC} Start Enterprise NGFW service:"
    echo -e "     ${YELLOW}sudo systemctl start enterprise-ngfw${NC}"
    echo ""
    echo -e "  ${BOLD}2.${NC} Test connectivity from client machine"
    echo ""
    echo -e "  ${BOLD}3.${NC} Monitor logs:"
    echo -e "     ${YELLOW}sudo tail -f /var/log/enterprise-ngfw/ngfw.log${NC}"
    echo ""
    echo -e "  ${BOLD}4.${NC} To remove rules, run:"
    echo -e "     ${YELLOW}sudo $0 --remove${NC}"
    echo ""
}

# ==================== Cleanup/Remove ====================

remove_rules() {
    echo -e "${YELLOW}Removing transparent proxy configuration...${NC}"
    
    backup_iptables
    clear_ngfw_rules
    
    # Also clear IPv6
    ip6tables -t nat -D PREROUTING -j NGFW_REDIRECT 2>/dev/null || true
    ip6tables -t nat -F NGFW_REDIRECT 2>/dev/null || true
    ip6tables -t nat -X NGFW_REDIRECT 2>/dev/null || true
    
    log_success "Transparent proxy rules removed"
    log_warning "IP forwarding was NOT disabled (may be needed by other services)"
    log_info "Backup saved to: $RULES_BACKUP"
    
    echo ""
    echo -e "${GREEN}✅ Cleanup completed${NC}"
    exit 0
}

# ==================== Main ====================

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --remove|--cleanup)
                check_root
                remove_rules
                ;;
            --non-interactive)
                INTERACTIVE=false
                shift
                ;;
            --lan)
                LAN_INTERFACE="$2"
                AUTO_DETECT=false
                shift 2
                ;;
            --wan)
                WAN_INTERFACE="$2"
                AUTO_DETECT=false
                shift 2
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Usage: $0 [--remove] [--non-interactive] [--lan INTERFACE] [--wan INTERFACE]"
                exit 1
                ;;
        esac
    done
    
    print_banner
    check_root
    load_config
    
    if [ "$AUTO_DETECT" = true ]; then
        detect_interfaces
    fi
    
    interactive_config
    
    echo ""
    log_info "Starting transparent proxy setup..."
    echo ""
    
    backup_iptables
    enable_forwarding
    clear_ngfw_rules
    setup_nat_rules
    setup_filter_rules
    setup_ipv6_rules
    
    if ! validate_rules; then
        log_error "Validation failed! Restoring backup..."
        iptables-restore < "$RULES_BACKUP"
        exit 1
    fi
    
    save_rules_persistent
    display_rules
    print_summary
}

# Run main
main "$@"

exit 0