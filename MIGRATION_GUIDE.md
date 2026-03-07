# 📦 Migration Guide - من MITM Proxy إلى NGFW 2.0

## نظرة عامة

هذا الدليل يشرح كيفية الانتقال من النظام القديم (MITM Proxy 1.0) إلى النظام الجديد (NGFW 2.0).

---

## 🔄 التغييرات الرئيسية

### 1. الهيكلة المعمارية

#### النظام القديم (v1.0):
```
old_system/
├── ca_manager.py
├── mitm_proxy.py
├── ebpf_manager.py
└── main.py
```

#### النظام الجديد (v2.0):
```
enterprise_ngfw/
├── core/
│   ├── proxy_modes/
│   └── ssl_engine/
├── acceleration/ebpf/
├── inspection/
├── policy/
└── integration/
```

### 2. تغييرات الأسماء

| القديم | الجديد |
|--------|--------|
| `CAManager` | `CAPoolManager` |
| `MITMProxy` | `TransparentProxy` |
| `eBPFManager` | `XDPEngine` |
| `create_ebpf_manager()` | `create_xdp_engine()` |

### 3. تغييرات الـ Imports

#### القديم:
```python
from ca_manager import CAManager
from mitm_proxy import MITMProxy
from ebpf_manager import create_ebpf_manager
```

#### الجديد:
```python
from core.ssl_engine.ca_pool import CAPoolManager
from core.proxy_modes import TransparentProxy
from acceleration.ebpf.xdp_engine import create_xdp_engine
```

---

## 🔧 تحديث الكود

### مثال 1: إنشاء CA Manager

#### القديم:
```python
from ca_manager import CAManager

ca_manager = CAManager(config)
cert, key = ca_manager.generate_server_certificate("example.com")
```

#### الجديد:
```python
from core.ssl_engine.ca_pool import CAPoolManager

ca_manager = CAPoolManager(config)
cert, key = ca_manager.generate_server_certificate("example.com")
```

### مثال 2: تشغيل Proxy

#### القديم:
```python
from mitm_proxy import MITMProxy

proxy = MITMProxy(config, ca_manager, ebpf_manager)
await proxy.start()
```

#### الجديد - خيار 1 (Transparent Mode):
```python
from core.proxy_modes import TransparentProxy

proxy = TransparentProxy(config, ca_manager, ebpf_manager)
await proxy.start()
```

#### الجديد - خيار 2 (Forward Mode):
```python
from core.proxy_modes import ForwardProxy

proxy = ForwardProxy(config, ca_manager, flow_tracker)
await proxy.start()
```

#### الجديد - خيار 3 (Reverse Mode):
```python
from core.proxy_modes import ReverseProxy

proxy = ReverseProxy(config, ca_manager, flow_tracker)
await proxy.start()
```

### مثال 3: eBPF/XDP

#### القديم:
```python
from ebpf_manager import create_ebpf_manager

ebpf = create_ebpf_manager(config)
await ebpf.start()
await ebpf.add_blocked_ip("1.2.3.4")
```

#### الجديد:
```python
from acceleration.ebpf.xdp_engine import create_xdp_engine

xdp = create_xdp_engine(config)
await xdp.start()
await xdp.add_blocked_ip("1.2.3.4")
```

---

## ⚙️ تحديث ملف الإعدادات

### القديم (config.yaml):
```yaml
proxy:
  listen_host: "0.0.0.0"
  listen_port: 8443
  http_port: 8080
  mode: "transparent"

tls:
  ca_cert_path: "/etc/mitm-proxy2/certs/root-ca.crt"
  ca_key_path: "/etc/mitm-proxy2/certs/root-ca.key"
```

### الجديد (config.yaml):
```yaml
proxy:
  mode: "transparent"  # أو forward, reverse
  
  # Transparent Proxy
  transparent_listen_host: "0.0.0.0"
  transparent_listen_port: 8443
  
  # Forward Proxy
  forward_listen_host: "0.0.0.0"
  forward_listen_port: 8080

tls:
  ca_cert_path: "/etc/ngfw/certs/root-ca.crt"
  ca_key_path: "/etc/ngfw/certs/root-ca.key"
  
# جديد: SSL Policy
ssl_inspection:
  enabled: true
  bypass_domains:
    - "*.bank.com"
```

---

## 📊 الميزات الجديدة المتاحة

### 1. أنماط Proxy متعددة

```yaml
proxy:
  mode: "all"  # تشغيل جميع الأنماط معاً
```

### 2. Flow Tracking

```python
from core.flow_tracker import FlowTracker

flow_tracker = FlowTracker(config)
await flow_tracker.start()

# Create flow
flow = flow_tracker.create_flow(
    client_ip="10.0.0.5",
    client_port=12345,
    server_ip="93.184.216.34",
    server_port=443,
    protocol="HTTPS"
)

# Update traffic
flow_tracker.update_flow_traffic(flow.flow_id, sent=1024, received=2048)
```

### 3. SSL Policy Engine

```python
from core.ssl_engine.policy_engine import SSLPolicyEngine

policy = SSLPolicyEngine(config)

# Decide whether to inspect
action = policy.decide(
    client_ip="10.0.0.5",
    target_host="example.com",
    category="shopping"
)
# Returns: SSLAction.INSPECT or SSLAction.BYPASS
```

### 4. Traffic Router

```python
from core.router import TrafficRouter

router = TrafficRouter(config)

# Route connection
decision = await router.route(
    client_addr=("10.0.0.5", 12345),
    local_port=443,
    initial_data=client_hello_data
)
# Returns: RoutingDecision with mode and target
```

---

## 🚀 خطوات الترحيل

### الخطوة 1: النسخ الاحتياطي
```bash
# Backup old system
sudo cp -r /opt/mitm-proxy2 /opt/mitm-proxy2.backup
sudo cp /etc/mitm-proxy2/config.yaml /etc/mitm-proxy2/config.yaml.backup
```

### الخطوة 2: تثبيت النظام الجديد
```bash
# Extract new system
cd /opt
sudo tar -xzf enterprise_ngfw.tar.gz

# Install dependencies
cd enterprise_ngfw
python3 -m venv venv
source venv/bin/activate
pip install -r requirements/base.txt
```

### الخطوة 3: نقل الإعدادات
```bash
# Create new config directory
sudo mkdir -p /etc/ngfw

# Convert old config to new format
python3 scripts/migrate_config.py \
  /etc/mitm-proxy2/config.yaml \
  /etc/ngfw/config.yaml
```

### الخطوة 4: نقل الشهادات
```bash
# Copy CA certificates
sudo mkdir -p /etc/ngfw/certs
sudo cp /opt/mitm-proxy2/certs/root-ca.crt /etc/ngfw/certs/
sudo cp /opt/mitm-proxy2/certs/root-ca.key /etc/ngfw/certs/
sudo cp /opt/mitm-proxy2/certs/intermediate-ca.* /etc/ngfw/certs/
```

### الخطوة 5: اختبار النظام الجديد
```bash
# Test configuration
python3 main.py -c /etc/ngfw/config.yaml --test

# Export CA (if needed)
python3 main.py --export-ca /tmp/ca-export
```

### الخطوة 6: التشغيل
```bash
# Stop old system
sudo systemctl stop mitm-proxy2

# Start new system
cd /opt/enterprise_ngfw
source venv/bin/activate
python3 main.py -c /etc/ngfw/config.yaml
```

---

## ⚠️ ملاحظات مهمة

### 1. التوافق مع الـ CA
الشهادات القديمة متوافقة تماماً. لا حاجة لإعادة تثبيتها على الأجهزة.

### 2. أداء eBPF
النظام الجديد يستخدم نفس XDP code، لكن مع تحسينات:
- Port filtering في kernel space
- إحصائيات أفضل
- دعم TC (Traffic Control)

### 3. مسارات الملفات
```
القديم: /opt/mitm-proxy2/
        /etc/mitm-proxy2/
        /var/log/mitm-proxy2/

الجديد: /opt/enterprise_ngfw/
        /etc/ngfw/
        /var/log/ngfw/
```

### 4. Systemd Service
```bash
# إنشاء service جديد
sudo nano /etc/systemd/system/ngfw.service

[Unit]
Description=Enterprise NGFW
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/enterprise_ngfw
ExecStart=/opt/enterprise_ngfw/venv/bin/python3 main.py -c /etc/ngfw/config.yaml
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable ngfw
sudo systemctl start ngfw
```

---

## 🔍 التحقق من الترحيل

### 1. فحص الـ Logs
```bash
# Old system logs
tail -f /var/log/mitm-proxy2/proxy.log

# New system logs
tail -f /var/log/ngfw/ngfw.log
```

### 2. فحص الاتصالات
```bash
# Test with curl
curl -x http://localhost:8080 https://www.google.com

# Check statistics
curl http://localhost:9090/metrics
```

### 3. فحص eBPF
```bash
# Old
sudo bpftool prog list | grep xdp

# New (same)
sudo bpftool prog list | grep xdp
```

---

## 🆘 استكشاف الأخطاء

### خطأ: Module not found
```bash
# الحل: تأكد من تفعيل virtual environment
source /opt/enterprise_ngfw/venv/bin/activate
```

### خطأ: Permission denied
```bash
# الحل: تشغيل بصلاحيات root
sudo python3 main.py
```

### خطأ: CA certificates not found
```bash
# الحل: توليد شهادات جديدة
python3 main.py --init-ca -c /etc/ngfw/config.yaml
```

---

## 📞 الدعم

إذا واجهتك مشاكل أثناء الترحيل:

1. راجع الـ logs في `/var/log/ngfw/`
2. تحقق من ملف الإعدادات `/etc/ngfw/config.yaml`
3. اتصل بفريق الأمن: security-team@enterprise.local

---

**نجاح الترحيل! 🎉**

النظام الجديد يوفر:
- ✅ أداء أفضل
- ✅ ميزات أكثر
- ✅ هيكلة أنظف
- ✅ قابلية توسع أعلى
