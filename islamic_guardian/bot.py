"""
Islamic Channel Guardian - Main Bot
====================================
بوت تليجرام الاحترافي لإدارة القنوات الدينية

المبدأ الأساسي: "لا نؤلف المحتوى الديني، بل نتحقق منه وننشر الموثوق منه"
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime, time
from typing import Optional, List, Dict
from pathlib import Path

# إعداد مسار المشروع
sys.path.insert(0, str(Path(__file__).parent))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)

from config import (
    bot_config, default_schedule, content_verification, 
    security_config, VERIFIED_CONTENT
)
from database import DatabaseManager
from content_verifier import ContentVerifier, VerificationStatus


# =============================================================================
# إعداد السجلات
# =============================================================================

# إنشاء مجلدات السجلات
Path(bot_config.AUDIT_LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
Path(bot_config.ERROR_LOG_PATH).parent.mkdir(parents=True, exist_ok=True)

# تكوين السجلات
logging.basicConfig(
    level=logging.INFO if not bot_config.DEBUG_MODE else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(bot_config.ERROR_LOG_PATH, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# =============================================================================
# فئة البوت الرئيسية
# =============================================================================

class IslamicGuardianBot:
    """
    بوت الحارس الإسلامي - مدير القنوات الدينية
    
    المميزات:
    - نشر تلقائي للمحتوى الديني الموثق
    - نظام تحقق صارم من المحتوى
    - إدارة متعددة القنوات
    - لوحة تحكم شاملة
    - إيقاف طوارئ
    """
    
    def __init__(self):
        """تهيئة البوت"""
        
        # تهيئة مكونات البوت
        self.db = DatabaseManager()
        self.verifier = ContentVerifier(self.db)
        
        # حالة البوت
        self.is_running = True
        self.scheduler_tasks = []
        
        # تطبيق تليجرام
        self.application = None
        
        logger.info("تم تهيئة بوت الحارس الإسلامي")
    
    def create_application(self) -> Application:
        """إنشاء تطبيق تليجرام"""
        
        if not bot_config.BOT_TOKEN:
            logger.error("لم يتم العثور على توكن البوت!")
            raise ValueError("BOT_TOKEN غير موجود في المتغيرات البيئية")
        
        application = Application.builder().token(bot_config.BOT_TOKEN).build()
        
        # تسجيل المعالجات
        self._register_handlers(application)
        
        logger.info("تم إنشاء تطبيق تليجرام بنجاح")
        return application
    
    def _register_handlers(self, application: Application):
        """تسجيل معالجات الأوامر"""
        
        # أوامر المستخدمين
        application.add_handler(CommandHandler("start", self.cmd_start))
        application.add_handler(CommandHandler("help", self.cmd_help))
        application.add_handler(CommandHandler("my_channels", self.cmd_my_channels))
        application.add_handler(CommandHandler("add_channel", self.cmd_add_channel))
        application.add_handler(CommandHandler("channel_settings", self.cmd_channel_settings))
        application.add_handler(CommandHandler("publish_now", self.cmd_publish_now))
        application.add_handler(CommandHandler("stats", self.cmd_stats))
        application.add_handler(CommandHandler("emergency_stop", self.cmd_emergency_stop))
        application.add_handler(CommandHandler("resume", self.cmd_resume))
        
        # أوامر المطورين
        if bot_config.ADMIN_IDS:
            application.add_handler(CommandHandler("review", self.cmd_review))
            application.add_handler(CommandHandler("audit", self.cmd_audit))
        
        # معالج الاستفسارات
        application.add_handler(CallbackQueryHandler(self.callback_handler))
        
        logger.info("تم تسجيل معالجات الأوامر")
    
    # =========================================================================
    # أوامر البوت الرئيسية
    # =========================================================================
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /start - رسالة الترحيب"""
        
        user = update.effective_user
        user_id = user.id if user else 0
        
        # التحقق من الحظر
        is_banned, ban_reason = self.db.is_user_banned(user_id)
        if is_banned:
            await update.message.reply_text(
                f"❌ أنت محظور من استخدام البوت\nالسبب: {ban_reason}"
            )
            return
        
        # نص الترحيب
        welcome_text = """
🕌 *أهلاً بك في بوت الحارس الإسلامي* 🕌

بوت احترافي لإدارة القنوات الدينية ونشر المحتوى الإسلامي الموثق تلقائياً.

✨ *مميزات البوت:*
• 📿 أذكار الصباح والمساء التلقائية
• 📖 آيات قرآنية يومية
• 🕌 أحاديث نبوية صحيحة
• 🤲 أدعية مأثورة
• 📿 تسبيحات واستغفار
• 🛡️ نظام تحقق صارم من المحتوى
• 📊 إحصائيات مفصلة
• 🚨 إيقاف طوارئ فوري

⚠️ *هام:* جميع المحتويات موثقة من مصادر معتمدة فقط.

📋 *للبدء:*
1. أضف البوت كمشرف في قناتك
2. استخدم /add_channel لإضافة القناة
3. اضبط الإعدادات حسب رغبتك
4. استمتع بالنشر التلقائي!

💡 استخدم /help لعرض جميع الأوامر
"""
        
        keyboard = [
            [InlineKeyboardButton("📋 دليل الاستخدام", callback_data="help_guide")],
            [InlineKeyboardButton("➕ إضافة قناة", callback_data="add_channel_btn")],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="view_stats")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        # تسجيل التدقيق
        self.db.log_audit(
            user_id=user_id,
            action="START",
            details=f"User started the bot"
        )
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /help - دليل الاستخدام"""
        
        help_text = """
📚 *دليل استخدام بوت الحارس الإسلامي*

━━━━━━━━━━━━━━━━━━━━

🎯 *الأوامر الأساسية:*

/start - رسالة الترحيب
/help - هذا الدليل
/my_channels - عرض قنواتك
/add_channel - إضافة قناة جديدة
/channel_settings - إعدادات القناة
/stats - الإحصائيات

━━━━━━━━━━━━━━━━━━━━

📢 *أوامر النشر اليدوي:*

/publish_now adkar_morning - نشر أذكار الصباح
/publish_now adkar_evening - نشر أذكار المساء
/publish_now verse - نشر آية قرآنية
/publish_now hadith - نشر حديث شريف
/publish_now dua - نشر دعاء
/publish_now tasbih - نشر تسبيحة
/publish_now istighfar - نشر استغفار

━━━━━━━━━━━━━━━━━━━━

🛡️ *أوامر الأمان:*

/emergency_stop - إيقاف النشر فوراً
/resume - استئناف النشر

━━━━━━━━━━━━━━━━━━━━

⚙️ *إعدادات القناة:*

بعد إضافة القناة، يمكنك التحكم في:
• تفعيل/تعطيل كل نوع محتوى
• تغيير أوقات النشر
• تخصيص الفترات الزمنية

━━━━━━━━━━━━━━━━━━━━

💡 *نصائح مهمة:*

1. يجب إضافة البوت كـ **مشرف** في القناة
2. البوت ينشر فقط المحتوى الموثق
3. يمكن إيقاف النشر في أي وقت
4. جميع العمليات مسجلة في سجل التدقيق

📞 للدعم والتواصل مع المطور
"""
        
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown'
        )
    
    async def cmd_my_channels(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /my_channels - عرض قنوات المستخدم"""
        
        user_id = update.effective_user.id
        channels = self.db.get_user_channels(user_id)
        
        if not channels:
            await update.message.reply_text(
                "📭 ليس لديك قنوات مضافة حالياً.\n\n"
                "استخدم /add_channel لإضافة قناة جديدة."
            )
            return
        
        text = f"📡 *قنواتك ({len(channels)})*\n\n"
        
        for i, channel in enumerate(channels, 1):
            status_icon = "✅" if channel['is_active'] else "❌"
            pub_icon = "🟢" if channel['publishing_enabled'] else "🔴"
            
            text += f"{i}. {status_icon} {channel['title']}\n"
            text += f"   ID: `{channel['chat_id']}`\n"
            text += f"   النشر: {pub_icon}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("⚙️ إعدادات قناة", callback_data="settings_select")]
        ]
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def cmd_add_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /add_channel - إضافة قناة جديدة"""
        
        user_id = update.effective_user.id
        
        # التحقق من وجود وسيطة (معرف القناة)
        if context.args:
            try:
                chat_id = int(context.args[0])
                
                # الحصول على معلومات القناة من تليجرام
                try:
                    chat = await context.bot.get_chat(chat_id)
                    
                    # التحقق من أن البوت مشرف في القناة
                    member = await context.bot.get_chat_member(chat_id, user_id)
                    if member.status not in ['creator', 'administrator']:
                        await update.message.reply_text(
                            "❌ يجب أن تكون مالكاً أو مشرفاً في القناة لإضافتها."
                        )
                        return
                    
                    # إضافة القناة
                    success = self.db.add_channel(
                        chat_id=chat_id,
                        title=chat.title,
                        owner_id=user_id,
                        username=chat.username
                    )
                    
                    if success:
                        await update.message.reply_text(
                            f"✅ تم إضافة القناة بنجاح!\n\n"
                            f"📡 الاسم: {chat.title}\n"
                            f"🆔 المعرف: `{chat_id}`\n\n"
                            f"استخدم /channel_settings لتخصيص الإعدادات."
                        )
                        
                        # تسجيل التدقيق
                        self.db.log_audit(
                            user_id=user_id,
                            action="ADD_CHANNEL",
                            target_type="channel",
                            target_id=chat_id,
                            details=f"Added channel: {chat.title}"
                        )
                    else:
                        await update.message.reply_text(
                            "❌ فشل إضافة القناة. حاول مرة أخرى."
                        )
                    
                except Exception as e:
                    await update.message.reply_text(
                        f"❌ خطأ في الوصول للقناة: {str(e)}\n\n"
                        "تأكد من إضافة البوت كمشرف في القناة أولاً."
                    )
                
            except ValueError:
                await update.message.reply_text(
                    "❌ معرف القناة يجب أن يكون رقماً.\n\n"
                    "مثال: /add_channel -1001234567890"
                )
        else:
            await update.message.reply_text(
                "📝 لإضافة قناة:\n\n"
                "1. أضف البوت كـ **مشرف** في القناة\n"
                "2. احصل على معرف القناة (Channel ID)\n"
                "3. أرسل الأمر: `/add_channel <channel_id>`\n\n"
                "💡 مثال: `/add_channel -1001234567890`\n\n"
                "يمكنك استخدام @RawDataBot لمعرفة معرف القناة."
            )
    
    async def cmd_channel_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /channel_settings - إعدادات القناة"""
        
        user_id = update.effective_user.id
        channels = self.db.get_user_channels(user_id)
        
        if not channels:
            await update.message.reply_text(
                "ليس لديك قنوات مضافة.\nاستخدم /add_channel أولاً."
            )
            return
        
        # بناء لوحة المفاتيح
        keyboard = []
        for channel in channels:
            status = "🟢" if channel['is_active'] else "🔴"
            keyboard.append([
                InlineKeyboardButton(
                    f"{status} {channel['title']}",
                    callback_data=f"channel_config_{channel['id']}"
                )
            ])
        
        await update.message.reply_text(
            "⚙️ اختر القناة لإعداداتها:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def cmd_publish_now(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /publish_now - نشر يدوي فوري"""
        
        user_id = update.effective_user.id
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "📝 الاستخدام:\n"
                "`/publish_now <channel_id> <content_type>`\n\n"
                "أنواع المحتوى المتاحة:\n"
                "• adkar_morning - أذكار الصباح\n"
                "• adkar_evening - أذكار المساء\n"
                "• verse - آية قرآنية\n"
                "• hadith - حديث شريف\n"
                "• dua - دعاء\n"
                "• tasbih - تسبيحة\n"
                "• istighfar - استغفار",
                parse_mode='Markdown'
            )
            return
        
        try:
            chat_id = int(context.args[0])
            content_type = context.args[1]
            
            # التحقق من ملكية القناة
            channel = self.db.get_channel(chat_id)
            if not channel or channel['owner_id'] != user_id:
                await update.message.reply_text(
                    "❌ هذه القناة لا تخصك أو غير موجودة."
                )
                return
            
            # التحقق من نوع المحتوى
            valid_types = list(VERIFIED_CONTENT.keys())
            if content_type not in valid_types:
                await update.message.reply_text(
                    f"❌ نوع المحتوى غير صالح.\n"
                    f"الأنواع المتاحة: {', '.join(valid_types)}"
                )
                return
            
            # النشر الفوري
            result = await self.publish_content(
                context=context,
                channel_id=channel['id'],
                chat_id=chat_id,
                content_type=content_type,
                manual=True
            )
            
            if result:
                await update.message.reply_text("✅ تم النشر بنجاح!")
            else:
                await update.message.reply_text("❌ فشل النشر.")
        
        except ValueError:
            await update.message.reply_text("❌ معرف القناة يجب أن يكون رقماً.")
        except Exception as e:
            logger.error(f"خطأ في النشر اليدوي: {e}")
            await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
    
    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /stats - الإحصائيات"""
        
        stats = self.db.get_statistics()
        
        text = f"""
📊 *إحصائيات بوت الحارس الإسلامي*

🕌 القنوات:
• الإجمالي: {stats['total_channels']}
• النشطة: {stats['active_channels']}

📝 النشر:
• الإجمالي: {stats['total_publishes']}
• الناجح: {stats['successful_publishes']}
• الفاشل: {stats['failed_publishes']}

🔒 الأمان:
• قيد المراجعة: {stats['pending_reviews']}
• المحظورون: {stats['active_bans']}

━━━━━━━━━━━━━━━━━━━━
🕐 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث", callback_data="refresh_stats")]
        ]
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def cmd_emergency_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /emergency_stop - إيقاف الطوارئ"""
        
        user_id = update.effective_user.id
        channels = self.db.get_user_channels(user_id)
        
        if not channels:
            await update.message.reply_text("ليس لديك قنوات.")
            return
        
        # بناء لوحة التأكيد
        keyboard = []
        for channel in channels:
            keyboard.append([
                InlineKeyboardButton(
                    f"🛑 {channel['title']}",
                    callback_data=f"emergency_stop_{channel['id']}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("🛑 إيقاف الكل", callback_data="emergency_stop_all")
        ])
        
        await update.message.reply_text(
            "⚠️ *تحذير: إيقاف الطوارئ*\n\n"
            "سيتم إيقاف جميع عمليات النشر فوراً.\n"
            "اختر القناة المراد إيقافها:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def cmd_resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /resume - استئناف النشر"""
        
        user_id = update.effective_user.id
        channels = self.db.get_user_channels(user_id)
        
        if not channels:
            await update.message.reply_text("ليس لديك قنوات.")
            return
        
        keyboard = []
        for channel in channels:
            if not channel['publishing_enabled']:
                keyboard.append([
                    InlineKeyboardButton(
                        f"▶️ {channel['title']}",
                        callback_data=f"resume_channel_{channel['id']}"
                    )
                ])
        
        if not keyboard:
            await update.message.reply_text("✅ جميع القنوات تعمل بالفعل.")
            return
        
        keyboard.append([
            InlineKeyboardButton("▶️ استئناف الكل", callback_data="resume_all")
        ])
        
        await update.message.reply_text(
            "▶️ اختر القناة لاستئناف النشر:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def cmd_review(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /review - مراجعة المحتوى المعلق (للمطورين)"""
        
        user_id = update.effective_user.id
        
        if user_id not in bot_config.ADMIN_IDS:
            await update.message.reply_text("❌ هذا الأمر للمطورين فقط.")
            return
        
        pending = self.db.get_pending_content('pending')
        
        if not pending:
            await update.message.reply_text("✅ لا يوجد محتوى قيد المراجعة.")
            return
        
        # عرض أول محتوى معلق
        item = pending[0]
        text = f"""
📝 *مراجعة محتوى جديد*

النوع: {item['content_type']}
المقدم: {item['submitted_by']}
التاريخ: {item['created_at']}

📄 المحتوى:
{item['content_text']}

📚 المصدر: {item.get('source', 'غير محدد')}
📖 المرجع: {item.get('reference', 'غير محدد')}
"""
        
        keyboard = [
            [
                InlineKeyboardButton("✅ موافق", callback_data=f"approve_{item['id']}"),
                InlineKeyboardButton("❌ مرفوض", callback_data=f"reject_{item['id']}")
            ]
        ]
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def cmd_audit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /audit - عرض سجل التدقيق (للمطورين)"""
        
        user_id = update.effective_user.id
        
        if user_id not in bot_config.ADMIN_IDS:
            await update.message.reply_text("❌ هذا الأمر للمطورين فقط.")
            return
        
        logs = self.db.get_audit_logs(limit=20)
        
        text = "📋 *سجل التدقيق الأخير*\n\n"
        for log in logs:
            text += f"• {log['action']} - User: {log['user_id']}\n"
            text += f"  الوقت: {log['created_at']}\n\n"
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown'
        )
    
    # =========================================================================
    # معالج الاستفسارات (Callback Queries)
    # =========================================================================
    
    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الاستفسارات من الأزرار"""
        
        query = update.callback_query
        data = query.data
        user_id = query.from_user.id
        
        await query.answer()
        
        # معالجة مختلفة حسب نوع البيانات
        if data == "help_guide":
            await self.cmd_help(update, context)
        
        elif data == "add_channel_btn":
            await update.message.reply_text(
                "➕ لإضافة قناة:\n"
                "1. أضف البوت كمشرف في القناة\n"
                "2. احصل على Channel ID\n"
                "3. استخدم: /add_channel <channel_id>"
            )
        
        elif data == "view_stats":
            await self.cmd_stats(update, context)
        
        elif data == "refresh_stats":
            await self.cmd_stats(update, context)
        
        elif data.startswith("emergency_stop_"):
            await self.handle_emergency_stop(query, context, data, user_id)
        
        elif data.startswith("resume_channel_"):
            await self.handle_resume(query, context, data, user_id)
        
        elif data.startswith("channel_config_"):
            await self.handle_channel_config(query, context, data, user_id)
        
        elif data.startswith("approve_") or data.startswith("reject_"):
            await self.handle_content_review(query, context, data, user_id)
    
    async def handle_emergency_stop(self, query, context, data: str, user_id: int):
        """معالجة إيقاف الطوارئ"""
        
        channel_id = data.replace("emergency_stop_", "")
        
        if channel_id == "all":
            # إيقاف جميع قنوات المستخدم
            channels = self.db.get_user_channels(user_id)
            count = 0
            for ch in channels:
                if self.db.update_channel_status(ch['chat_id'], True, False):
                    count += 1
            await query.edit_message_text(f"✅ تم إيقاف {count} قنوات.")
        else:
            # إيقاف قناة محددة
            channel = self.db.get_channel_by_id(int(channel_id))
            if channel and channel['owner_id'] == user_id:
                self.db.update_channel_status(channel['chat_id'], True, False)
                await query.edit_message_text(f"✅ تم إيقاف القناة: {channel['title']}")
                
                # تسجيل التدقيق
                self.db.log_audit(
                    user_id=user_id,
                    action="EMERGENCY_STOP",
                    target_type="channel",
                    target_id=int(channel_id)
                )
    
    async def handle_resume(self, query, context, data: str, user_id: int):
        """معالجة استئناف النشر"""
        
        channel_id = data.replace("resume_channel_", "")
        
        if channel_id == "all":
            channels = self.db.get_user_channels(user_id)
            count = 0
            for ch in channels:
                if self.db.update_channel_status(ch['chat_id'], True, True):
                    count += 1
            await query.edit_message_text(f"✅ تم استئناف {count} قنوات.")
        else:
            channel = self.db.get_channel_by_id(int(channel_id))
            if channel and channel['owner_id'] == user_id:
                self.db.update_channel_status(channel['chat_id'], True, True)
                await query.edit_message_text(f"✅ تم استئناف القناة: {channel['title']}")
    
    async def handle_channel_config(self, query, context, data: str, user_id: int):
        """معالجة إعدادات القناة"""
        
        channel_id = int(data.replace("channel_config_", ""))
        channel = self.db.get_channel_by_id(channel_id)
        
        if not channel or channel['owner_id'] != user_id:
            await query.edit_message_text("❌ وصول مرفوض.")
            return
        
        settings = self.db.get_all_channel_settings(channel_id)
        
        # بناء لوحة الإعدادات
        keyboard = [
            [
                InlineKeyboardButton(
                    "🌅 أذكار الصباح " + ("✅" if settings.get('adkar_morning_enabled') == '1' else "❌"),
                    callback_data=f"toggle_adkar_morning_{channel_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🌙 أذكار المساء " + ("✅" if settings.get('adkar_evening_enabled') == '1' else "❌"),
                    callback_data=f"toggle_adkar_evening_{channel_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "📖 آية يومية " + ("✅" if settings.get('verse_daily_enabled') == '1' else "❌"),
                    callback_data=f"toggle_verse_{channel_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🕌 حديث يومي " + ("✅" if settings.get('hadith_daily_enabled') == '1' else "❌"),
                    callback_data=f"toggle_hadith_{channel_id}"
                )
            ],
            [
                InlineKeyboardButton("🔙 رجوع", callback_data="my_channels_back")
            ]
        ]
        
        text = f"""
⚙️ *إعدادات القناة: {channel['title']}*

حالة النشر: {'🟢 نشط' if channel['publishing_enabled'] else '🔴 متوقف'}

اختر نوع المحتوى للتفعيل/التعطيل:
"""
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def handle_content_review(self, query, context, data: str, user_id: int):
        """معالجة مراجعة المحتوى"""
        
        if user_id not in bot_config.ADMIN_IDS:
            await query.answer("❌ وصول مرفوض", show_alert=True)
            return
        
        parts = data.split("_")
        action = parts[0]
        content_id = int(parts[1])
        
        approved = action == "approve"
        self.db.review_pending_content(
            content_id=content_id,
            reviewed_by=user_id,
            approved=approved,
            notes="تمت المراجعة عبر البوت"
        )
        
        await query.edit_message_text(
            f"{'✅ تمت الموافقة' if approved else '❌ تم الرفض'} على المحتوى."
        )
    
    # =========================================================================
    # وظائف النشر
    # =========================================================================
    
    async def publish_content(self, context: ContextTypes.DEFAULT_TYPE,
                             channel_id: int, chat_id: int,
                             content_type: str, manual: bool = False) -> bool:
        """
        نشر محتوى في قناة
        
        Args:
            context: سياق البوت
            channel_id: معرف القناة الداخلي
            chat_id: معرف القناة في تليجرام
            content_type: نوع المحتوى
            manual: هل هو نشر يدوي
            
        Returns:
            bool: نجاح النشر
        """
        
        # التحقق من حالة الطوارئ
        is_stopped, stop_reason = self.db.is_emergency_stopped()
        if is_stopped:
            logger.warning(f"النشر متوقف طوارئ: {stop_reason}")
            return False
        
        # التحقق من حالة القناة
        channel = self.db.get_channel_by_id(channel_id)
        if not channel or not channel['publishing_enabled']:
            logger.warning(f"القناة {channel_id} غير مفعلة للنشر")
            return False
        
        # الحصول على المحتوى الموثق
        content = self.verifier.get_verified_content(content_type)
        if not content:
            logger.error(f"لا يوجد محتوى متاح من نوع: {content_type}")
            return False
        
        # التحقق الشامل من المحتوى
        verification = self.verifier.verify_content(
            content_type=content_type,
            content_data=content,
            channel_id=channel_id
        )
        
        if verification.status != VerificationStatus.VERIFIED:
            logger.warning(f"فشل التحقق من المحتوى: {verification.message}")
            
            # تسجيل الفشل
            self.db.log_publish(
                channel_id=channel_id,
                content_type=content_type,
                content_text=content.get('text', ''),
                status='skipped',
                error_message=verification.message
            )
            
            return False
        
        # تنسيق الرسالة
        message_text = self.format_message(content_type, content)
        
        # إرسال الرسالة
        try:
            message = await context.bot.send_message(
                chat_id=chat_id,
                text=message_text,
                parse_mode='HTML'
            )
            
            # تسجيل النجاح
            self.db.log_publish(
                channel_id=channel_id,
                content_type=content_type,
                content_text=content.get('text', ''),
                message_id=message.message_id,
                status='success'
            )
            
            logger.info(f"تم نشر {content_type} في القناة {channel_id}")
            return True
            
        except Exception as e:
            logger.error(f"فشل النشر في القناة {channel_id}: {e}")
            
            self.db.log_publish(
                channel_id=channel_id,
                content_type=content_type,
                content_text=content.get('text', ''),
                status='failed',
                error_message=str(e)
            )
            
            return False
    
    def format_message(self, content_type: str, content: Dict) -> str:
        """تنسيق رسالة النشر"""
        
        text = content.get('text', '')
        
        if content_type == 'verse':
            surah = content.get('surah', '')
            verse_num = content.get('verse_number', '')
            return f"""
📖 *آية من القرآن الكريم*

{text}

📜 سورة {surah}، الآية {verse_num}

صدق الله العظيم
            """
        
        elif content_type == 'hadith':
            narrator = content.get('narrator', '')
            source = content.get('source', '')
            reference = content.get('reference', '')
            grade = content.get('grade', '')
            
            return f"""
🕌 *حديث شريف*

{text}

📖 {narrator}
📚 {source}
🔖 {reference}
✅ {grade}
            """
        
        elif content_type in ['adkar_morning', 'adkar_evening']:
            source = content.get('source', '')
            reference = content.get('reference', '')
            count = content.get('count', 1)
            
            title = "🌅 أذكار الصباح" if content_type == 'adkar_morning' else "🌙 أذكار المساء"
            
            return f"""
{title}

{text}

📚 {source}
🔖 {reference}
🔢 العدد: {count}
            """
        
        elif content_type == 'dua':
            source = content.get('source', '')
            reference = content.get('reference', '')
            category = content.get('category', '')
            
            return f"""
🤲 *دعاء مأثور*

{text}

🏷️ {category}
📚 {source}
🔖 {reference}
            """
        
        elif content_type == 'tasbih':
            text = content.get('text', '')
            count = content.get('count', 33)
            virtue = content.get('virtue', '')
            source = content.get('source', '')
            
            return f"""
📿 *تسبيحة*

{text}

🔢 {count} مرة
✨ {virtue}
📚 {source}
            """
        
        elif content_type == 'istighfar':
            text = content.get('text', '')
            count = content.get('count', 100)
            source = content.get('source', '')
            reference = content.get('reference', '')
            
            return f"""
🤍 *استغفار*

{text}

🔢 {count} مرة
📚 {source}
🔖 {reference}
            """
        
        return text
    
    # =========================================================================
    # الجدولة التلقائية
    # =========================================================================
    
    async def start_scheduler(self, context: ContextTypes.DEFAULT_TYPE):
        """بدء الجدولة التلقائية للنشر"""
        
        logger.info("بدء الجدولة التلقائية")
        
        # تشغيل مهام الجدولة في الخلفية
        self.scheduler_tasks = [
            asyncio.create_task(self.schedule_adkar_morning(context)),
            asyncio.create_task(self.schedule_adkar_evening(context)),
            asyncio.create_task(self.schedule_verse_daily(context)),
            asyncio.create_task(self.schedule_hadith_daily(context)),
            asyncio.create_task(self.schedule_tasbih(context)),
            asyncio.create_task(self.schedule_istighfar(context))
        ]
        
        logger.info("تم بدء جميع مهام الجدولة")
    
    async def schedule_adkar_morning(self, context: ContextTypes.DEFAULT_TYPE):
        """جدولة أذكار الصباح (6:00 صباحاً)"""
        
        while self.is_running:
            now = datetime.now()
            target_time = now.replace(
                hour=default_schedule.ADKAR_MORNING.hour,
                minute=default_schedule.ADKAR_MORNING.minute,
                second=0,
                microsecond=0
            )
            
            if now >= target_time:
                target_time = target_time.replace(day=target_time.day + 1)
            
            wait_seconds = (target_time - now).total_seconds()
            logger.info(f"انتظار أذكار الصباح: {wait_seconds} ثانية")
            
            await asyncio.sleep(wait_seconds)
            
            if not self.is_running:
                break
            
            # النشر في جميع القنوات النشطة
            channels = self.db.get_all_active_channels()
            for channel in channels:
                settings = self.db.get_all_channel_settings(channel['id'])
                if settings.get('adkar_morning_enabled') == '1':
                    await self.publish_content(
                        context=context,
                        channel_id=channel['id'],
                        chat_id=channel['chat_id'],
                        content_type='adkar_morning'
                    )
    
    async def schedule_adkar_evening(self, context: ContextTypes.DEFAULT_TYPE):
        """جدولة أذكار المساء (6:00 مساءً)"""
        
        while self.is_running:
            now = datetime.now()
            target_time = now.replace(
                hour=default_schedule.ADKAR_EVENING.hour,
                minute=default_schedule.ADKAR_EVENING.minute,
                second=0,
                microsecond=0
            )
            
            if now >= target_time:
                target_time = target_time.replace(day=target_time.day + 1)
            
            wait_seconds = (target_time - now).total_seconds()
            logger.info(f"انتظار أذكار المساء: {wait_seconds} ثانية")
            
            await asyncio.sleep(wait_seconds)
            
            if not self.is_running:
                break
            
            channels = self.db.get_all_active_channels()
            for channel in channels:
                settings = self.db.get_all_channel_settings(channel['id'])
                if settings.get('adkar_evening_enabled') == '1':
                    await self.publish_content(
                        context=context,
                        channel_id=channel['id'],
                        chat_id=channel['chat_id'],
                        content_type='adkar_evening'
                    )
    
    async def schedule_verse_daily(self, context: ContextTypes.DEFAULT_TYPE):
        """جدولة الآية اليومية (8:00 صباحاً)"""
        
        while self.is_running:
            now = datetime.now()
            target_time = now.replace(
                hour=default_schedule.VERSE_DAILY.hour,
                minute=default_schedule.VERSE_DAILY.minute,
                second=0,
                microsecond=0
            )
            
            if now >= target_time:
                target_time = target_time.replace(day=target_time.day + 1)
            
            wait_seconds = (target_time - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            
            if not self.is_running:
                break
            
            channels = self.db.get_all_active_channels()
            for channel in channels:
                settings = self.db.get_all_channel_settings(channel['id'])
                if settings.get('verse_daily_enabled') == '1':
                    await self.publish_content(
                        context=context,
                        channel_id=channel['id'],
                        chat_id=channel['chat_id'],
                        content_type='verse'
                    )
    
    async def schedule_hadith_daily(self, context: ContextTypes.DEFAULT_TYPE):
        """جدولة الحديث اليومي (12:00 ظهراً)"""
        
        while self.is_running:
            now = datetime.now()
            target_time = now.replace(
                hour=default_schedule.HADITH_DAILY.hour,
                minute=default_schedule.HADITH_DAILY.minute,
                second=0,
                microsecond=0
            )
            
            if now >= target_time:
                target_time = target_time.replace(day=target_time.day + 1)
            
            wait_seconds = (target_time - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            
            if not self.is_running:
                break
            
            channels = self.db.get_all_active_channels()
            for channel in channels:
                settings = self.db.get_all_channel_settings(channel['id'])
                if settings.get('hadith_daily_enabled') == '1':
                    await self.publish_content(
                        context=context,
                        channel_id=channel['id'],
                        chat_id=channel['chat_id'],
                        content_type='hadith'
                    )
    
    async def schedule_tasbih(self, context: ContextTypes.DEFAULT_TYPE):
        """جدولة التسبيح (كل ساعتين)"""
        
        while self.is_running:
            await asyncio.sleep(default_schedule.TASBIH_INTERVAL)
            
            if not self.is_running:
                break
            
            channels = self.db.get_all_active_channels()
            for channel in channels:
                settings = self.db.get_all_channel_settings(channel['id'])
                if settings.get('tasbih_enabled') == '1':
                    await self.publish_content(
                        context=context,
                        channel_id=channel['id'],
                        chat_id=channel['chat_id'],
                        content_type='tasbih'
                    )
    
    async def schedule_istighfar(self, context: ContextTypes.DEFAULT_TYPE):
        """جدولة الاستغفار (كل 3 ساعات)"""
        
        while self.is_running:
            await asyncio.sleep(default_schedule.ISTIGHFAR_INTERVAL)
            
            if not self.is_running:
                break
            
            channels = self.db.get_all_active_channels()
            for channel in channels:
                settings = self.db.get_all_channel_settings(channel['id'])
                if settings.get('istighfar_enabled') == '1':
                    await self.publish_content(
                        context=context,
                        channel_id=channel['id'],
                        chat_id=channel['chat_id'],
                        content_type='istighfar'
                    )
    
    # =========================================================================
    # تشغيل وإيقاف البوت
    # =========================================================================
    
    async def run(self):
        """تشغيل البوت"""
        
        logger.info("=" * 50)
        logger.info("🕌 بدء بوت الحارس الإسلامي")
        logger.info("=" * 50)
        
        # إنشاء التطبيق
        self.application = self.create_application()
        
        # بدء التطبيق
        await self.application.initialize()
        await self.application.start()
        
        # بدء updater
        await self.application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
        logger.info("البوت يعمل الآن!")
        
        # بدء الجدولة بعد فترة قصيرة
        await asyncio.sleep(5)
        await self.start_scheduler(self.application.context)
        
        # البقاء قيد التشغيل
        while self.is_running:
            await asyncio.sleep(1)
    
    def stop(self):
        """إيقاف البوت"""
        
        logger.info("إيقاف البوت...")
        self.is_running = False
        
        # إلغاء مهام الجدولة
        for task in self.scheduler_tasks:
            task.cancel()
        
        logger.info("تم إيقاف البوت")


# =============================================================================
# نقطة الدخول الرئيسية
# =============================================================================

def main():
    """الدالة الرئيسية"""
    
    bot = IslamicGuardianBot()
    
    # معالجة إشارات الإيقاف
    def signal_handler(sig, frame):
        logger.info("تم استلام إشارة الإيقاف")
        bot.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # تشغيل البوت
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        logger.error(f"خطأ غير متوقع: {e}")
        raise


if __name__ == "__main__":
    main()
