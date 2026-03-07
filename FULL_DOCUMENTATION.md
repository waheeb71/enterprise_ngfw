# 🛡️ Enterprise Next-Generation Firewall (NGFW) - Comprehensive Documentation

## 1. Project Overview
The Enterprise NGFW is a high-performance, modular security solution designed to protect modern network environments. It combines traditional firewalling with advanced features like SSL/TLS inspection, Deep Packet Inspection (DPI), eBPF acceleration, and Machine Learning-based threat detection.

### Key Capabilities
- **Dynamic Proxy Architecture**: Automatically switches between Forward, Transparent, and Reverse proxy modes based on traffic context.
- **Advanced SSL Inspection**: Manages certificate generation, rotation, and pinning bypass for encrypted traffic visibility.
- **High-Performance Filtering**: Utilizes eBPF/XDP (on Linux) for packet filtering at the kernel level.
- **Intelligent Protection**: Integrated Smart Blocker with GeoIP, Reputation, and Anomaly detection.
- **Innovation Features**: Traffic Replay for testing and Threat Intelligence integration.

---

## 2. Architecture & Components

### 2.1 Core Components
- **`main.py`**: The central entry point that orchestrates all services.
- **`core/proxy_modes/dynamic_proxy.py`**: Manages sub-proxies (Forward, Transparent, Reverse).
- **`core/firewall/firewall_engine.py`**: Handles L3/L4 filtering and DPI integration.
- **`core/ssl_engine/ca_pool.py`**: Manages CA certificates and dynamic generation.

### 2.2 Directory Structure
```
enterprise_ngfw/
├── api/            # REST API implementation
├── config/         # Configuration files (defaults/base.yaml)
├── core/           # Core logic (Firewall, Proxy, SSL)
├── ids_ips/        # Suricata/Snort integration
├── ml/             # Machine Learning models
├── scripts/        # Installation & Setup scripts
├── ui/             # Web Dashboard
└── main.py         # Application entry point
```

---

## 3. Installation & Deployment

### 3.1 System Requirements
- **OS**: Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+) or Windows (Limited eBPF support).
- **Python**: 3.9+
- **Root Privileges**: Required for network operations.

### 3.2 Automated Installation (Linux)
Use the provided shell scripts for a complete setup:

1.  **Run the Installer**:
    ```bash
    sudo ./scripts/install.sh
    ```
    This script will:
    - Install system dependencies (Python, libssl, eBPF tools).
    - Create the `ngfw` user and necessary directories.
    - Generate default CA certificates.
    - Install the systemd service.

2.  **Setup Transparent Proxy** (Optional):
    ```bash
    sudo ./scripts/setup-transparent-proxy.sh
    ```
    This script configures `iptables` to redirect traffic to the firewall ports (8444/8081).

### 3.3 Docker Deployment
For containerized environments:

```bash
docker-compose up --build -d
```
This starts:
- **NGFW**: The main firewall application.
- **Prometheus**: For metrics collection (Port 9090).
- **Suricata**: (Optional) For IDS/IPS.

---

## 4. Configuration

The primary configuration file is located at `config/defaults/base.yaml` (or `/etc/enterprise-ngfw/config.yaml` after install).

### 4.1 Key Settings

**Proxy Configuration:**
```yaml
proxy:
  mode: "dynamic"
  forward:
    listen_port: 8081
  transparent:
    listen_port: 8444
    http_port: 8081
```

**SSL Inspection:**
```yaml
tls:
  enabled: true
  inspection:
    bypass_categories: ["banking", "health"]
  ca:
    auto_rotation: true
```

**Firewall & Protection:**
```yaml
firewall:
  enabled: true
  ebpf:
    enabled: true  # Set to false on Windows
protection:
  smart_blocker:
    geoip_blocking:
      enabled: true
      blocked_countries: ["XX"]
```

---

## 5. Usage & Management

### 5.1 Starting the Service
- **Systemd**: `sudo systemctl start enterprise-ngfw`
- **Manual**: `python main.py`

### 5.2 Web Dashboard
Access the real-time dashboard at:
- **URL**: `http://localhost:8889/dashboard.html` (or open `ui/dashboard.html` locally)
- **Features**: View active connections, blocked threats, and system health.

### 5.3 REST API
Manage the firewall programmatically via the API (Port 8889):
- `GET /status`: System health and stats.
- `GET /metrics`: Prometheus metrics.
- `POST /firewall/rules`: Add new blocking rules.

### 5.4 Client Configuration
For SSL inspection to work without warnings, you must install the Root CA certificate on client devices:
- **Certificate Path**: `certs/root-ca.crt` (or `/etc/enterprise-ngfw/certs/ca.crt`)
- **Installation**: Import into the "Trusted Root Certification Authorities" store.

---

## 6. Troubleshooting

### Common Issues
1.  **"Port already in use"**:
    - Check if another service is using ports 8081, 8444, or 8889.
    - Edit `base.yaml` to change ports.

2.  **SSL Warnings on Clients**:
    - Ensure the Root CA is correctly installed and trusted on the client.

3.  **eBPF Errors**:
    - Ensure you are running on a supported Linux kernel (5.3+).
    - On Windows, eBPF is simulated; check logs for "Simulation Mode".

### Logs
- **Application Log**: `/var/log/ngfw/ngfw.log`
- **Systemd Log**: `journalctl -u enterprise-ngfw -f`

---

## 7. Innovation Features

### Traffic Replay
Capture and replay traffic to test policy changes safely.
- **Enable**: Set `innovation.traffic_replay.enabled: true` in config.
- **Usage**: Use API to start/stop recording sessions.

### Threat Intelligence
Automatically blocks IPs from external feeds.
- **Config**: Add feed URLs to `innovation.threat_intel.sources`.
