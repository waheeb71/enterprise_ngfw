# 🚀 Enterprise NGFW - Phase 5 & 6 Complete Guide

## 📦 Package Information

**Package**: `enterprise_ngfw_phase5_6.tar.gz`  
**Size**: 35 KB  
**MD5**: `2b569337e451444848ecf5ac2acf66a4`  
**Files**: 18 files, ~4,024 lines of code  
**Status**: ✅ Production Ready

---

## 📋 Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Phase 5: ML Integration](#phase-5-ml-integration)
4. [Phase 6: API & Dashboard](#phase-6-api--dashboard)
5. [Integration Examples](#integration-examples)
6. [Configuration](#configuration)
7. [Production Deployment](#production-deployment)
8. [Troubleshooting](#troubleshooting)

---

## 🔧 Installation

### 1. Extract Package

```bash
tar -xzf enterprise_ngfw_phase5_6.tar.gz
cd enterprise-ngfw-v2
```

### 2. Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install requirements
pip install -r requirements_phase5_6.txt
```

### 3. Verify Installation

```bash
# Test ML components
python examples/test_ml.py

# Test API (in another terminal)
cd api/rest
python main.py
```

---

## 🚀 Quick Start

### Starting the Complete System

```bash
# Terminal 1: Start API Server
cd api/rest
python main.py
# API: http://localhost:8000
# Docs: http://localhost:8000/docs

# Terminal 2: Start Dashboard
cd api/dashboard
python -m http.server 8080
# Dashboard: http://localhost:8080

# Terminal 3: Use CLI
cd api/cli
chmod +x ngfw_cli.py
./ngfw_cli.py auth login --username admin --password admin123
./ngfw_cli.py status show
```

### First API Request

```bash
# 1. Login and get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')

# 2. Get system status
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/status | jq

# 3. Get traffic statistics
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/statistics | jq
```

---

## 🤖 Phase 5: ML Integration

### Component 1: Anomaly Detector

**Purpose**: Real-time anomaly detection using Isolation Forest

**Basic Usage**:
```python
from ml.inference import AnomalyDetector, TrafficFeatures

# Initialize detector
detector = AnomalyDetector(
    contamination=0.1,    # Expected 10% anomalies
    n_estimators=100,     # 100 trees
    max_samples=1000      # Max training samples
)

# Create features from traffic
features = TrafficFeatures(
    packets_per_second=1500,
    bytes_per_second=750000,
    avg_packet_size=500,
    packet_size_variance=100,
    tcp_ratio=0.7,
    udp_ratio=0.3,
    syn_ratio=0.1,
    unique_dst_ports=5,
    unique_src_ports=10,
    inter_arrival_time_mean=0.01,
    inter_arrival_time_variance=0.001,
    failed_connections=0,
    connection_attempts=10,
    reputation_score=80.0
)

# Detect anomaly
result = detector.detect(features)

if result.is_anomaly:
    print(f"⚠️ Anomaly detected!")
    print(f"   Score: {result.anomaly_score:.3f}")
    print(f"   Reason: {result.reason}")
    print(f"   Confidence: {result.confidence:.3f}")
```

**Integration with NGFW**:
```python
class NGFWEngine:
    def __init__(self):
        self.anomaly_detector = AnomalyDetector()
    
    def process_packet(self, packet):
        # Extract features from packet
        features = self.extract_features(packet)
        
        # Detect anomaly
        result = self.anomaly_detector.detect(features)
        
        if result.is_anomaly and result.confidence > 0.8:
            # Take action
            self.block_source(packet.src_ip)
            self.log_alert("Anomaly detected", result)
```

---

### Component 2: Traffic Profiler

**Purpose**: Pattern detection and behavioral profiling

**Basic Usage**:
```python
from ml.inference import TrafficProfiler, TrafficPattern

# Initialize profiler
profiler = TrafficProfiler(
    time_window=300,      # 5 minute window
    max_profiles=10000    # Track 10K IPs
)

# Profile a connection
pattern, confidence = profiler.profile_connection(
    src_ip="192.168.1.100",
    dst_ip="8.8.8.8",
    dst_port=443,
    protocol="TCP",
    bytes_sent=5000,
    bytes_recv=3000,
    packets_sent=10,
    packets_recv=8,
    duration=1.0
)

# Check pattern
if pattern == TrafficPattern.SCANNING:
    print("⚠️ Port scanning detected!")
elif pattern == TrafficPattern.DDOS:
    print("🚨 DDoS attack detected!")

# Get IP profile
profile = profiler.get_ip_profile("192.168.1.100")
print(f"Reputation: {profile.reputation_score:.1f}")
print(f"Connections: {profile.total_connections}")
print(f"Patterns: {profile.patterns_detected}")

# Get low reputation IPs
suspicious_ips = profiler.get_low_reputation_ips(threshold=40.0)
for ip, score in suspicious_ips:
    print(f"{ip}: {score:.1f}")
```

**Pattern Detection Examples**:

```python
# Scanning Detection
for port in range(1, 100):
    profiler.profile_connection(
        src_ip="attacker.com",
        dst_ip="target.com",
        dst_port=port,
        protocol="TCP",
        bytes_sent=64,
        packets_sent=1
    )
# Result: SCANNING pattern detected

# DDoS Detection
for i in range(2000):
    profiler.profile_connection(
        src_ip="botnet.com",
        dst_ip="target.com",
        dst_port=80,
        protocol="TCP",
        bytes_sent=0,
        packets_sent=1
    )
# Result: DDOS pattern detected

# C2 Communication Detection
# Regular beaconing with small packets
for i in range(10):
    time.sleep(60)  # Every minute
    profiler.profile_connection(
        src_ip="infected.host",
        dst_ip="c2.server",
        dst_port=8443,
        protocol="TCP",
        bytes_sent=128,
        packets_sent=2
    )
# Result: C2_COMMUNICATION pattern detected
```

---

### Component 3: Adaptive Policy Engine

**Purpose**: ML-driven dynamic policy adjustment

**Basic Usage**:
```python
from ml.inference import AdaptivePolicyEngine, PolicyAction

# Initialize engine
engine = AdaptivePolicyEngine(
    learning_rate=0.1,
    adaptation_interval=300,  # Adapt every 5 minutes
    min_confidence=0.7
)

# Evaluate traffic
action, confidence, reason = engine.evaluate(
    src_ip="192.168.1.100",
    dst_ip="8.8.8.8",
    dst_port=443,
    protocol="TCP",
    anomaly_score=0.85,
    reputation_score=35.0,
    pattern="scanning"
)

# Take action
if action == PolicyAction.BLOCK:
    print(f"🚫 BLOCK: {reason}")
elif action == PolicyAction.THROTTLE:
    print(f"⚠️ THROTTLE: {reason}")
elif action == PolicyAction.ALLOW:
    print(f"✅ ALLOW: {reason}")

# Add feedback for learning
engine.add_feedback(
    src_ip="192.168.1.100",
    action_taken=action,
    was_threat=True,
    threat_type="scanning"
)

# Create dynamic rule
rule_id = engine.create_dynamic_rule(
    condition="dst_port == 23",  # Telnet
    action=PolicyAction.BLOCK,
    priority=150,
    confidence=0.95,
    reason="Insecure protocol"
)

# Get metrics
metrics = engine.get_metrics()
print(f"Accuracy: {metrics.calculate_accuracy():.2%}")
print(f"False Positives: {metrics.false_positives}")
print(f"False Negatives: {metrics.false_negatives}")
```

**Adaptive Behavior**:

The engine automatically:
1. **Adjusts thresholds** based on false positive/negative rates
2. **Creates rules** for repeat offenders (5+ threats from same IP)
3. **Removes ineffective rules** (not triggered in 1 hour)
4. **Optimizes performance** using feedback loop

---

### Component 4: Model Trainer

**Purpose**: Offline model training and optimization

**Basic Usage**:
```python
from ml.training import ModelTrainer, TrainingConfig, generate_training_data

# Generate or load training data
X, y, feature_names = generate_training_data(n_samples=10000)

# Initialize trainer
trainer = ModelTrainer(model_dir="./models")

# Train anomaly detector
config = TrainingConfig(
    model_type="isolation_forest",
    n_estimators=200,
    contamination=0.1
)
result = trainer.train_anomaly_detector(X, feature_names, config)

# Train classifier
config = TrainingConfig(
    model_type="random_forest",
    n_estimators=200,
    test_size=0.2
)
result = trainer.train_classifier(X, y, feature_names, config)

print(f"Accuracy: {result.accuracy:.4f}")
print(f"F1 Score: {result.f1_score:.4f}")

# Feature importance
for feature, importance in result.feature_importance.items():
    print(f"{feature}: {importance:.4f}")

# Hyperparameter optimization
best_params = trainer.optimize_hyperparameters(X, y)
print(f"Best params: {best_params}")
```

---

## 🌐 Phase 6: API & Dashboard

### Component 1: FastAPI REST API

**Starting the API**:
```bash
cd api/rest
python main.py

# Production with Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

**Authentication**:
```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"username": "admin", "password": "admin123"}
)
token = response.json()["access_token"]

# Use token in requests
headers = {"Authorization": f"Bearer {token}"}
```

**API Examples**:

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Get token
r = requests.post(f"{BASE_URL}/auth/login", 
    json={"username": "admin", "password": "admin123"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 1. System Status
status = requests.get(f"{BASE_URL}/status", headers=headers).json()
print(f"Status: {status['status']}")
print(f"CPU: {status['cpu_usage']}%")

# 2. Traffic Statistics
stats = requests.get(f"{BASE_URL}/statistics?time_window=300", 
    headers=headers).json()
print(f"Total packets: {stats['total_packets']}")
print(f"Blocked: {stats['blocked_packets']}")

# 3. Create Rule
rule = {
    "dst_port": 22,
    "action": "BLOCK",
    "priority": 200
}
r = requests.post(f"{BASE_URL}/rules", json=rule, headers=headers)
print(f"Created rule: {r.json()['rule_id']}")

# 4. List Rules
rules = requests.get(f"{BASE_URL}/rules", headers=headers).json()
for rule in rules:
    print(f"{rule['rule_id']}: {rule['action']}")

# 5. Block IP
r = requests.post(f"{BASE_URL}/block/192.168.1.100?duration=3600", 
    headers=headers)
print(r.json())

# 6. Get Anomalies
anomalies = requests.get(f"{BASE_URL}/anomalies?limit=10", 
    headers=headers).json()
for anomaly in anomalies:
    print(f"{anomaly['src_ip']}: {anomaly['anomaly_score']}")

# 7. Evaluate Policy
r = requests.post(f"{BASE_URL}/policy/evaluate",
    params={
        "src_ip": "192.168.1.100",
        "dst_ip": "8.8.8.8",
        "dst_port": 443,
        "protocol": "TCP"
    },
    headers=headers)
print(r.json())

# 8. Get IP Profile
profile = requests.get(f"{BASE_URL}/profiles/192.168.1.100", 
    headers=headers).json()
print(f"Reputation: {profile['reputation_score']}")
```

**Rate Limits**:
- `/auth/login`: 5/min
- `/status`, `/statistics`, `/rules`, `/anomalies`: 60/min
- `/rules` (POST/PUT/DELETE): 30/min (admin only)
- `/policy/evaluate`: 1000/min

---

### Component 2: WebSocket Real-time

**Client Example**:

```html
<!DOCTYPE html>
<html>
<head>
    <title>NGFW Live Monitor</title>
</head>
<body>
    <h1>Live Statistics</h1>
    <div id="stats"></div>
    <div id="alerts"></div>

    <script>
        const token = "YOUR_JWT_TOKEN";
        const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);
        
        ws.onopen = () => {
            console.log('Connected');
            
            // Subscribe to stats
            ws.send(JSON.stringify({
                type: 'subscribe',
                room: 'stats'
            }));
            
            // Subscribe to alerts
            ws.send(JSON.stringify({
                type: 'subscribe',
                room: 'alerts'
            }));
        };
        
        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            
            if (message.type === 'stats') {
                const data = message.data;
                document.getElementById('stats').innerHTML = `
                    <p>Packets/sec: ${data.packets_per_second}</p>
                    <p>Active connections: ${data.active_connections}</p>
                    <p>Blocked: ${data.blocked_count}</p>
                `;
            }
            else if (message.type === 'alert') {
                const alert = message.data;
                const alertDiv = document.getElementById('alerts');
                alertDiv.innerHTML += `
                    <div class="alert ${alert.severity}">
                        <strong>${alert.alert_type}</strong>
                        ${alert.source_ip} → ${alert.destination_ip}
                        <p>${alert.description}</p>
                    </div>
                `;
            }
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        ws.onclose = () => {
            console.log('Disconnected');
            // Reconnect logic
            setTimeout(() => location.reload(), 5000);
        };
    </script>
</body>
</html>
```

**Python Client**:

```python
import asyncio
import websockets
import json

async def monitor():
    uri = "ws://localhost:8000/ws?token=YOUR_JWT_TOKEN"
    
    async with websockets.connect(uri) as websocket:
        # Subscribe to stats
        await websocket.send(json.dumps({
            'type': 'subscribe',
            'room': 'stats'
        }))
        
        # Subscribe to alerts
        await websocket.send(json.dumps({
            'type': 'subscribe',
            'room': 'alerts'
        }))
        
        # Receive messages
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            
            if data['type'] == 'stats':
                print(f"Stats: {data['data']}")
            elif data['type'] == 'alert':
                print(f"🚨 Alert: {data['data']}")

asyncio.run(monitor())
```

---

### Component 3: CLI Tool

**Installation**:
```bash
cd api/cli
chmod +x ngfw_cli.py

# Optional: Add to PATH
sudo ln -s $(pwd)/ngfw_cli.py /usr/local/bin/ngfw
```

**Usage Examples**:

```bash
# Authentication
ngfw auth login --username admin --password admin123
ngfw auth whoami
ngfw auth logout

# System Status
ngfw status show
ngfw status health

# Statistics
ngfw stats show --window 300

# Rules Management
ngfw rules list
ngfw rules list --format json
ngfw rules add --dst-port 22 --action BLOCK --priority 200
ngfw rules add --src-ip 192.168.1.0/24 --dst-port 23 --action BLOCK
ngfw rules delete rule_20240120_123456

# IP Blocking
ngfw block add 192.168.1.100 --duration 3600
ngfw block remove 192.168.1.100

# Anomalies
ngfw anomalies list --limit 20

# IP Profiles
ngfw profile show 192.168.1.100
```

**Configuration**:
The CLI stores configuration in `~/.ngfw/config.yaml`:
```yaml
api_url: http://localhost:8000/api/v1
token: eyJ...
username: admin
```

---

### Component 4: Web Dashboard

**Starting the Dashboard**:
```bash
cd api/dashboard
python -m http.server 8080

# Access at: http://localhost:8080
```

**Features**:
- ✅ Real-time statistics cards
- ✅ Live traffic chart (Chart.js)
- ✅ Protocol distribution pie chart
- ✅ Top blocked IPs bar chart
- ✅ Recent alerts table
- ✅ Responsive design
- ✅ Dark theme

**Customization**:

Edit `index.html` to customize:
- Update `API_URL` and `WS_URL`
- Modify chart colors
- Add new widgets
- Change refresh intervals

---

## 🔗 Integration Examples

### Full NGFW Integration

```python
from ml.inference import AnomalyDetector, TrafficProfiler, AdaptivePolicyEngine
from ml.inference import TrafficFeatures, PolicyAction

class EnterpriseNGFW:
    def __init__(self):
        # Initialize ML components
        self.anomaly_detector = AnomalyDetector()
        self.traffic_profiler = TrafficProfiler()
        self.policy_engine = AdaptivePolicyEngine()
    
    def process_connection(self, conn_data):
        """Process a network connection"""
        
        # 1. Profile the connection
        pattern, pattern_confidence = self.traffic_profiler.profile_connection(
            src_ip=conn_data['src_ip'],
            dst_ip=conn_data['dst_ip'],
            dst_port=conn_data['dst_port'],
            protocol=conn_data['protocol'],
            bytes_sent=conn_data['bytes_sent'],
            packets_sent=conn_data['packets_sent']
        )
        
        # 2. Get IP profile
        ip_profile = self.traffic_profiler.get_ip_profile(conn_data['src_ip'])
        reputation = ip_profile.reputation_score if ip_profile else 100.0
        
        # 3. Extract features for anomaly detection
        features = self.extract_features(conn_data)
        
        # 4. Detect anomaly
        anomaly_result = self.anomaly_detector.detect(features)
        
        # 5. Evaluate policy
        action, confidence, reason = self.policy_engine.evaluate(
            src_ip=conn_data['src_ip'],
            dst_ip=conn_data['dst_ip'],
            dst_port=conn_data['dst_port'],
            protocol=conn_data['protocol'],
            anomaly_score=anomaly_result.anomaly_score,
            reputation_score=reputation,
            pattern=pattern.value
        )
        
        # 6. Log decision
        self.log_decision(conn_data, action, reason, confidence)
        
        # 7. Take action
        if action == PolicyAction.BLOCK:
            self.block_connection(conn_data['src_ip'])
        elif action == PolicyAction.THROTTLE:
            self.throttle_connection(conn_data['src_ip'])
        
        return action
    
    def extract_features(self, conn_data):
        """Extract ML features from connection"""
        return TrafficFeatures(
            packets_per_second=conn_data.get('pps', 0),
            bytes_per_second=conn_data.get('bps', 0),
            # ... other features
        )
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# API Configuration
export NGFW_API_HOST=0.0.0.0
export NGFW_API_PORT=8000
export NGFW_SECRET_KEY="your-secret-key-here"
export NGFW_TOKEN_EXPIRE=30

# ML Configuration
export NGFW_ML_CONTAMINATION=0.1
export NGFW_ML_TIME_WINDOW=300
export NGFW_ML_LEARNING_RATE=0.1

# Logging
export NGFW_LOG_LEVEL=INFO
export NGFW_LOG_FILE=/var/log/ngfw/ngfw.log
```

### Production Settings

```python
# api/rest/main.py

# Security
SECRET_KEY = os.getenv("NGFW_SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("NGFW_TOKEN_EXPIRE", 30))

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # Restrict origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Rate Limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000/hour"]
)
```

---

## 🚀 Production Deployment

### 1. Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements_phase5_6.txt .
RUN pip install --no-cache-dir -r requirements_phase5_6.txt

COPY ml/ ml/
COPY api/ api/

EXPOSE 8000

CMD ["uvicorn", "api.rest.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t ngfw-api .
docker run -p 8000:8000 -e NGFW_SECRET_KEY=secret ngfw-api
```

### 2. Systemd Service

```ini
# /etc/systemd/system/ngfw-api.service
[Unit]
Description=Enterprise NGFW API
After=network.target

[Service]
Type=simple
User=ngfw
WorkingDirectory=/opt/enterprise-ngfw-v2
Environment="NGFW_SECRET_KEY=your-secret-key"
ExecStart=/opt/enterprise-ngfw-v2/venv/bin/uvicorn api.rest.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ngfw-api
sudo systemctl start ngfw-api
```

### 3. Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name ngfw.example.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 🐛 Troubleshooting

### Common Issues

**1. Import Error: No module named 'ml'**
```bash
# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/enterprise-ngfw-v2"
```

**2. JWT Token Expired**
```bash
# Re-login
ngfw auth login --username admin --password admin123
```

**3. WebSocket Connection Failed**
```javascript
// Check token in browser console
console.log('Token:', localStorage.getItem('ngfw_token'));

// Reconnect with new token
ws.close();
ws = new WebSocket(`ws://localhost:8000/ws?token=${newToken}`);
```

**4. ML Model Not Training**
```python
# Check sample count
print(f"Samples: {detector.samples_collected}")

# Manual training
detector.train_model()
```

**5. Rate Limit Exceeded**
```bash
# Wait for reset or use exponential backoff
sleep 60
```

---

## 📊 Performance Tuning

### ML Optimization

```python
# Anomaly Detector
detector = AnomalyDetector(
    n_estimators=50,      # Reduce for faster inference
    max_samples=500,      # Smaller training set
    contamination=0.05    # Adjust based on your traffic
)

# Traffic Profiler
profiler = TrafficProfiler(
    time_window=180,      # Shorter window for faster cleanup
    max_profiles=5000     # Limit memory usage
)

# Adaptive Policy
engine = AdaptivePolicyEngine(
    learning_rate=0.05,   # Slower adaptation
    adaptation_interval=600  # Less frequent updates
)
```

### API Optimization

```bash
# Run with more workers
uvicorn api.rest.main:app --workers 4 --host 0.0.0.0 --port 8000

# Or with Gunicorn
gunicorn api.rest.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Examples**: See `examples/test_ml.py`
- **Source Code**: Well-commented, production-ready
- **Phase Summary**: See `PHASE5_6_SUMMARY.md`

---

## ✅ Checklist for Production

- [ ] Change default SECRET_KEY
- [ ] Use strong passwords (bcrypt hashing)
- [ ] Configure CORS properly
- [ ] Enable HTTPS/WSS
- [ ] Set up proper logging
- [ ] Configure rate limits
- [ ] Use environment variables
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Implement backup strategy
- [ ] Test load capacity
- [ ] Document API for team
- [ ] Set up CI/CD pipeline

---

**Status**: ✅ Phase 5 & 6 Complete - Ready for Production!

**Next Steps**: Integrate with existing Phase 2-4 components and deploy!