# database.py - إدارة قاعدة البيانات لبوت القنوات الدينية

import sqlite3
import json
from datetime import datetime, date
from typing import List, Dict, Optional
from config import DatabaseConfig

class DatabaseManager:
    """مدير قاعدة البيانات للبوت"""
    
    def __init__(self, db_path: str = "islamic_channels.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # لتمكين الوصول بالأسماء
        self.cursor = self.conn.cursor()
        self.init_database()
    
    def init_database(self):
        """تهيئة جميع الجداول"""
        for table_name, create_sql in DatabaseConfig.TABLES.items():
            self.cursor.execute(create_sql)
        self.conn.commit()
    
    # ========== إدارة القنوات ==========
    
    def add_channel(self, channel_id: int, channel_username: str, channel_title: str, 
                    owner_id: int, owner_username: str) -> bool:
        """إضافة قناة جديدة"""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO channels 
                (channel_id, channel_username, channel_title, owner_id, owner_username, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (channel_id, channel_username, channel_title, owner_id, owner_username))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding channel: {e}")
            return False
    
    def get_channel(self, channel_id: int) -> Optional[sqlite3.Row]:
        """الحصول على معلومات القناة"""
        self.cursor.execute('SELECT * FROM channels WHERE channel_id = ?', (channel_id,))
        return self.cursor.fetchone()
    
    def get_user_channels(self, user_id: int) -> List[sqlite3.Row]:
        """الحصول على جميع قنوات المستخدم"""
        self.cursor.execute('SELECT * FROM channels WHERE owner_id = ? AND is_active = 1', (user_id,))
        return self.cursor.fetchall()
    
    def deactivate_channel(self, channel_id: int) -> bool:
        """تعطيل قناة"""
        try:
            self.cursor.execute('UPDATE channels SET is_active = 0 WHERE channel_id = ?', (channel_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error deactivating channel: {e}")
            return False
    
    def update_channel_settings(self, channel_id: int, **kwargs) -> bool:
        """تحديث إعدادات القناة"""
        try:
            set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values()) + [channel_id]
            self.cursor.execute(f'UPDATE channels SET {set_clause} WHERE channel_id = ?', values)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating channel settings: {e}")
            return False
    
    def get_all_active_channels(self) -> List[sqlite3.Row]:
        """الحصول على جميع القنوات النشطة"""
        self.cursor.execute('SELECT * FROM channels WHERE is_active = 1')
        return self.cursor.fetchall()
    
    # ========== إدارة المنشورات ==========
    
    def log_adkar_post(self, channel_id: int, post_type: str, content: str, message_id: int) -> bool:
        """تسجيل منشور أذكار"""
        try:
            self.cursor.execute('''
                INSERT INTO adkar_posts (channel_id, post_type, content, message_id)
                VALUES (?, ?, ?, ?)
            ''', (channel_id, post_type, content, message_id))
            
            # تحديث إحصائيات القناة
            self.cursor.execute('''
                UPDATE channels SET posts_count = posts_count + 1, last_post_time = CURRENT_TIMESTAMP
                WHERE channel_id = ?
            ''', (channel_id,))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error logging adkar post: {e}")
            return False
    
    def log_daily_content(self, channel_id: int, content_type: str, content_text: str, 
                          source: str, message_id: int) -> bool:
        """تسجيل محتوى يومي (آية أو حديث)"""
        try:
            self.cursor.execute('''
                INSERT INTO daily_content (channel_id, content_type, content_text, source, message_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (channel_id, content_type, content_text, source, message_id))
            
            self.cursor.execute('''
                UPDATE channels SET posts_count = posts_count + 1, last_post_time = CURRENT_TIMESTAMP
                WHERE channel_id = ?
            ''', (channel_id,))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error logging daily content: {e}")
            return False
    
    # ========== الإحصائيات ==========
    
    def update_daily_stats(self, channel_id: int, stat_type: str, count: int = 1) -> bool:
        """تحديث الإحصائيات اليومية"""
        try:
            today = date.today().isoformat()
            
            # التحقق من وجود سجل لليوم
            self.cursor.execute('''
                SELECT stat_id FROM statistics 
                WHERE channel_id = ? AND date = ?
            ''', (channel_id, today))
            
            exists = self.cursor.fetchone()
            
            if exists:
                self.cursor.execute(f'''
                    UPDATE statistics SET {stat_type}_count = {stat_type}_count + ?
                    WHERE channel_id = ? AND date = ?
                ''', (count, channel_id, today))
            else:
                self.cursor.execute('''
                    INSERT INTO statistics (channel_id, date, posts_count, adkar_count, tasbih_count, verses_count, hadith_count)
                    VALUES (?, ?, 0, 0, 0, 0, 0)
                ''', (channel_id, today))
                
                self.cursor.execute(f'''
                    UPDATE statistics SET {stat_type}_count = ?
                    WHERE channel_id = ? AND date = ?
                ''', (count, channel_id, today))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating stats: {e}")
            return False
    
    def get_channel_stats(self, channel_id: int, days: int = 7) -> List[sqlite3.Row]:
        """الحصول على إحصائيات القناة لآخر أيام"""
        self.cursor.execute('''
            SELECT * FROM statistics 
            WHERE channel_id = ? 
            ORDER BY date DESC 
            LIMIT ?
        ''', (channel_id, days))
        return self.cursor.fetchall()
    
    def get_total_stats(self, channel_id: int) -> Dict:
        """الحصول على إجمالي الإحصائيات"""
        self.cursor.execute('''
            SELECT 
                SUM(posts_count) as total_posts,
                SUM(adkar_count) as total_adkar,
                SUM(tasbih_count) as total_tasbih,
                SUM(verses_count) as total_verses,
                SUM(hadith_count) as total_hadith
            FROM statistics
            WHERE channel_id = ?
        ''', (channel_id,))
        
        result = self.cursor.fetchone()
        return dict(result) if result else {}
    
    # ========== المهام المجدولة ==========
    
    def schedule_task(self, channel_id: int, task_type: str, scheduled_time: datetime) -> int:
        """جدولة مهمة"""
        try:
            self.cursor.execute('''
                INSERT INTO scheduled_tasks (channel_id, task_type, scheduled_time)
                VALUES (?, ?, ?)
            ''', (channel_id, task_type, scheduled_time.isoformat()))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"Error scheduling task: {e}")
            return -1
    
    def get_pending_tasks(self) -> List[sqlite3.Row]:
        """الحصول على المهام المعلقة"""
        self.cursor.execute('''
            SELECT * FROM scheduled_tasks 
            WHERE is_executed = 0 AND scheduled_time <= CURRENT_TIMESTAMP
            ORDER BY scheduled_time ASC
        ''')
        return self.cursor.fetchall()
    
    def mark_task_executed(self, task_id: int) -> bool:
        """وضع علامة على المهمة كمُنفَّذة"""
        try:
            self.cursor.execute('''
                UPDATE scheduled_tasks 
                SET is_executed = 1, executed_at = CURRENT_TIMESTAMP
                WHERE task_id = ?
            ''', (task_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error marking task executed: {e}")
            return False
    
    # ========== تقارير وتنظيف ==========
    
    def get_channel_report(self, channel_id: int) -> Dict:
        """الحصول على تقرير شامل للقناة"""
        channel_info = self.get_channel(channel_id)
        stats = self.get_total_stats(channel_id)
        
        if not channel_info:
            return {}
        
        return {
            'channel': dict(channel_info),
            'stats': stats,
            'recent_posts': self.get_recent_posts(channel_id, 10)
        }
    
    def get_recent_posts(self, channel_id: int, limit: int = 10) -> List[Dict]:
        """الحصول على آخر المنشورات"""
        self.cursor.execute('''
            SELECT 'adkar' as type, post_type as subtype, content, posted_at 
            FROM adkar_posts WHERE channel_id = ?
            UNION ALL
            SELECT 'daily' as type, content_type as subtype, content_text as content, posted_date as posted_at
            FROM daily_content WHERE channel_id = ?
            ORDER BY posted_at DESC
            LIMIT ?
        ''', (channel_id, channel_id, limit))
        
        return [dict(row) for row in self.cursor.fetchall()]
    
    def cleanup_old_data(self, days: int = 30) -> int:
        """تنظيف البيانات القديمة"""
        try:
            # حذف المنشورات القديمة
            self.cursor.execute('''
                DELETE FROM adkar_posts 
                WHERE posted_at < datetime('now', '-' || ? || ' days')
            ''', (days,))
            
            self.cursor.execute('''
                DELETE FROM daily_content 
                WHERE posted_date < date('now', '-' || ? || ' days')
            ''', (days,))
            
            self.cursor.execute('''
                DELETE FROM statistics 
                WHERE date < date('now', '-' || ? || ' days')
            ''', (days,))
            
            deleted = self.cursor.rowcount
            self.conn.commit()
            return deleted
        except Exception as e:
            print(f"Error cleaning up data: {e}")
            return 0
    
    def close(self):
        """إغلاق الاتصال بقاعدة البيانات"""
        self.conn.close()
