# config.py - إعدادات متقدمة لحماية الحسابات

import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class SecurityConfig:
    # التوكن الأساسي للبوت
    BOT_TOKEN = os.getenv("BOT_TOKEN", "8631971512:AAHyuDK3Sr9tn14CTBfzDVWbamxfAZdcs7c")
    
    # إعدادات الأمان المتقدمة
    ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
    
    # حدود الحماية التلقائية
    MAX_FAILED_LOGINS = 3                    # الحد الأقصى لمحاولات تسجيل دخول فاشلة
    MAX_SUSPICIOUS_REQUESTS = 10             # الحد الأقصى للطلبات المشبوهة في الدقيقة
    
    # الفترات الزمنية للحماية
    LOGIN_COOLDOWN_MINUTES = 15              # وقت التبريد بعد محاولات فاشلة
    SESSION_TIMEOUT_HOURS = 24               # انتهاء صلاحية الجلسة
    
    # إعدادات المراقبة المتقدمة
    MONITOR_NEW_LOGINS = True               # مراقبة تسجيلات الدخول الجديدة
    MONITOR_LOCATION_CHANGES = True         # مراقبة تغييرات الموقع الجغرافي
    
    # قوائم الحماية المتقدمة
    BLOCKED_COUNTRIES = ["CN", "RU", "KP"]   # دول محظورة افتراضياً
    
    # إعدادات التشفير المتقدمة
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "your-secure-key-here")
    
    # إعدادات التنبيهات المتعددة القنوات
    ALERT_CHANNELS = {
        "telegram": True,
        "email": False,
        "sms": False,
        "webhook": False
    }
    
    # مستويات التهديد وتصنيفاتها
    THREAT_LEVELS = {
        1: {"name": "منخفض", "color": "🟢", "action": "تسجيل فقط"},
        2: {"name": "متوسط", "color": "🟡", "action": "تنبيه فوري"},
        3: {"name": "مرتفع", "color": "🟠", "action": "إجراء فوري"},
        4: {"name": "حرج", "color": "🔴", "action": "حظر تلقائي"}
    }

class DatabaseConfig:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///accounts_protection.db")
    
    # إعدادات النسخ الاحتياطي التلقائي
    BACKUP_ENABLED = True
    BACKUP_INTERVAL_HOURS = 6
    
    # إعدادات الأداء والتخزين المؤقت
    CACHE_TTL_SECONDS = 300                  # 5 دقائق للتخزين المؤقت

class MonitoringConfig:
    # إعدادات المراقبة في الوقت الحقيقي
    REALTIME_MONITORING = True
    
    # الفحص الدوري للأنشطة المشبوهة (بالدقائق)
    PERIODIC_SCAN_INTERVAL = 5
    
    # إعدادات الذكاء الاصطناعي للكشف عن السلوك المشبوه
    AI_DETECTION_ENABLED = True
    
    # نقاط الخطر لكل نوع نشاط مشبوه
    RISK_POINTS = {
        "new_device": 10,
        "new_location": 15,
        "multiple_failed_logins": 20,
        "suspicious_ip": 25,
        "password_change": 5,
        "2fa_bypass_attempt": 30,
        "2fa_failure": 10,
        "2fa_success": -5
    }
