"""
Islamic Channel Guardian - Database Manager
============================================
إدارة قاعدة البيانات SQLite مع نظام التحقق من المحتوى

المبدأ: "لا نؤلف المحتوى الديني، بل نتحقق منه وننشر الموثوق منه"
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from contextlib import contextmanager

from config import bot_config, content_verification


# إعداد السجلات
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """مدير قاعدة البيانات للبوت"""
    
    def __init__(self, db_path: str = None):
        """
        تهيئة مدير قاعدة البيانات
        
        Args:
            db_path: مسار قاعدة البيانات
        """
        self.db_path = db_path or bot_config.DATABASE_PATH
        
        # التأكد من وجود مجلد البيانات
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # إنشاء الجداول
        self._create_tables()
        
        logger.info(f"تم الاتصال بقاعدة البيانات: {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """سياق لإدارة اتصالات قاعدة البيانات بأمان"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"خطأ في قاعدة البيانات: {e}")
            raise
        finally:
            conn.close()
    
    def _create_tables(self):
        """إنشاء جداول قاعدة البيانات"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # جدول القنوات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    username TEXT,
                    owner_id INTEGER NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    publishing_enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول إعدادات القناة
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS channel_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id INTEGER NOT NULL,
                    setting_key TEXT NOT NULL,
                    setting_value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE,
                    UNIQUE(channel_id, setting_key)
                )
            ''')
            
            # جدول سجل النشر
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS publish_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id INTEGER NOT NULL,
                    content_type TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    message_id INTEGER,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE
                )
            ''')
            
            # جدول التدقيق الأمني
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    target_type TEXT,
                    target_id INTEGER,
                    details TEXT,
                    ip_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول المحتوى المعلق للمراجعة
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pending_content (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_type TEXT NOT NULL,
                    content_text TEXT NOT NULL,
                    source TEXT,
                    reference TEXT,
                    submitted_by INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending',
                    reviewed_by INTEGER,
                    review_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TIMESTAMP
                )
            ''')
            
            # جدول حظر المستخدمين المؤقت
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS temp_bans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    reason TEXT,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول حالات الطوارئ
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS emergency_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    is_stopped BOOLEAN DEFAULT 0,
                    stop_reason TEXT,
                    stopped_by INTEGER,
                    stopped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # إدخال حالة الطوارئ الافتراضية
            cursor.execute('''
                INSERT OR IGNORE INTO emergency_status (id, is_stopped) VALUES (1, 0)
            ''')
            
            # إنشاء الفهارس لتحسين الأداء
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_channels_owner 
                ON channels(owner_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_publish_log_channel 
                ON publish_log(channel_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_publish_log_time 
                ON publish_log(published_at)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_audit_log_user 
                ON audit_log(user_id)
            ''')
            
            logger.info("تم إنشاء جداول قاعدة البيانات بنجاح")
    
    # =========================================================================
    # إدارة القنوات
    # =========================================================================
    
    def add_channel(self, chat_id: int, title: str, owner_id: int, 
                    username: str = None) -> bool:
        """
        إضافة قناة جديدة
        
        Args:
            chat_id: معرف القناة
            title: عنوان القناة
            owner_id: معرف المالك
            username: اسم المستخدم للقناة
            
        Returns:
            bool: نجاح العملية
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO channels 
                    (chat_id, title, username, owner_id, is_active, publishing_enabled)
                    VALUES (?, ?, ?, ?, 1, 1)
                ''', (chat_id, title, username, owner_id))
                
                channel_id = cursor.lastrowid
                
                # إضافة الإعدادات الافتراضية
                self._add_default_settings(channel_id)
                
                # تسجيل التدقيق
                self.log_audit(
                    user_id=owner_id,
                    action="ADD_CHANNEL",
                    target_type="channel",
                    target_id=channel_id,
                    details=f"Added channel: {title}"
                )
                
                logger.info(f"تمت إضافة القناة: {title} (ID: {channel_id})")
                return True
                
        except Exception as e:
            logger.error(f"فشل إضافة القناة: {e}")
            return False
    
    def _add_default_settings(self, channel_id: int):
        """إضافة الإعدادات الافتراضية للقناة"""
        
        default_settings = {
            'adkar_morning_enabled': '1',
            'adkar_evening_enabled': '1',
            'verse_daily_enabled': '1',
            'hadith_daily_enabled': '1',
            'dua_random_enabled': '1',
            'tasbih_enabled': '1',
            'istighfar_enabled': '1',
            'adkar_morning_time': '06:00',
            'adkar_evening_time': '18:00',
            'verse_daily_time': '08:00',
            'hadith_daily_time': '12:00',
            'dua_random_time': '15:00',
            'tasbih_interval': '7200',
            'istighfar_interval': '10800',
            'language': 'ar',
            'content_format': 'formatted'
        }
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for key, value in default_settings.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO channel_settings 
                    (channel_id, setting_key, setting_value)
                    VALUES (?, ?, ?)
                ''', (channel_id, key, value))
    
    def get_channel(self, chat_id: int) -> Optional[Dict]:
        """الحصول على معلومات القناة"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM channels WHERE chat_id = ?
            ''', (chat_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_channel_by_id(self, channel_id: int) -> Optional[Dict]:
        """الحصول على معلومات القناة بالمعرف الداخلي"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM channels WHERE id = ?
            ''', (channel_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_channels(self, user_id: int) -> List[Dict]:
        """الحصول على جميع قنوات المستخدم"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM channels WHERE owner_id = ?
            ''', (user_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_active_channels(self) -> List[Dict]:
        """الحصول على جميع القنوات النشطة"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM channels 
                WHERE is_active = 1 AND publishing_enabled = 1
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_channel_status(self, chat_id: int, is_active: bool, 
                             publishing_enabled: bool = None) -> bool:
        """تحديث حالة القناة"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if publishing_enabled is not None:
                    cursor.execute('''
                        UPDATE channels 
                        SET is_active = ?, publishing_enabled = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE chat_id = ?
                    ''', (is_active, publishing_enabled, chat_id))
                else:
                    cursor.execute('''
                        UPDATE channels 
                        SET is_active = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE chat_id = ?
                    ''', (is_active, chat_id))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"فشل تحديث حالة القناة: {e}")
            return False
    
    def delete_channel(self, chat_id: int) -> bool:
        """حذف قناة"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM channels WHERE chat_id = ?', (chat_id,))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"فشل حذف القناة: {e}")
            return False
    
    # =========================================================================
    # إعدادات القناة
    # =========================================================================
    
    def get_channel_setting(self, channel_id: int, key: str) -> Optional[str]:
        """الحصول على إعداد للقناة"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT setting_value FROM channel_settings 
                WHERE channel_id = ? AND setting_key = ?
            ''', (channel_id, key))
            
            row = cursor.fetchone()
            return row['setting_value'] if row else None
    
    def set_channel_setting(self, channel_id: int, key: str, value: str) -> bool:
        """تعيين إعداد للقناة"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO channel_settings 
                    (channel_id, setting_key, setting_value, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (channel_id, key, value))
                
                return True
                
        except Exception as e:
            logger.error(f"فشل تعيين الإعداد: {e}")
            return False
    
    def get_all_channel_settings(self, channel_id: int) -> Dict[str, str]:
        """الحصول على جميع إعدادات القناة"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT setting_key, setting_value FROM channel_settings 
                WHERE channel_id = ?
            ''', (channel_id,))
            
            return {row['setting_key']: row['setting_value'] for row in cursor.fetchall()}
    
    # =========================================================================
    # سجل النشر
    # =========================================================================
    
    def log_publish(self, channel_id: int, content_type: str, content_text: str,
                    message_id: int = None, status: str = 'success',
                    error_message: str = None) -> bool:
        """
        تسجيل عملية نشر
        
        Args:
            channel_id: معرف القناة
            content_type: نوع المحتوى (adkar_morning, verse, hadith, etc.)
            content_text: نص المحتوى
            message_id: معرف الرسالة المنشورة
            status: حالة النشر (success, failed, skipped)
            error_message: رسالة الخطأ إن وجدت
        """
        
        import hashlib
        
        # إنشاء hash فريد للمحتوى لمنع التكرار
        content_hash = hashlib.sha256(content_text.encode()).hexdigest()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO publish_log 
                    (channel_id, content_type, content_hash, message_id, status, error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (channel_id, content_type, content_hash, message_id, status, error_message))
                
                return True
                
        except Exception as e:
            logger.error(f"فشل تسجيل النشر: {e}")
            return False
    
    def get_recent_publishes(self, channel_id: int, limit: int = 50) -> List[Dict]:
        """الحصول على آخر عمليات النشر للقناة"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM publish_log 
                WHERE channel_id = ?
                ORDER BY published_at DESC
                LIMIT ?
            ''', (channel_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def check_content_published_recently(self, channel_id: int, content_text: str,
                                         hours: int = None) -> bool:
        """
        التحقق مما إذا تم نشر هذا المحتوى مؤخراً
        
        Args:
            channel_id: معرف القناة
            content_text: نص المحتوى
            hours: عدد الساعات للتحقق خلالها
            
        Returns:
            bool: True إذا تم نشر المحتوى مؤخراً
        """
        
        import hashlib
        
        if hours is None:
            hours = content_verification.DUPLICATE_PREVENTION_HOURS
        
        content_hash = hashlib.sha256(content_text.encode()).hexdigest()
        time_threshold = datetime.now() - timedelta(hours=hours)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) as count FROM publish_log 
                WHERE channel_id = ? 
                AND content_hash = ?
                AND published_at > ?
                AND status = 'success'
            ''', (channel_id, content_hash, time_threshold))
            
            row = cursor.fetchone()
            return row['count'] > 0
    
    # =========================================================================
    # سجل التدقيق الأمني
    # =========================================================================
    
    def log_audit(self, user_id: int, action: str, target_type: str = None,
                  target_id: int = None, details: str = None,
                  ip_address: str = None) -> bool:
        """تسجيل حدث تدقيق أمني"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO audit_log 
                    (user_id, action, target_type, target_id, details, ip_address)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, action, target_type, target_id, details, ip_address))
                
                return True
                
        except Exception as e:
            logger.error(f"فشل تسجيل التدقيق: {e}")
            return False
    
    def get_audit_logs(self, user_id: int = None, limit: int = 100) -> List[Dict]:
        """الحصول على سجلات التدقيق"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('''
                    SELECT * FROM audit_log 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (user_id, limit))
            else:
                cursor.execute('''
                    SELECT * FROM audit_log 
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # =========================================================================
    # المحتوى المعلق للمراجعة
    # =========================================================================
    
    def submit_pending_content(self, content_type: str, content_text: str,
                               source: str, reference: str,
                               submitted_by: int) -> Optional[int]:
        """
       提交 محتوى للمراجعة
        
        Returns:
            int: معرف المحتوى المعلق أو None عند الفشل
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO pending_content 
                    (content_type, content_text, source, reference, submitted_by, status)
                    VALUES (?, ?, ?, ?, ?, 'pending')
                ''', (content_type, content_text, source, reference, submitted_by))
                
                content_id = cursor.lastrowid
                
                logger.info(f"تم提交 محتوى للمراجعة ID: {content_id}")
                return content_id
                
        except Exception as e:
            logger.error(f"فشل提交 المحتوى للمراجعة: {e}")
            return None
    
    def review_pending_content(self, content_id: int, reviewed_by: int,
                               approved: bool, notes: str = None) -> bool:
        """مراجعة محتوى معلق"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                status = 'approved' if approved else 'rejected'
                
                cursor.execute('''
                    UPDATE pending_content 
                    SET status = ?, reviewed_by = ?, review_notes = ?, 
                        reviewed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, reviewed_by, notes, content_id))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"فشل مراجعة المحتوى: {e}")
            return False
    
    def get_pending_content(self, status: str = 'pending') -> List[Dict]:
        """الحصول على المحتوى المعلق"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM pending_content 
                WHERE status = ?
                ORDER BY created_at ASC
            ''', (status,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # =========================================================================
    # الحظر المؤقت
    # =========================================================================
    
    def add_temp_ban(self, user_id: int, reason: str, 
                     duration_minutes: int) -> bool:
        """إضافة حظر مؤقت"""
        
        expires_at = datetime.now() + timedelta(minutes=duration_minutes)
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO temp_bans (user_id, reason, expires_at)
                    VALUES (?, ?, ?)
                ''', (user_id, reason, expires_at))
                
                return True
                
        except Exception as e:
            logger.error(f"فشل إضافة الحظر المؤقت: {e}")
            return False
    
    def is_user_banned(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        التحقق مما إذا كان المستخدم محظوراً
        
        Returns:
            Tuple[bool, Optional[str]]: (محظور, السبب)
        """
        
        # تنظيف الحظر المنتهي
        self._cleanup_expired_bans()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT reason FROM temp_bans 
                WHERE user_id = ? AND expires_at > ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (user_id, datetime.now()))
            
            row = cursor.fetchone()
            if row:
                return True, row['reason']
            
            return False, None
    
    def _cleanup_expired_bans(self):
        """تنظيف الحظر المنتهي"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM temp_bans WHERE expires_at <= ?
            ''', (datetime.now(),))
    
    # =========================================================================
    # حالة الطوارئ
    # =========================================================================
    
    def set_emergency_stop(self, is_stopped: bool, reason: str = None,
                           stopped_by: int = None) -> bool:
        """تفعيل/تعطيل إيقاف الطوارئ"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if is_stopped:
                    cursor.execute('''
                        UPDATE emergency_status 
                        SET is_stopped = 1, stop_reason = ?, stopped_by = ?,
                            stopped_at = CURRENT_TIMESTAMP
                        WHERE id = 1
                    ''', (reason, stopped_by))
                else:
                    cursor.execute('''
                        UPDATE emergency_status 
                        SET is_stopped = 0, stop_reason = NULL, stopped_by = NULL,
                            stopped_at = NULL
                        WHERE id = 1
                    ''')
                
                return True
                
        except Exception as e:
            logger.error(f"فشل تحديث حالة الطوارئ: {e}")
            return False
    
    def is_emergency_stopped(self) -> Tuple[bool, Optional[str]]:
        """
        التحقق من حالة إيقاف الطوارئ
        
        Returns:
            Tuple[bool, Optional[str]]: (متوقف, السبب)
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT is_stopped, stop_reason FROM emergency_status WHERE id = 1
            ''')
            
            row = cursor.fetchone()
            if row:
                return bool(row['is_stopped']), row['stop_reason']
            
            return False, None
    
    # =========================================================================
    # الإحصائيات
    # =========================================================================
    
    def get_statistics(self, channel_id: int = None) -> Dict:
        """الحصول على إحصائيات"""
        
        stats = {
            'total_channels': 0,
            'active_channels': 0,
            'total_publishes': 0,
            'successful_publishes': 0,
            'failed_publishes': 0,
            'pending_reviews': 0,
            'active_bans': 0
        }
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # إحصائيات القنوات
            cursor.execute('SELECT COUNT(*) as count FROM channels')
            stats['total_channels'] = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM channels WHERE is_active = 1')
            stats['active_channels'] = cursor.fetchone()['count']
            
            # إحصائيات النشر
            if channel_id:
                cursor.execute('SELECT COUNT(*) as count FROM publish_log WHERE channel_id = ?', (channel_id,))
            else:
                cursor.execute('SELECT COUNT(*) as count FROM publish_log')
            stats['total_publishes'] = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM publish_log WHERE status = "success"')
            stats['successful_publishes'] = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM publish_log WHERE status = "failed"')
            stats['failed_publishes'] = cursor.fetchone()['count']
            
            # المحتوى المعلق
            cursor.execute('SELECT COUNT(*) as count FROM pending_content WHERE status = "pending"')
            stats['pending_reviews'] = cursor.fetchone()['count']
            
            # الحظر النشط
            cursor.execute('SELECT COUNT(*) as count FROM temp_bans WHERE expires_at > ?', (datetime.now(),))
            stats['active_bans'] = cursor.fetchone()['count']
        
        return stats
    
    def get_channel_statistics(self, channel_id: int) -> Dict:
        """الحصول على إحصائيات قناة محددة"""
        
        stats = {
            'total_publishes': 0,
            'publishes_by_type': {},
            'recent_activity': []
        }
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # إجمالي النشر
            cursor.execute('''
                SELECT COUNT(*) as count FROM publish_log WHERE channel_id = ?
            ''', (channel_id,))
            stats['total_publishes'] = cursor.fetchone()['count']
            
            # النشر حسب النوع
            cursor.execute('''
                SELECT content_type, COUNT(*) as count 
                FROM publish_log 
                WHERE channel_id = ?
                GROUP BY content_type
            ''', (channel_id,))
            
            for row in cursor.fetchall():
                stats['publishes_by_type'][row['content_type']] = row['count']
            
            # النشاط الأخير
            cursor.execute('''
                SELECT * FROM publish_log 
                WHERE channel_id = ?
                ORDER BY published_at DESC
                LIMIT 10
            ''', (channel_id,))
            
            stats['recent_activity'] = [dict(row) for row in cursor.fetchall()]
        
        return stats
