# ⚡ Quick Start - Enterprise NGFW

## 🎯 تشغيل سريع في 5 دقائق

### الخطوة 1: فك الضغط (30 ثانية)

```bash
cd /opt
sudo tar -xzf enterprise_ngfw_v2.0.tar.gz
cd enterprise_ngfw
```

### الخطوة 2: التثبيت (2 دقيقة)

```bash
# إنشاء virtual environment
python3 -m venv venv
source venv/bin/activate

# تثبيت المتطلبات
pip install -r requirements.txt
```

### الخطوة 3: الإعدادات (1 دقيقة)

```bash
# إنشاء مجلد الإعدادات
sudo mkdir -p /etc/ngfw/certs

# نسخ الإعدادات الافتراضية
sudo cp config/defaults/base.yaml /etc/ngfw/config.yaml

# توليد شهادات CA
python3 main.py --init-ca -c /etc/ngfw/config.yaml
```

### الخطوة 4: التشغيل (30 ثانية)

```bash
# تشغيل Forward Proxy على المنفذ 8080
python3 main.py -c /etc/ngfw/config.yaml
```

### الخطوة 5: الاختبار (30 ثانية)

```bash
# في terminal آخر:
curl -x http://localhost:8080 https://www.google.com
```

---

## 🔧 إعدادات سريعة

### Forward Proxy Mode (الأسهل)

```yaml
# /etc/ngfw/config.yaml
proxy:
  mode: "forward"
  forward_listen_port: 8080
```

ثم في المتصفح:
```
HTTP Proxy: localhost
Port: 8080
```

### Transparent Proxy Mode (للـ Gateway)

```yaml
proxy:
  mode: "transparent"
  transparent_listen_port: 8443
```

ثم:
```bash
# إعادة توجيه الترافيك
sudo iptables -t nat -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-port 8443
sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080
```

### Reverse Proxy Mode (للحماية)

```yaml
proxy:
  mode: "reverse"
  reverse_listen_port: 443
  backends:
    - host: "localhost"
      port: 8000
```

---

## 📊 أوامر مفيدة

```bash
# عرض الـ logs
tail -f /var/log/ngfw/ngfw.log

# عرض الإحصائيات (Prometheus)
curl http://localhost:9090/metrics

# فحص الصحة
curl http://localhost:9091/health

# تصدير CA للأجهزة
python3 main.py --export-ca /tmp/ca-export -c /etc/ngfw/config.yaml
```

---

## 🆘 مشاكل شائعة

### خطأ: Permission denied
```bash
# الحل: تشغيل بصلاحيات root
sudo python3 main.py -c /etc/ngfw/config.yaml
```

### خطأ: Port already in use
```bash
# الحل: تغيير المنفذ في config.yaml
forward_listen_port: 8081  # بدلاً من 8080
```

### خطأ: CA certificates not found
```bash
# الحل: توليد شهادات جديدة
python3 main.py --init-ca -c /etc/ngfw/config.yaml
```

---

## 📚 المزيد من التوثيق

- [README.md](README.md) - توثيق شامل
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - ترحيل من النظام القديم
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - ملخص المشروع

---

**جاهز للانطلاق! 🚀**
