import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
    en: {
        translation: {
            "dashboard": "Dashboard",
            "ai_inspection": "AI Inspection Pipeline",
            "vpn_manager": "VPN Manager",
            "qos_traffic": "QoS & Traffic",
            "system_ha": "System & HA",
            "enterprise_ngfw": "Enterprise NGFW",
            "threats_blocked": "Threats Blocked",
            "active_connections": "Active Connections",
            "bandwidth_usage": "Bandwidth Usage",
            "ai_confidence": "AI Confidence Level",
            "system_healthy": "System Healthy",
            "alert": "Alert",
            "recent_events": "Recent Attack Events",
            "live_traffic": "Live Network Traffic",
            "language": "Language / اللغة",
            "toggle_theme": "Toggle Theme",
            "source_ip": "Source IP",
            "destination": "Destination",
            "action": "Action",
            "layer": "AI Layer Triggered",
            "passed": "Passed",
            "blocked": "Blocked",
            "ha_master": "Master Node",
            "ha_backup": "Backup Node"
        }
    },
    ar: {
        translation: {
            "dashboard": "لوحة التحكّم",
            "ai_inspection": "طبقات الذكاء الاصطناعي",
            "vpn_manager": "مدير الـ VPN",
            "qos_traffic": "إدارة السرعات (QoS)",
            "system_ha": "النظام والتوافر العالي",
            "enterprise_ngfw": "جدار الحماية المؤسسي",
            "threats_blocked": "الهجمات المصدودة",
            "active_connections": "الاتصالات النشطة",
            "bandwidth_usage": "استهلاك الباندويث",
            "ai_confidence": "مستوى دقة AI",
            "system_healthy": "النظام مستقر",
            "alert": "إنذار",
            "recent_events": "أحدث أحداث الهجمات",
            "live_traffic": "حركة المرور المباشرة",
            "language": "Language / اللغة",
            "toggle_theme": "تغيير المظهر",
            "source_ip": "المصدر IP",
            "destination": "الوجهة",
            "action": "القرار",
            "layer": "الطبقة المحفزة",
            "passed": "مسموح",
            "blocked": "محظور",
            "ha_master": "الخادم الأساسي",
            "ha_backup": "الخادم الاحتياطي"
        }
    }
};

i18n
    .use(initReactI18next)
    .init({
        resources,
        lng: "ar", // Default language Arabic per user region logic
        fallbackLng: "en",
        interpolation: {
            escapeValue: false
        }
    });

export default i18n;
