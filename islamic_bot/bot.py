# bot.py - البوت الرئيسي لإدارة القنوات الدينية

import logging
import random
from datetime import datetime, time, timedelta
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, CallbackQueryHandler,
    ConversationHandler
)

from config import BotConfig, PrayerTimes, ContentLimits, IslamicContent
from database import DatabaseManager

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class IslamicChannelBot:
    """بوت إدارة القنوات الدينية"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.config = BotConfig()
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /start - رسالة الترحيب"""
        user = update.effective_user
        
        start_text = f"""
🌟 *مرحباً بك في بوت القنوات الدينية!* 🌟

👤 أهلاً بك يا {user.first_name}

🕌 **وظيفة البوت:**
إدارة قنوات تليجرام دينية ونشر الأذكار والآيات والأحاديث تلقائياً

✨ **المميزات الرئيسية:**
1️⃣ 📿 نشر أذكار الصباح والمساء تلقائياً
2️⃣ 📖 آية يومية مختارة
3️⃣ 📜 حديث شريف يومي
4️⃣ 💫 تسبيحات دورية طوال اليوم
5️⃣ 📊 إحصائيات مفصلة للقناة
6️⃣ ⚙️ تحكم كامل في الإعدادات

🔧 **للبدء:**
- أضف البوت كمشرف في قناتك
- استخدم /add_channel لتسجيل القناة
- استخدم /help لمعرفة جميع الأوامر

💡 **ملاحظة:** البوت مجاني تماماً لخدمة الإسلام والمسلمين
        """
        
        keyboard = [
            [InlineKeyboardButton("➕ إضافة قناة", callback_data='add_channel')],
            [InlineKeyboardButton("📋 قنواتي", callback_data='my_channels')],
            [InlineKeyboardButton("❓ مساعدة", callback_data='help')],
            [InlineKeyboardButton("⚙️ الإعدادات", callback_data='settings')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(start_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /help - عرض المساعدة"""
        help_text = """
📚 *دليل استخدام البوت* 📚

🔹 *أوامر الإدارة:*
/add_channel - إضافة قناة جديدة
/remove_channel - إزالة قناة
/my_channels - عرض قنواتك
/settings - إعدادات القناة

🔹 *أوامر النشر:*
/publish_adkar - نشر الأذكار الآن
/publish_verse - نشر آية
/publish_hadith - نشر حديث
/publish_tasbih - نشر تسبيحة

🔹 *أوامر التحكم:*
/enable_adkar - تفعيل أذكار تلقائية
/disable_adkar - تعطيل أذكار تلقائية
/enable_verse - تفعيل الآيات اليومية
/enable_hadith - تفعيل الأحاديث اليومية

🔹 *الإحصائيات:*
/stats - إحصائيات القناة
/report - تقرير شامل

🔹 *أوامر أخرى:*
/developers - معلومات المطورين
/about - عن البوت

💡 ملاحظة: معظم الأوامر تعمل فقط مع القنوات المسجلة
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def add_channel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /add_channel - إضافة قناة جديدة"""
        user_id = update.effective_user.id
        
        # التحقق من عدد القنوات
        user_channels = self.db.get_user_channels(user_id)
        if len(user_channels) >= ContentLimits.MAX_CHANNELS_PER_USER:
            await update.message.reply_text(
                f"⚠️ عذراً، لقد وصلت للحد الأقصى ({ContentLimits.MAX_CHANNELS_PER_USER} قنوات)"
            )
            return
        
        # طلب تحويل القناة
        await update.message.reply_text(
            "📝 *لإضافة قناة:*\\n\\n"
            "1️⃣ أضف البوت كـ **مشرف** في قناتك\\n"
            "2️⃣ أرسل معرف القناة (مثال: @MyChannel)\\n\\n"
            "أو قم بتحويل أي رسالة من القناة إلى البوت",
            parse_mode='Markdown'
        )
        
        # وضع المستخدم في حالة انتظار
        context.user_data['waiting_for_channel'] = True
    
    async def my_channels_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /my_channels - عرض قنوات المستخدم"""
        user_id = update.effective_user.id
        channels = self.db.get_user_channels(user_id)
        
        if not channels:
            await update.message.reply_text(
                "📭 ليس لديك قنوات مسجلة حالياً.\n\n"
                "استخدم /add_channel لإضافة قناة جديدة."
            )
            return
        
        text = "📋 *قنواتك المسجلة:*\n\n"
        keyboard = []
        
        for channel in channels:
            status = "✅ مفعلة" if channel['is_active'] else "❌ معطلة"
            text += f"• {channel['channel_title']} ({channel['channel_username']})\n"
            text += f"  الحالة: {status}\n"
            text += f"  المنشورات: {channel['posts_count']}\n\n"
            
            keyboard.append([
                InlineKeyboardButton(f"⚙️ إعدادات", callback_data=f'channel_settings_{channel["channel_id"]}'),
                InlineKeyboardButton(f"📊 إحصائيات", callback_data=f'channel_stats_{channel["channel_id"]}')
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='back_main')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def publish_adkar_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /publish_adkar - نشر الأذكار"""
        user_id = update.effective_user.id
        channels = self.db.get_user_channels(user_id)
        
        if not channels:
            await update.message.reply_text("⚠️ ليس لديك قنوات مسجلة!")
            return
        
        # تحديد نوع الذكر
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            adkar_type = 'morning'
            adkar_list = IslamicContent.MORNING_ADKAR
            title = "🌅 أذكار الصباح"
        elif 12 <= current_hour < 18:
            adkar_type = 'evening'
            adkar_list = IslamicContent.EVENING_ADKAR
            title = "🌙 أذكار المساء"
        else:
            adkar_type = 'sleep'
            adkar_list = IslamicContent.SLEEP_ADKAR
            title = "😴 أذكار النوم"
        
        # اختيار ذكر عشوائي
        selected_dhikr = random.choice(adkar_list)
        
        message_text = f"{title}\n\n{selected_dhikr}\n\n"
        message_text += "📿 سبحان الله وبحمده، سبحان الله العظيم"
        
        # نشر في جميع القنوات
        success_count = 0
        for channel in channels:
            try:
                sent_message = await context.bot.send_message(
                    chat_id=channel['channel_id'],
                    text=message_text,
                    parse_mode='Markdown'
                )
                
                # تسجيل المنشور
                self.db.log_adkar_post(
                    channel['channel_id'],
                    adkar_type,
                    selected_dhikr,
                    sent_message.message_id
                )
                self.db.update_daily_stats(channel['channel_id'], 'adkar')
                success_count += 1
            except Exception as e:
                logger.error(f"Error publishing to channel {channel['channel_id']}: {e}")
        
        await update.message.reply_text(
            f"✅ تم نشر الأذكار في {success_count} من قنواتك"
        )
    
    async def publish_verse_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /publish_verse - نشر آية قرآنية"""
        user_id = update.effective_user.id
        channels = self.db.get_user_channels(user_id)
        
        if not channels:
            await update.message.reply_text("⚠️ ليس لديك قنوات مسجلة!")
            return
        
        verse_data = random.choice(IslamicContent.QURAN_VERSES)
        message_text = f"""
📖 *آية من القرآن الكريم*

"{verse_data['verse']}"

📚 سورة: {verse_data['surah']}

✨ صدق الله العظيم
        """
        
        success_count = 0
        for channel in channels:
            try:
                sent_message = await context.bot.send_message(
                    chat_id=channel['channel_id'],
                    text=message_text,
                    parse_mode='Markdown'
                )
                
                self.db.log_daily_content(
                    channel['channel_id'],
                    'verse',
                    verse_data['verse'],
                    verse_data['surah'],
                    sent_message.message_id
                )
                self.db.update_daily_stats(channel['channel_id'], 'verses')
                success_count += 1
            except Exception as e:
                logger.error(f"Error publishing verse to channel {channel['channel_id']}: {e}")
        
        await update.message.reply_text(
            f"✅ تم نشر الآية في {success_count} من قنواتك"
        )
    
    async def publish_hadith_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /publish_hadith - نشر حديث شريف"""
        user_id = update.effective_user.id
        channels = self.db.get_user_channels(user_id)
        
        if not channels:
            await update.message.reply_text("⚠️ ليس لديك قنوات مسجلة!")
            return
        
        hadith_data = random.choice(IslamicContent.HADITHS)
        message_text = f"""
📜 *حديث شريف*

{hadith_data['text']}

📚 {hadith_data['source']}

ﷺ صلى الله عليه وسلم
        """
        
        success_count = 0
        for channel in channels:
            try:
                sent_message = await context.bot.send_message(
                    chat_id=channel['channel_id'],
                    text=message_text,
                    parse_mode='Markdown'
                )
                
                self.db.log_daily_content(
                    channel['channel_id'],
                    'hadith',
                    hadith_data['text'],
                    hadith_data['source'],
                    sent_message.message_id
                )
                self.db.update_daily_stats(channel['channel_id'], 'hadith')
                success_count += 1
            except Exception as e:
                logger.error(f"Error publishing hadith to channel {channel['channel_id']}: {e}")
        
        await update.message.reply_text(
            f"✅ تم نشر الحديث في {success_count} من قنواتك"
        )
    
    async def publish_tasbih_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /publish_tasbih - نشر تسبيحة"""
        user_id = update.effective_user.id
        channels = self.db.get_user_channels(user_id)
        
        if not channels:
            await update.message.reply_text("⚠️ ليس لديك قنوات مسجلة!")
            return
        
        tasbih = random.choice(IslamicContent.TASBIHAT)
        count = random.choice([33, 100, 300])
        
        message_text = f"""
💫 *تسبيحة*

{tasbih}

عدد التسبيحات: {count}

📿 اللهم تقبل منا إنك أنت السميع العليم
        """
        
        success_count = 0
        for channel in channels:
            try:
                sent_message = await context.bot.send_message(
                    chat_id=channel['channel_id'],
                    text=message_text,
                    parse_mode='Markdown'
                )
                
                self.db.log_adkar_post(
                    channel['channel_id'],
                    'tasbih',
                    f"{tasbih} ({count} مرة)",
                    sent_message.message_id
                )
                self.db.update_daily_stats(channel['channel_id'], 'tasbih')
                success_count += 1
            except Exception as e:
                logger.error(f"Error publishing tasbih to channel {channel['channel_id']}: {e}")
        
        await update.message.reply_text(
            f"✅ تم نشر التسبيحة في {success_count} من قنواتك"
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /stats - عرض الإحصائيات"""
        user_id = update.effective_user.id
        channels = self.db.get_user_channels(user_id)
        
        if not channels:
            await update.message.reply_text("⚠️ ليس لديك قنوات مسجلة!")
            return
        
        if len(channels) == 1:
            # قناة واحدة فقط
            channel = channels[0]
            stats = self.db.get_total_stats(channel['channel_id'])
            
            text = f"""
📊 *إحصائيات القناة*

📍 {channel['channel_title']}

📝 إجمالي المنشورات: {stats.get('total_posts', 0)}
📿 الأذكار: {stats.get('total_adkar', 0)}
💫 التسبيحات: {stats.get('total_tasbih', 0)}
📖 الآيات: {stats.get('total_verses', 0)}
📜 الأحاديث: {stats.get('total_hadith', 0)}
            """
            await update.message.reply_text(text, parse_mode='Markdown')
        else:
            # عرض قائمة القنوات
            keyboard = []
            for channel in channels:
                keyboard.append([
                    InlineKeyboardButton(
                        f"📊 {channel['channel_title']}",
                        callback_data=f'stats_{channel["channel_id"]}'
                    )
                ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "📊 اختر قناة لعرض إحصائياتها:",
                reply_markup=reply_markup
            )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الأزرار التفاعلية"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == 'add_channel':
            await query.edit_message_text(
                "➕ *إضافة قناة جديدة*\n\n"
                "1️⃣ أضف البوت كمشرف في قناتك\n"
                "2️⃣ أرسل معرف القناة (مثال: @ChannelName)\n\n"
                "أو قم بتحويل أي رسالة من القناة إلى البوت",
                parse_mode='Markdown'
            )
            context.user_data['waiting_for_channel'] = True
            
        elif data == 'my_channels':
            await self.my_channels_command(update, context)
            
        elif data == 'help':
            await query.edit_message_text(
                """
📚 *دليل الاستخدام*

🔹 /start - العودة للصفحة الرئيسية
🔹 /help - عرض هذه الرسالة
🔹 /add_channel - إضافة قناة
🔹 /my_channels - قنواتك
🔹 /publish_adkar - نشر الأذكار
🔹 /publish_verse - نشر آية
🔹 /publish_hadith - نشر حديث
🔹 /stats - الإحصائيات
                """,
                parse_mode='Markdown'
            )
            
        elif data == 'settings':
            await query.edit_message_text(
                "⚙️ *الإعدادات*\n\n"
                "اختر القناة التي تريد تعديل إعداداتها:",
                parse_mode='Markdown'
            )
            
        elif data.startswith('channel_stats_'):
            channel_id = int(data.split('_')[2])
            stats = self.db.get_total_stats(channel_id)
            channel = self.db.get_channel(channel_id)
            
            text = f"""
📊 *إحصائيات القناة*

📍 {channel['channel_title']}

📝 إجمالي المنشورات: {stats.get('total_posts', 0)}
📿 الأذكار: {stats.get('total_adkar', 0)}
💫 التسبيحات: {stats.get('total_tasbih', 0)}
📖 الآيات: {stats.get('total_verses', 0)}
📜 الأحاديث: {stats.get('total_hadith', 0)}
            """
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='my_channels')]]
            await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
            
        elif data.startswith('channel_settings_'):
            channel_id = int(data.split('_')[2])
            channel = self.db.get_channel(channel_id)
            
            adkar_status = "✅ مفعلة" if channel['adkar_enabled'] else "❌ معطلة"
            tasbih_status = "✅ مفعلة" if channel['tasbih_enabled'] else "❌ معطلة"
            verse_status = "✅ مفعلة" if channel['verse_enabled'] else "❌ معطلة"
            hadith_status = "✅ مفعلة" if channel['hadith_enabled'] else "❌ معطلة"
            
            text = f"""
⚙️ *إعدادات القناة*

📍 {channel['channel_title']}

📿 أذكار تلقائية: {adkar_status}
💫 تسبيحات: {tasbih_status}
📖 آيات يومية: {verse_status}
📜 أحاديث: {hadith_status}
            """
            
            keyboard = [
                [
                    InlineKeyboardButton(
                        "toggle_adkar",
                        callback_data=f'toggle_adkar_{channel_id}'
                    ),
                    InlineKeyboardButton(
                        "toggle_tasbih",
                        callback_data=f'toggle_tasbih_{channel_id}'
                    )
                ],
                [
                    InlineKeyboardButton(
                        "toggle_verse",
                        callback_data=f'toggle_verse_{channel_id}'
                    ),
                    InlineKeyboardButton(
                        "toggle_hadith",
                        callback_data=f'toggle_hadith_{channel_id}'
                    )
                ],
                [InlineKeyboardButton("🔙 رجوع", callback_data='my_channels')]
            ]
            
            await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
            
        elif data.startswith('toggle_'):
            parts = data.split('_')
            setting = parts[1]
            channel_id = int(parts[2])
            
            # تبديل الإعداد
            current_value = self.db.get_channel(channel_id)[f'{setting}_enabled']
            new_value = 0 if current_value else 1
            
            self.db.update_channel_settings(channel_id, **{f'{setting}_enabled': new_value})
            
            await query.edit_message_text(
                f"✅ تم {'تفعيل' if new_value else 'تعطيل'} {setting} بنجاح!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data=f'channel_settings_{channel_id}')]])
            )
            
        elif data == 'back_main':
            await self.start_command(update, context)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الرسائل النصية"""
        user_data = context.user_data
        
        if user_data.get('waiting_for_channel'):
            channel_info = update.message.text
            
            # التحقق إذا كان معرف قناة
            if channel_info.startswith('@'):
                try:
                    # الحصول على معلومات القناة
                    chat = await context.bot.get_chat(chat_id=channel_info)
                    
                    # التحقق من أن البوت مشرف
                    member = await context.bot.get_chat_member(
                        chat_id=chat.id,
                        user_id=context.bot.id
                    )
                    
                    if member.status in ['administrator', 'creator']:
                        # إضافة القناة
                        success = self.db.add_channel(
                            channel_id=chat.id,
                            channel_username=chat.username or '',
                            channel_title=chat.title,
                            owner_id=update.effective_user.id,
                            owner_username=update.effective_user.username or ''
                        )
                        
                        if success:
                            await update.message.reply_text(
                                f"✅ تم إضافة القناة بنجاح!\n\n"
                                f"📍 {chat.title}\n"
                                f"🆔 @{chat.username}"
                            )
                        else:
                            await update.message.reply_text("❌ حدث خطأ أثناء إضافة القناة")
                        
                        user_data['waiting_for_channel'] = False
                    else:
                        await update.message.reply_text(
                            "⚠️ البوت ليس مشرفاً في هذه القناة!\n"
                            "يرجى إضافة البوت كمشرف أولاً."
                        )
                except Exception as e:
                    await update.message.reply_text(f"❌ خطأ: {str(e)}")
            else:
                await update.message.reply_text(
                    "⚠️ يرجى إرسال معرف القناة بشكل صحيح (مثال: @ChannelName)"
                )
    
    async def scheduled_tasks(self, context: ContextTypes.DEFAULT_TYPE):
        """تنفيذ المهام المجدولة"""
        now = datetime.now()
        
        # أذكار الصباح (6:00 صباحاً)
        if now.hour == PrayerTimes.MORNING_ADKAR_TIME.hour and now.minute == PrayerTimes.MORNING_ADKAR_TIME.minute:
            await self.auto_publish_morning_adkar(context)
        
        # أذكار المساء (6:00 مساءً)
        if now.hour == PrayerTimes.EVENING_ADKAR_TIME.hour and now.minute == PrayerTimes.EVENING_ADKAR_TIME.minute:
            await self.auto_publish_evening_adkar(context)
        
        # الآية اليومية (8:00 صباحاً)
        if now.hour == PrayerTimes.DAILY_VERSE_TIME.hour and now.minute == PrayerTimes.DAILY_VERSE_TIME.minute:
            await self.auto_publish_daily_verse(context)
        
        # الحديث اليومي (12:00 ظهراً)
        if now.hour == PrayerTimes.DAILY_HADITH_TIME.hour and now.minute == PrayerTimes.DAILY_HADITH_TIME.minute:
            await self.auto_publish_daily_hadith(context)
    
    async def auto_publish_morning_adkar(self, context: ContextTypes.DEFAULT_TYPE):
        """نشر أذكار الصباح تلقائياً"""
        channels = self.db.get_all_active_channels()
        
        for channel in channels:
            if not channel['adkar_enabled']:
                continue
            
            try:
                dhikr = random.choice(IslamicContent.MORNING_ADKAR)
                message_text = f"🌅 *أذكار الصباح*\n\n{dhikr}\n\n📿 سبحان الله وبحمده"
                
                sent_message = await context.bot.send_message(
                    chat_id=channel['channel_id'],
                    text=message_text,
                    parse_mode='Markdown'
                )
                
                self.db.log_adkar_post(channel['channel_id'], 'morning', dhikr, sent_message.message_id)
                self.db.update_daily_stats(channel['channel_id'], 'adkar')
            except Exception as e:
                logger.error(f"Error auto-publishing morning adkar: {e}")
    
    async def auto_publish_evening_adkar(self, context: ContextTypes.DEFAULT_TYPE):
        """نشر أذكار المساء تلقائياً"""
        channels = self.db.get_all_active_channels()
        
        for channel in channels:
            if not channel['adkar_enabled']:
                continue
            
            try:
                dhikr = random.choice(IslamicContent.EVENING_ADKAR)
                message_text = f"🌙 *أذكار المساء*\n\n{dhikr}\n\n📿 سبحان الله وبحمده"
                
                sent_message = await context.bot.send_message(
                    chat_id=channel['channel_id'],
                    text=message_text,
                    parse_mode='Markdown'
                )
                
                self.db.log_adkar_post(channel['channel_id'], 'evening', dhikr, sent_message.message_id)
                self.db.update_daily_stats(channel['channel_id'], 'adkar')
            except Exception as e:
                logger.error(f"Error auto-publishing evening adkar: {e}")
    
    async def auto_publish_daily_verse(self, context: ContextTypes.DEFAULT_TYPE):
        """نشر الآية اليومية تلقائياً"""
        channels = self.db.get_all_active_channels()
        
        for channel in channels:
            if not channel['verse_enabled']:
                continue
            
            try:
                verse = random.choice(IslamicContent.QURAN_VERSES)
                message_text = f"📖 *آية يومية*\n\n\"{verse['verse']}\"\n\n📚 {verse['surah']}"
                
                sent_message = await context.bot.send_message(
                    chat_id=channel['channel_id'],
                    text=message_text,
                    parse_mode='Markdown'
                )
                
                self.db.log_daily_content(channel['channel_id'], 'verse', verse['verse'], verse['surah'], sent_message.message_id)
                self.db.update_daily_stats(channel['channel_id'], 'verses')
            except Exception as e:
                logger.error(f"Error auto-publishing daily verse: {e}")
    
    async def auto_publish_daily_hadith(self, context: ContextTypes.DEFAULT_TYPE):
        """نشر الحديث اليومي تلقائياً"""
        channels = self.db.get_all_active_channels()
        
        for channel in channels:
            if not channel['hadith_enabled']:
                continue
            
            try:
                hadith = random.choice(IslamicContent.HADITHS)
                message_text = f"📜 *حديث يومي*\n\n{hadith['text']}\n\n📚 {hadith['source']}"
                
                sent_message = await context.bot.send_message(
                    chat_id=channel['channel_id'],
                    text=message_text,
                    parse_mode='Markdown'
                )
                
                self.db.log_daily_content(channel['channel_id'], 'hadith', hadith['text'], hadith['source'], sent_message.message_id)
                self.db.update_daily_stats(channel['channel_id'], 'hadith')
            except Exception as e:
                logger.error(f"Error auto-publishing daily hadith: {e}")
    
    def run(self):
        """تشغيل البوت"""
        application = Application.builder().token(self.config.BOT_TOKEN).build()
        
        # إضافة المعالجات
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("add_channel", self.add_channel_command))
        application.add_handler(CommandHandler("my_channels", self.my_channels_command))
        application.add_handler(CommandHandler("publish_adkar", self.publish_adkar_command))
        application.add_handler(CommandHandler("publish_verse", self.publish_verse_command))
        application.add_handler(CommandHandler("publish_hadith", self.publish_hadith_command))
        application.add_handler(CommandHandler("publish_tasbih", self.publish_tasbih_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        
        application.add_handler(CallbackQueryHandler(self.button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # جدولة المهام التلقائية
        job_queue = application.job_queue
        job_queue.run_repeating(self.scheduled_tasks, interval=60, first=1)
        
        logger.info("🕌 بوت القنوات الدينية يعمل بنجاح!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    bot = IslamicChannelBot()
    bot.run()


if __name__ == '__main__':
    main()
