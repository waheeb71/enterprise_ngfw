# 🔥 Enterprise Next-Generation Firewall (NGFW)

**Professional-grade Next-Generation Firewall with advanced SSL inspection, eBPF acceleration, and ML-based threat detection**

## 📋 Overview

Enterprise NGFW is a high-performance, asyncio-based Next-Generation Firewall designed for modern enterprise environments. It combines traditional firewall capabilities with advanced features like deep packet inspection, SSL/TLS interception, and machine learning-based threat detection.

### 🎯 Key Features

#### Core Capabilities
- ✅ **Multiple Proxy Modes**
  - Forward Proxy (Explicit proxy configuration)
  - Transparent Proxy (Gateway mode)
  - Reverse Proxy (Web application protection)
  - Hybrid Mode (Combined operation)

- ✅ **Advanced SSL/TLS Inspection**
  - Dynamic certificate generation per domain
  - Multi-CA support (Root CA + Intermediate CA)
  - Certificate pinning detection and bypass
  - Policy-based inspection decisions
  - TLS 1.2/1.3 support with configurable cipher suites

- ✅ **eBPF XDP Acceleration**
  - Kernel-level packet filtering (XDP/TC)
  - Sub-microsecond latency for blocked traffic
  - Port-based filtering at kernel level
  - Support for 100,000+ IP blocklist entries
  - Adaptive rate limiting

#### Security Features
- ✅ **Smart Blocker**
  - IP/Domain reputation engine
  - GeoIP-based filtering
  - Category-based blocking (90+ categories)
  - Threat intelligence integration
  - Custom blocklists

- ✅ **Deep Packet Inspection (DPI)**
  - Protocol detection and analysis
  - Application identification (7000+ apps)
  - Data Loss Prevention (DLP)
  - Malware scanning hooks
  - Custom inspection plugins

- ✅ **IDS/IPS Integration**
  - Suricata integration
  - Snort support (optional)
  - Zeek/Bro support (optional)
  - Custom signature engine

#### Advanced Features
- ✅ **Flow Tracking**
  - Connection state management
  - Bandwidth monitoring per flow
  - User association (with authentication)
  - Application identification

- ✅ **Machine Learning**
  - Anomaly detection
  - Traffic profiling
  - Adaptive policies
  - Real-time threat prediction

- ✅ **Enterprise Integration**
  - LDAP/Active Directory authentication
  - RADIUS support
  - SIEM integration (Syslog, ELK, Splunk)
  - REST API & WebSocket
  - CLI management tool

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Enterprise NGFW                              │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │         eBPF XDP (Kernel-Level Filtering)              │    │
│  │  • Port filtering  • IP blocking  • Rate limiting      │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ▼                                      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Traffic Router                             │    │
│  │  Routes to: Forward / Transparent / Reverse Proxy      │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ▼                                      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │           SSL/TLS Inspection Engine                     │    │
│  │  • Policy decisions  • Certificate generation           │    │
│  │  • Pinning detection • Multi-CA support                │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ▼                                      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │        Deep Packet Inspection Pipeline                 │    │
│  │  • Protocol analysis  • App detection                   │    │
│  │  • Malware scanning  • DLP engine                       │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ▼                                      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │            Policy Engine & Smart Blocker               │    │
│  │  • Reputation  • Threat Intel  • ML Anomaly            │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 📦 Project Structure

```
enterprise_ngfw/
├── core/                    # Core components
│   ├── router.py           # Traffic routing engine
│   ├── flow_tracker.py     # Connection tracking
│   ├── proxy_modes/        # Proxy implementations
│   └── ssl_engine/         # SSL/TLS inspection
│
├── acceleration/            # Performance optimization
│   └── ebpf/               # eBPF XDP programs
│
├── inspection/             # Deep packet inspection
│   ├── framework/          # Plugin framework
│   └── plugins/            # DPI plugins
│
├── policy/                 # Policy management
│   ├── smart_blocker/      # Intelligent blocking
│   └── behavioral/         # Behavioral analysis
│
├── integration/            # External integrations
│   ├── auth/               # LDAP/AD/RADIUS
│   ├── siem/               # SIEM connectors
│   └── ids_ips/            # IDS/IPS bridges
│
├── telemetry/              # Monitoring & logging
│   ├── metrics/            # Prometheus metrics
│   └── logging/            # Advanced logging
│
├── ml/                     # Machine learning
│   ├── models/             # Trained models
│   └── inference/          # Real-time inference
│
├── api/                    # Management APIs
│   ├── rest/               # REST API
│   ├── websocket/          # WebSocket API
│   └── cli/                # CLI tool
│
└── config/                 # Configuration
    └── defaults/           # Default configs
```

## 🚀 Quick Start

### Prerequisites

```bash
# System requirements
- OS: Linux (Ubuntu 20.04+, RHEL 8+, Debian 11+)
- Kernel: 4.15+ (for eBPF support)
- Python: 3.8+
- RAM: 4GB minimum (8GB recommended)
- CPU: 2+ cores

# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv
sudo apt-get install -y build-essential linux-headers-$(uname -r)

# Optional: Install BCC for eBPF support
sudo apt-get install -y bpfcc-tools linux-headers-$(uname -r)
```

### Installation

```bash
# 1. Clone or extract the project
cd /opt
sudo tar -xzf enterprise_ngfw.tar.gz
cd enterprise_ngfw

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements/base.txt

# 4. Create configuration directory
sudo mkdir -p /etc/ngfw/certs
sudo cp config/defaults/base.yaml /etc/ngfw/config.yaml

# 5. Generate CA certificates
python3 main.py --init-ca -c /etc/ngfw/config.yaml

# 6. Export CA for clients
python3 main.py --export-ca /tmp/ca-export -c /etc/ngfw/config.yaml
```

### Running

```bash
# Development mode
python3 main.py -c /etc/ngfw/config.yaml

# Production mode (with systemd)
sudo systemctl start ngfw
sudo systemctl enable ngfw
```

## ⚙️ Configuration

Edit `/etc/ngfw/config.yaml`:

```yaml
# Proxy mode: forward, transparent, reverse, or all
proxy:
  mode: "forward"
  forward_listen_port: 8080

# SSL inspection
ssl_inspection:
  enabled: true
  bypass_domains:
    - "*.bank.com"
    - "*.paypal.com"

# eBPF XDP
ebpf:
  enabled: true
  interface: "eth0"
  port_filter:
    enabled: true
    allowed_ports: [80, 443, 8080, 8443]
```

## 📊 Usage Examples

### Forward Proxy Mode

```bash
# Configure browser to use proxy:
# HTTP/HTTPS Proxy: localhost:8080

# Or use curl:
curl -x http://localhost:8080 https://www.google.com

# With authentication (future):
curl -x http://user:pass@localhost:8080 https://www.google.com
```

### Transparent Proxy Mode

```bash
# Setup iptables redirection
sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080
sudo iptables -t nat -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-port 8443

# Enable IP forwarding
sudo sysctl -w net.ipv4.ip_forward=1
```

### Reverse Proxy Mode

```yaml
# Configure backend servers in config.yaml
proxy:
  mode: "reverse"
  reverse_listen_port: 443
  backends:
    - host: "backend1.local"
      port: 8000
    - host: "backend2.local"
      port: 8000
```

## 📈 Monitoring

### Prometheus Metrics

```bash
# Metrics endpoint
curl http://localhost:9090/metrics

# Example metrics:
# ngfw_total_connections
# ngfw_active_connections
# ngfw_bytes_sent_total
# ngfw_bytes_received_total
# ngfw_ssl_inspected_total
# ngfw_ssl_bypassed_total
# ngfw_ebpf_packets_blocked
```

### Health Check

```bash
curl http://localhost:9091/health
```

## 🔒 Security

### Installing CA Certificate

After generating CA certificates, install them on client devices:

**Windows:**
```powershell
certutil -addstore -f "ROOT" enterprise-ca.crt
```

**Linux:**
```bash
sudo cp enterprise-ca.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

**macOS:**
```bash
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain enterprise-ca.crt
```

### Best Practices

1. **Change default passwords** in configuration
2. **Enable authentication** for API access
3. **Use strong TLS ciphers** only
4. **Regular updates** of threat intelligence feeds
5. **Monitor logs** for suspicious activity
6. **Backup CA certificates** securely

## 🧪 Testing

```bash
# Run unit tests
python -m pytest tests/unit/

# Run integration tests
python -m pytest tests/integration/

# Performance tests
python -m pytest tests/performance/
```

## 📚 Documentation

- [Architecture Guide](docs/architecture.md)
- [Configuration Reference](docs/configuration.md)
- [API Documentation](docs/api_reference.md)
- [Deployment Guide](docs/deployment/)
- [Plugin Development](docs/plugin_development.md)

## 🛠️ Development

### Adding Custom Inspection Plugin

```python
# inspection/plugins/custom/my_plugin.py
from inspection.framework.plugin_base import InspectionPlugin

class MyPlugin(InspectionPlugin):
    def should_inspect(self, context):
        return context.protocol == "HTTP"
    
    async def inspect(self, context):
        # Your inspection logic
        if "malicious" in context.data:
            return Verdict(action=Action.BLOCK)
        return Verdict(action=Action.ALLOW)
```

### Extending Smart Blocker

```python
# Add custom reputation source
from policy.smart_blocker.reputation_engine import ReputationEngine

engine = ReputationEngine(config)
engine.add_reputation_source("custom", CustomReputationAPI())
```

## 🐛 Troubleshooting

### Common Issues

**eBPF not loading:**
```bash
# Check kernel version
uname -r  # Must be 4.15+

# Check BCC installation
python3 -c "from bcc import BPF; print('BCC OK')"

# Check permissions
sudo setcap cap_sys_admin,cap_net_admin=eip $(which python3)
```

**Certificate errors:**
```bash
# Regenerate certificates
sudo rm -rf /etc/ngfw/certs/*
python3 main.py --init-ca

# Check certificate validity
openssl x509 -in /etc/ngfw/certs/root-ca.crt -text -noout
```

**Performance issues:**
```bash
# Enable eBPF
ebpf:
  enabled: true

# Increase connection limits
proxy:
  max_connections: 50000
  buffer_size: 131072

# Check system limits
ulimit -n  # Should be high (e.g., 65536)
```

## 📝 License

Proprietary - Enterprise Security Team

## 🤝 Contributing

Internal project - contact Enterprise Security Team for access.

## 📞 Support

- Email: security-team@enterprise.local
- Slack: #ngfw-support
- Documentation: https://docs.enterprise.local/ngfw

## 🔄 Version History

### Version 2.0.0 (Current)
- ✨ Complete rewrite with modular architecture
- ✨ Added Forward/Reverse proxy modes
- ✨ Enhanced SSL inspection with policy engine
- ✨ eBPF XDP port filtering
- ✨ Flow tracking system
- ✨ Plugin framework for DPI

### Version 1.0.0
- 🎉 Initial release (MITM Proxy)
- Basic TLS interception
- eBPF IP blocking
- Transparent proxy mode

---

**Built with ❤️ for Enterprise Security Excellence**

*Version: 2.0.0*
*Last Updated: 2024*
