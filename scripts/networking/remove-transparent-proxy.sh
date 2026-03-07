#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Remove Transparent Proxy Configuration
# ═══════════════════════════════════════════════════════════════════

set -e

echo "🗑️  Removing transparent proxy configuration..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Remove MITM chain from PREROUTING
iptables -t nat -D PREROUTING -j MITM_REDIRECT 2>/dev/null || true

# Remove MITM chain from OUTPUT
iptables -t nat -D OUTPUT -j MITM_REDIRECT 2>/dev/null || true

# Flush and delete MITM chain
iptables -t nat -F MITM_REDIRECT 2>/dev/null || true
iptables -t nat -X MITM_REDIRECT 2>/dev/null || true

# Remove NAT rules (be careful with this)
# iptables -t nat -F POSTROUTING

echo "✅ Transparent proxy configuration removed"
echo ""
echo "⚠️  Note: NAT/MASQUERADE rules were NOT removed to avoid breaking internet access"
echo "   If you want to remove all NAT rules: sudo iptables -t nat -F"
echo ""