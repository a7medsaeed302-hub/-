# database.py
import sqlite3
import json
from datetime import datetime
import hashlib

class DatabaseManager:
    def __init__(self, db_name="group_protection.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.init_database()
    
    def init_database(self):
        """تهيئة جميع الجداول المتقدمة"""
        
        # جدول المجموعات مع معلومات متقدمة
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY,
                group_title TEXT,
                owner_id INTEGER,
                owner_username TEXT,
                welcome_message TEXT DEFAULT 'أهلاً وسهلاً بك في مجموعتنا! 🌟',
                rules TEXT DEFAULT 'القواعد: احترام الآخرين، عدم السب، المشاركة الإيجابية',
                chat_locked INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_messages INTEGER DEFAULT 0,
                total_members INTEGER DEFAULT 0,
                heart_count INTEGER DEFAULT 0  -- عدد القلوب للمالك
            )
        ''')
        
        # جدول الأعضاء مع إحصائيات متقدمة
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS members (
                member_id INTEGER,
                group_id INTEGER,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_count INTEGER DEFAULT 0,
                warning_count INTEGER DEFAULT 0,
                is_admin INTEGER DEFAULT 0,
                is_muted INTEGER DEFAULT 0,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (member_id, group_id)
            )
        ''')
        
        # جدول المشرفين
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                admin_id INTEGER,
                group_id INTEGER,
                added_by INTEGER,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                permissions TEXT DEFAULT 'all',
                PRIMARY KEY (admin_id, group_id)
            )
        ''')
        
        # جدول العقوبات
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS punishments (
                punishment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER,
                group_id INTEGER,
                punishment_type TEXT,  -- ban, mute, warn, kick
                reason TEXT,
                duration_minutes INTEGER,
                issued_by INTEGER,
                issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # جدول الألعاب والإحصائيات
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                game_type TEXT,
                players TEXT,  -- JSON format
                winner_id INTEGER,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                finished_at TIMESTAMP,
                score INTEGER DEFAULT 0
            )
        ''')
        
        # جدول ردود القلب للمالك
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS heart_reactions (
                reaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                owner_id INTEGER,
                message_id INTEGER,
                reacted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reaction_type TEXT DEFAULT 'heart'
            )
        ''')
        
        # جدول إحصائيات المجموعة
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_stats (
                stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                date DATE DEFAULT CURRENT_DATE,
                messages_count INTEGER DEFAULT 0,
                new_members INTEGER DEFAULT 0,
                warnings_count INTEGER DEFAULT 0,
                bans_count INTEGER DEFAULT 0,
                games_count INTEGER DEFAULT 0
            )
        ''')
        
        self.conn.commit()
    
    def add_heart_to_owner(self, group_id, owner_id, message_id):
        """إضافة قلب لرسالة المالك"""
        self.cursor.execute('''
            INSERT INTO heart_reactions (group_id, owner_id, message_id)
            VALUES (?, ?, ?)
        ''', (group_id, owner_id, message_id))
        
        # تحديث عدد القلوب في جدول المجموعات
        self.cursor.execute('''
            UPDATE groups 
            SET heart_count = heart_count + 1 
            WHERE group_id = ?
        ''', (group_id,))
        
        self.conn.commit()
    
    def get_owner_hearts_count(self, group_id):
        """الحصول على عدد القلوب للمالك"""
        self.cursor.execute('''
            SELECT heart_count FROM groups WHERE group_id = ?
        ''', (group_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 0
    
    def add_new_member(self, group_id, user_id, username, first_name, last_name):
        """إضافة عضو جديد"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO members 
            (member_id, group_id, username, first_name, last_name, join_date)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, group_id, username, first_name, last_name))
        
        # تحديث عدد الأعضاء في المجموعة
        self.cursor.execute('''
            UPDATE groups 
            SET total_members = total_members + 1 
            WHERE group_id = ?
        ''', (group_id,))
        
        self.conn.commit()
    
    def record_message(self, group_id, user_id):
        """تسجيل رسالة جديدة"""
        self.cursor.execute('''
            UPDATE members 
            SET message_count = message_count + 1,
                last_active = CURRENT_TIMESTAMP
            WHERE member_id = ? AND group_id = ?
        ''', (user_id, group_id))
        
        self.cursor.execute('''
            UPDATE groups 
            SET total_messages = total_messages + 1 
            WHERE group_id = ?
        ''', (group_id,))
        
        self.conn.commit()
    
    def get_group_info(self, group_id):
        """الحصول على معلومات المجموعة"""
        self.cursor.execute('''
            SELECT * FROM groups WHERE group_id = ?
        ''', (group_id,))
        return self.cursor.fetchone()
    
    def get_member_stats(self, group_id, user_id):
        """الحصول على إحصائيات العضو"""
        self.cursor.execute('''
            SELECT * FROM members 
            WHERE member_id = ? AND group_id = ?
        ''', (user_id, group_id))
        return self.cursor.fetchone()
