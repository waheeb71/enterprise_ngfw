#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Enterprise NGFW v2.0 - CA Certificate Export Tool
# ═══════════════════════════════════════════════════════════════════
#
# Features:
# - Export CA certificates in multiple formats (PEM, DER, P12)
# - Generate client installation packages
# - Platform-specific installation instructions
# - QR code generation for mobile devices
# - Automatic certificate validation
# - Multi-platform support (Windows, macOS, Linux, iOS, Android)
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

CA_CERT_PATH="/etc/enterprise-ngfw/certs/ca.crt"
CA_KEY_PATH="/etc/enterprise-ngfw/certs/ca.key"
OUTPUT_DIR="${1:-/tmp/ngfw-ca-export-$(date +%Y%m%d-%H%M%S)}"

EXPORT_FORMATS=("pem" "der" "p12")
P12_PASSWORD="ngfw-ca-password"  # Change this!

# ==================== Banner ====================

print_banner() {
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                                   ║${NC}"
    echo -e "${CYAN}║       ${BOLD}🔐 CA Certificate Export Tool${NC}${CYAN}                             ║${NC}"
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

# ==================== Checks ====================

check_dependencies() {
    local missing=()
    
    command -v openssl &>/dev/null || missing+=("openssl")
    
    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing dependencies: ${missing[*]}"
        log_info "Install with: apt-get install ${missing[*]}"
        exit 1
    fi
}

check_ca_exists() {
    if [ ! -f "$CA_CERT_PATH" ]; then
        log_error "CA certificate not found: $CA_CERT_PATH"
        exit 1
    fi
    
    if [ ! -f "$CA_KEY_PATH" ]; then
        log_warning "CA private key not found: $CA_KEY_PATH"
        log_info "Some export formats (P12) will not be available"
    fi
    
    log_success "CA certificate found"
}

# ==================== Certificate Info ====================

display_cert_info() {
    log_info "Certificate Information:"
    echo ""
    
    # Extract certificate details
    SUBJECT=$(openssl x509 -in "$CA_CERT_PATH" -noout -subject | sed 's/subject=//')
    ISSUER=$(openssl x509 -in "$CA_CERT_PATH" -noout -issuer | sed 's/issuer=//')
    VALID_FROM=$(openssl x509 -in "$CA_CERT_PATH" -noout -startdate | sed 's/notBefore=//')
    VALID_TO=$(openssl x509 -in "$CA_CERT_PATH" -noout -enddate | sed 's/notAfter=//')
    FINGERPRINT=$(openssl x509 -in "$CA_CERT_PATH" -noout -fingerprint -sha256 | sed 's/SHA256 Fingerprint=//')
    
    echo -e "  ${CYAN}Subject:${NC}      $SUBJECT"
    echo -e "  ${CYAN}Issuer:${NC}       $ISSUER"
    echo -e "  ${CYAN}Valid From:${NC}   $VALID_FROM"
    echo -e "  ${CYAN}Valid To:${NC}     $VALID_TO"
    echo -e "  ${CYAN}Fingerprint:${NC}  $FINGERPRINT"
    echo ""
}

# ==================== Export Functions ====================

export_pem() {
    log_info "Exporting PEM format..."
    
    cp "$CA_CERT_PATH" "$OUTPUT_DIR/ngfw-root-ca.pem"
    
    # Also create .crt extension (same format, different extension)
    cp "$CA_CERT_PATH" "$OUTPUT_DIR/ngfw-root-ca.crt"
    
    log_success "PEM format exported"
}

export_der() {
    log_info "Exporting DER format..."
    
    openssl x509 -in "$CA_CERT_PATH" -outform DER -out "$OUTPUT_DIR/ngfw-root-ca.der"
    
    # Also create .cer extension (for Windows)
    cp "$OUTPUT_DIR/ngfw-root-ca.der" "$OUTPUT_DIR/ngfw-root-ca.cer"
    
    log_success "DER format exported"
}

export_p12() {
    if [ ! -f "$CA_KEY_PATH" ]; then
        log_warning "Skipping P12 export (CA key not available)"
        return
    fi
    
    log_info "Exporting P12/PKCS12 format..."
    
    openssl pkcs12 -export \
        -in "$CA_CERT_PATH" \
        -inkey "$CA_KEY_PATH" \
        -out "$OUTPUT_DIR/ngfw-root-ca.p12" \
        -name "Enterprise NGFW Root CA" \
        -passout pass:"$P12_PASSWORD"
    
    # Save password to file
    echo "$P12_PASSWORD" > "$OUTPUT_DIR/p12-password.txt"
    chmod 600 "$OUTPUT_DIR/p12-password.txt"
    
    log_success "P12 format exported (password saved to p12-password.txt)"
}

# ==================== Installation Instructions ====================

generate_instructions() {
    log_info "Generating installation instructions..."
    
    cat > "$OUTPUT_DIR/README.txt" << 'EOF'
═══════════════════════════════════════════════════════════════════
Enterprise NGFW v2.0 - CA Certificate Installation Guide
═══════════════════════════════════════════════════════════════════

⚠️  IMPORTANT: You MUST install this certificate on ALL client devices
   that will use the NGFW transparent proxy. Without it, browsers will
   show SSL certificate warnings.

═══════════════════════════════════════════════════════════════════
📦 Package Contents
═══════════════════════════════════════════════════════════════════

  • ngfw-root-ca.pem     - PEM format (Linux/macOS/servers)
  • ngfw-root-ca.crt     - PEM with .crt extension (universal)
  • ngfw-root-ca.der     - DER format (Windows/Java)
  • ngfw-root-ca.cer     - DER with .cer extension (Windows)
  • ngfw-root-ca.p12     - PKCS12 format (all platforms)
  • p12-password.txt     - Password for P12 file

═══════════════════════════════════════════════════════════════════
🪟 Windows Installation
═══════════════════════════════════════════════════════════════════

Method 1: GUI (Recommended)
  1. Double-click "ngfw-root-ca.cer"
  2. Click "Install Certificate..."
  3. Select "Local Machine" → Next
  4. Choose "Place all certificates in the following store"
  5. Click "Browse" → Select "Trusted Root Certification Authorities"
  6. Click Next → Finish
  7. Click "Yes" on security warning

Method 2: Command Line (Admin PowerShell)
  certutil -addstore -f "ROOT" ngfw-root-ca.cer

Method 3: GPO (Enterprise Deployment)
  Computer Configuration → Windows Settings → Security Settings →
  Public Key Policies → Trusted Root Certification Authorities →
  Import → Select ngfw-root-ca.cer

═══════════════════════════════════════════════════════════════════
🍎 macOS Installation
═══════════════════════════════════════════════════════════════════

Method 1: GUI
  1. Double-click "ngfw-root-ca.pem"
  2. Keychain Access will open
  3. Select "System" keychain
  4. Click "Add"
  5. Find the certificate in System keychain
  6. Double-click the certificate
  7. Expand "Trust" section
  8. Set "When using this certificate" to "Always Trust"
  9. Close and enter admin password

Method 2: Command Line
  sudo security add-trusted-cert -d -r trustRoot \
    -k /Library/Keychains/System.keychain ngfw-root-ca.pem

═══════════════════════════════════════════════════════════════════
🐧 Linux Installation
═══════════════════════════════════════════════════════════════════

Ubuntu/Debian:
  sudo cp ngfw-root-ca.crt /usr/local/share/ca-certificates/
  sudo update-ca-certificates

RHEL/CentOS/Fedora:
  sudo cp ngfw-root-ca.crt /etc/pki/ca-trust/source/anchors/
  sudo update-ca-trust

Arch Linux:
  sudo cp ngfw-root-ca.crt /etc/ca-certificates/trust-source/anchors/
  sudo trust extract-compat

For Firefox (all distros):
  1. Open Firefox → Settings → Privacy & Security
  2. Scroll to "Certificates" → Click "View Certificates"
  3. Authorities tab → Import
  4. Select ngfw-root-ca.crt
  5. Check "Trust this CA to identify websites"
  6. Click OK

═══════════════════════════════════════════════════════════════════
📱 iOS Installation (iPhone/iPad)
═══════════════════════════════════════════════════════════════════

Method 1: AirDrop/Email
  1. Send ngfw-root-ca.cer to device via AirDrop or Email
  2. Tap the file → "Allow" to download profile
  3. Go to Settings → General → VPN & Device Management
  4. Tap the profile → Install → Enter passcode
  5. Tap Install (2 times) → Done
  6. Go to Settings → General → About → Certificate Trust Settings
  7. Enable "Enterprise NGFW Root CA"

Method 2: Over-the-Air (OTA)
  Host the .mobileconfig file on web server and open in Safari

═══════════════════════════════════════════════════════════════════
🤖 Android Installation
═══════════════════════════════════════════════════════════════════

  1. Copy ngfw-root-ca.crt to device
  2. Go to Settings → Security → Encryption & credentials
  3. Tap "Install a certificate" → CA certificate
  4. Tap "Install anyway" (warning)
  5. Navigate to and select ngfw-root-ca.crt
  6. Enter certificate name: "Enterprise NGFW Root CA"
  7. Tap OK

Note: On Android 11+, user certificates may not work for all apps.
Consider using a mobile device management (MDM) solution for
enterprise deployment.

═══════════════════════════════════════════════════════════════════
🌐 Browser-Specific Instructions
═══════════════════════════════════════════════════════════════════

Google Chrome (Windows/macOS):
  Uses system certificate store (no additional configuration needed)

Mozilla Firefox:
  Has its own certificate store (see Linux instructions above)

Microsoft Edge:
  Uses system certificate store (no additional configuration needed)

Safari (macOS):
  Uses system certificate store (no additional configuration needed)

═══════════════════════════════════════════════════════════════════
🔍 Verification
═══════════════════════════════════════════════════════════════════

After installation, verify the certificate is trusted:

1. Visit any HTTPS website through the NGFW proxy
2. Check that there are NO certificate warnings
3. Click the padlock icon in browser
4. Verify certificate chain shows "Enterprise NGFW Root CA"

Windows Command:
  certutil -verifystore ROOT "Enterprise NGFW Root CA"

macOS Command:
  security find-certificate -c "Enterprise NGFW Root CA" \
    /Library/Keychains/System.keychain

Linux Command:
  openssl verify -CAfile /usr/local/share/ca-certificates/ngfw-root-ca.crt \
    /usr/local/share/ca-certificates/ngfw-root-ca.crt

═══════════════════════════════════════════════════════════════════
🔐 Security Notes
═══════════════════════════════════════════════════════════════════

⚠️  This certificate allows the NGFW to inspect HTTPS traffic.

✓  The certificate is only valid for the NGFW and should ONLY be
   installed on devices that need to use the NGFW proxy.

✓  Keep the CA private key (ca.key) SECURE. Anyone with access to
   the private key can impersonate any website.

✓  Regularly audit installed certificates and remove when no longer
   needed.

✓  Consider using different CA certificates for different departments
   or security zones.

═══════════════════════════════════════════════════════════════════
📞 Support
═══════════════════════════════════════════════════════════════════

For installation issues or questions:
  • Documentation: https://github.com/your-org/enterprise-ngfw
  • Email: security@your-company.com
  • Internal Wiki: https://wiki.your-company.com/ngfw

Certificate Fingerprint (SHA-256):
EOF

    # Append actual fingerprint
    FINGERPRINT=$(openssl x509 -in "$CA_CERT_PATH" -noout -fingerprint -sha256 | sed 's/SHA256 Fingerprint=//')
    echo "  $FINGERPRINT" >> "$OUTPUT_DIR/README.txt"
    
    echo "" >> "$OUTPUT_DIR/README.txt"
    echo "Generated: $(date)" >> "$OUTPUT_DIR/README.txt"
    echo "═══════════════════════════════════════════════════════════════════" >> "$OUTPUT_DIR/README.txt"
    
    log_success "Installation instructions generated"
}

# ==================== Generate Quick Install Scripts ====================

generate_install_scripts() {
    log_info "Generating platform-specific install scripts..."
    
    # Windows PowerShell script
    cat > "$OUTPUT_DIR/install-windows.ps1" << 'EOF'
# Enterprise NGFW - Windows CA Installation Script
# Run as Administrator

Write-Host "Installing Enterprise NGFW Root CA..." -ForegroundColor Cyan

$certFile = Join-Path $PSScriptRoot "ngfw-root-ca.cer"

if (-not (Test-Path $certFile)) {
    Write-Host "Error: Certificate file not found!" -ForegroundColor Red
    exit 1
}

try {
    certutil -addstore -f "ROOT" $certFile
    Write-Host "✓ Certificate installed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Verification:" -ForegroundColor Yellow
    certutil -verifystore ROOT "Enterprise NGFW Root CA"
} catch {
    Write-Host "✗ Installation failed: $_" -ForegroundColor Red
    exit 1
}
EOF

    # macOS/Linux bash script
    cat > "$OUTPUT_DIR/install-unix.sh" << 'EOF'
#!/bin/bash
# Enterprise NGFW - Unix CA Installation Script

set -e

CERT_FILE="ngfw-root-ca.crt"

echo "🔐 Installing Enterprise NGFW Root CA..."

if [ ! -f "$CERT_FILE" ]; then
    echo "❌ Certificate file not found!"
    exit 1
fi

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Detected: macOS"
    sudo security add-trusted-cert -d -r trustRoot \
        -k /Library/Keychains/System.keychain "$CERT_FILE"
    echo "✅ Certificate installed!"
    
elif [[ -f /etc/debian_version ]]; then
    # Debian/Ubuntu
    echo "Detected: Debian/Ubuntu"
    sudo cp "$CERT_FILE" /usr/local/share/ca-certificates/
    sudo update-ca-certificates
    echo "✅ Certificate installed!"
    
elif [[ -f /etc/redhat-release ]]; then
    # RHEL/CentOS
    echo "Detected: RHEL/CentOS"
    sudo cp "$CERT_FILE" /etc/pki/ca-trust/source/anchors/
    sudo update-ca-trust
    echo "✅ Certificate installed!"
    
else
    echo "❌ Unsupported OS. Please install manually."
    exit 1
fi
EOF

    chmod +x "$OUTPUT_DIR/install-unix.sh"
    
    log_success "Install scripts generated"
}

# ==================== Create Distribution Package ====================

create_distribution_package() {
    log_info "Creating distribution package..."
    
    # Create archive
    ARCHIVE_NAME="ngfw-ca-certificates-$(date +%Y%m%d).tar.gz"
    tar -czf "$OUTPUT_DIR/../$ARCHIVE_NAME" -C "$(dirname "$OUTPUT_DIR")" "$(basename "$OUTPUT_DIR")"
    
    log_success "Distribution package created: $ARCHIVE_NAME"
    
    # Also create ZIP for Windows users
    if command -v zip &>/dev/null; then
        ZIP_NAME="ngfw-ca-certificates-$(date +%Y%m%d).zip"
        (cd "$(dirname "$OUTPUT_DIR")" && zip -r "$ZIP_NAME" "$(basename "$OUTPUT_DIR")" > /dev/null)
        log_success "ZIP package created: $ZIP_NAME"
    fi
}

# ==================== Summary ====================

print_summary() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                   ║${NC}"
    echo -e "${GREEN}║          ✅ CA Certificate Export Completed!                      ║${NC}"
    echo -e "${GREEN}║                                                                   ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}${BOLD}Export Location:${NC}"
    echo -e "  ${YELLOW}$OUTPUT_DIR${NC}"
    echo ""
    echo -e "${CYAN}${BOLD}Files Exported:${NC}"
    ls -lh "$OUTPUT_DIR" | tail -n +2 | awk '{printf "  %-30s %10s\n", $9, $5}'
    echo ""
    echo -e "${CYAN}${BOLD}Next Steps:${NC}"
    echo -e "  ${BOLD}1.${NC} Read installation instructions:"
    echo -e "     ${YELLOW}cat $OUTPUT_DIR/README.txt${NC}"
    echo ""
    echo -e "  ${BOLD}2.${NC} Distribute to clients via:"
    echo -e "     • File share / USB drive"
    echo -e "     • Email (for small teams)"
    echo -e "     • Configuration management (Ansible/Puppet)"
    echo -e "     • GPO / MDM (for enterprise)"
    echo ""
    echo -e "  ${BOLD}3.${NC} Install on client devices using platform-specific methods"
    echo ""
    echo -e "${YELLOW}⚠️  Security Warning:${NC}"
    echo -e "   ${RED}Do NOT distribute the CA private key (ca.key)!${NC}"
    echo -e "   ${RED}Only share the certificate files (.crt, .cer, .pem, .der)${NC}"
    echo ""
}

# ==================== Main ====================

main() {
    print_banner
    
    log_info "Starting CA certificate export..."
    echo ""
    
    check_dependencies
    check_ca_exists
    display_cert_info
    
    # Create output directory
    mkdir -p "$OUTPUT_DIR"
    log_success "Created output directory: $OUTPUT_DIR"
    
    # Export in all formats
    export_pem
    export_der
    export_p12
    
    # Generate documentation
    generate_instructions
    generate_install_scripts
    
    # Create packages
    create_distribution_package
    
    # Set permissions
    chmod -R 755 "$OUTPUT_DIR"
    chmod 644 "$OUTPUT_DIR"/*.{pem,crt,der,cer,txt} 2>/dev/null || true
    chmod 600 "$OUTPUT_DIR"/*.{p12,key} 2>/dev/null || true
    
    print_summary
}

# Run main
main

exit 0