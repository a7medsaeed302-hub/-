# main.py - البوت الرئيسي المتقدم
import logging
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, CallbackQueryHandler,
    ConversationHandler
)
from config import Config
from database import DatabaseManager

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AdvancedGroupProtectionBot:
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager()
        self.active_games = {}
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /start مع رسالة بداية احترافية"""
        user = update.effective_user
        
        start_text = f"""
🎉 *مرحباً بك في بوت حماية المجموعات الاحترافي!* 🎉

👑 **مطور البوت:** @{@A7med19_7}
🛡️ **وظيفة البوت:** حماية المجموعات وتنظيمها بشكل قوي

🌟 **المميزات المتوفرة:**

1️⃣ 🛡️ **حماية متقدمة:** حظر، طرد، كتم، تحذير
2️⃣ 🎮 **ألعاب جماعية:** 10 ألعاب مختلفة
3️⃣ 📚 **مسابقات قرآن:** آيات وحكم
4️⃣ 🤖 **ردود ذكية:** ردود لطيفة وفكاهية
5️⃣ ❤️ **قلوب للمالك:** قلب على كل رسالة للمالك
6️⃣ 🎉 **ترحيب متقدم:** رسائل ترحيب مع صور

🔧 **الأوامر العربية المتاحة:** /help

💡 **نصيحة:** قم بإضافة البوت كمسؤول في المجموعة ليعمل بكامل ميزاته!
        """
        
        await update.message.reply_text(start_text, parse_mode='Markdown')
        
        # إضافة صورة البوت
        try:
            await update.message.reply_photo(
                photo=open(self.config.BOT_IMAGE_PATH, 'rb'),
                caption="🛡️ هذا هو بوت الحماية الخاص بكم!"
            )
        except:
            await update.message.reply_text("🛡️ بوت الحماية الاحترافي")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /help مع جميع الأوامر العربية"""
        
        help_text = """
🛡️ *أوامر الحماية والتنظيم* 🛡️

👮‍♂️ **أوامر المشرفين:**

🔴 `/حظر` - حظر عضو من المجموعة
🔴 `/فك_حظر` - فك حظر عضو
🔴 `/طرد` - طرد عضو من المجموعة
🔴 `/كتم` - كتم عضو لفترة محددة
🔴 `/فك_كتم` - فك كتم عضو
🔴 `/تحذير` - إعطاء تحذير لعضو
🔴 `/قفل` - قفل الشات كاملاً
🔴 `/فتح` - فتح الشات بعد القفل
🔴 `/مسح` - مسح رسالة محددة
🔴 `/مسح_كل` - مسح جميع الرسائل

⚙️ **أوامر الإدارة:**

📝 `/القواعد` - عرض قواعد المجموعة
📝 `/تعيين_القواعد` - تعيين قواعد جديدة
🎉 `/الترحيب` - عرض رسالة الترحيب
🎉 `/تعيين_ترحيب` - تعيين ترحيب جديد
📊 `/الإحصائيات` - إحصائيات المجموعة
👥 `/الأعضاء` - قائمة الأعضاء النشطين
⚠️ `/التحذيرات` - قائمة التحذيرات

🎮 **أوامر الألعاب والأنشطة:**

🎯 `/مسابقة` - بدء مسابقة ذكاء
🎲 `/نرد` - لعبة النرد
🏀 `/سلة` - لعبة السلة
🎮 `/تخمين` - لعبة التخمين
📚 `/قرآن` - مسابقة قرآنية
🧠 `/اختبار` - اختبار معلومات
🎪 `/لغز` - لعبة الألغاز
🎨 `/رسم` - لعبة الرسم
🎤 `/غناء` - مسابقة غنائية
🏆 `/بطولة` - بطولة المجموعة

😊 **أوامر التفاعل:**

❤️ `/قلوب` - عدد قلوب المالك
🌟 `/نشاط` - نشاط الأعضاء
🎉 `/ترحيب` - ترحيب بالأعضاء الجدد

🔧 **أوامر المساعدة:**

❓ `/مساعدة` - هذه الرسالة
🌀 `/المطور` - معلومات المطور
🔄 `/تحديث` - تحديث بيانات البوت

💡 **تذكير:** معظم الأوامر تحتاج إلى صلاحيات مشرف!
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def ban_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /حظر"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("⚠️ هذا الأمر للمشرفين فقط!")
            return
        
        try:
            user_id = int(context.args[0])
            reason = " ".join(context.args[1:]) if len(context.args) > 1 else "سبب غير محدد"
            
            await context.bot.ban_chat_member(
                chat_id=update.effective_chat.id,
                user_id=user_id
            )
            
            await update.message.reply_text(
                f"🔴 *تم حظر العضو بنجاح!*\n\n"
                f"👤 **العضو:** {user_id}\n"
                f"📝 **السبب:** {reason}\n"
                f"🕒 **التاريخ:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                f"⚠️ يمكن فك الحظر باستخدام /فك_حظر",
                parse_mode='Markdown'
            )
            
        except (IndexError, ValueError):
            await update.message.reply_text(
                "⚠️ *طريقة استخدام الأمر:*\n"
                "/حظر <رقم العضو> [سبب الحظر]\n\n"
                "مثال: /حظر 123456789 السبب: مخالفة القواعد",
                parse_mode='Markdown'
            )

    async def kick_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /طرد"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("⚠️ هذا الأمر للمشرفين فقط!")
            return
        
        try:
            user_id = int(context.args[0])
            reason = " ".join(context.args[1:]) if len(context.args) > 1 else "سبب غير محدد"
            
            await context.bot.ban_chat_member(
                chat_id=update.effective_chat.id,
                user_id=user_id
            )
            await context.bot.unban_chat_member(
                chat_id=update.effective_chat.id,
                user_id=user_id
            )
            
            await update.message.reply_text(
                f"🚪 *تم طرد العضو بنجاح!*\n\n"
                f"👤 **العضو:** {user_id}\n"
                f"📝 **السبب:** {reason}\n"
                f"🕒 **التاريخ:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                f"💡 يمكن للعضو الانضمام مرة أخرى إذا دعاه أحد الأعضاء",
                parse_mode='Markdown'
            )
            
        except (IndexError, ValueError):
            await update.message.reply_text(
                "⚠️ *طريقة استخدام الأمر:*\n"
                "/طرد <رقم العضو> [سبب الطرد]\n\n"
                "مثال: /طرد 123456789 السبب: سلوك غير لائق",
                parse_mode='Markdown'
            )

    async def mute_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /كتم"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("⚠️ هذا الأمر للمشرفين فقط!")
            return
        
        try:
            user_id = int(context.args[0])
            duration = int(context.args[1]) if len(context.args) > 1 else 60  # 60 دقيقة افتراضياً
            reason = " ".join(context.args[2:]) if len(context.args) > 2 else "سبب غير محدد"
            
            until_date = datetime.now() + timedelta(minutes=duration)
            
            await context.bot.restrict_chat_member(
                chat_id=update.effective_chat.id,
                user_id=user_id,
                permissions={
                    'can_send_messages': False,
                    'can_send_media_messages': False,
                    'can_send_polls': False,
                    'can_send_other_messages': False,
                    'can_add_web_page_previews': False
                },
                until_date=until_date
            )
            
            await update.message.reply_text(
                f"🔇 *تم كتم العضو بنجاح!*\n\n"
                f"👤 **العضو:** {user_id}\n"
                f"⏰ **المدة:** {duration} دقيقة\n"
                f"📝 **السبب:** {reason}\n"
                f"🕒 **التاريخ:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                f"⚠️ يمكن فك الكتم باستخدام /فك_كتم",
                parse_mode='Markdown'
            )
            
        except (IndexError, ValueError):
            await update.message.reply_text(
                "⚠️ *طريقة استخدام الأمر:*\n"
                "/كتم <رقم العضو> [المدة بالدقائق] [سبب الكتم]\n\n"
                "مثال: /كتم 123456789 30 السبب: إساءة",
                parse_mode='Markdown'
            )

    async def lock_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /قفل"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("⚠️ هذا الأمر للمشرفين فقط!")
            return
        
        chat_id = update.effective_chat.id
        
        await context.bot.set_chat_permissions(
            chat_id=chat_id,
            permissions={
                'can_send_messages': False,
                'can_send_media_messages': False,
                'can_send_polls': False,
                'can_send_other_messages': False,
                'can_add_web_page_previews': False,
                'can_change_info': False,
                'can_invite_users': False,
                'can_pin_messages': False
            }
        )
        
        await update.message.reply_text(
            "🔒 *تم قفل الشات بنجاح!*\n\n"
            "⚠️ جميع الأعضاء لا يمكنهم الكتابة الآن\n"
            "💡 يمكن فتح الشات باستخدام /فتح",
            parse_mode='Markdown'
        )

    async def unlock_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /فتح"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("⚠️ هذا الأمر للمشرفين فقط!")
            return
        
        chat_id = update.effective_chat.id
        
        await context.bot.set_chat_permissions(
            chat_id=chat_id,
            permissions={
                'can_send_messages': True,
                'can_send_media_messages': True,
                'can_send_polls': True,
                'can_send_other_messages': True,
                'can_add_web_page_previews': True,
                'can_change_info': True,
                'can_invite_users': True,
                'can_pin_messages': True
            }
        )
        
        await update.message.reply_text(
            "🔓 *تم فتح الشات بنجاح!*\n\n"
            "🎉 يمكن للأعضاء الكتابة الآن\n"
            "💬 الشات مفتوح للجميع",
            parse_mode='Markdown'
        )

    async def games_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /مسابقة - عرض قائمة الألعاب"""
        
        keyboard = []
        for i in range(0, len(self.config.GAMES_LIST), 2):
            row = []
            for game in self.config.GAMES_LIST[i:i+2]:
                row.append(InlineKeyboardButton(game["name"], callback_data=f"game_{game['command'][1:]}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🎲 جميع الألعاب", callback_data="game_all")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎮 *قائمة الألعاب المتاحة:*\n\n"
            "اختر لعبة من القائمة:\n"
            "🎯 مسابقة ذكاء\n"
            "🎲 لعبة النرد\n"
            "🏀 لعبة السلة\n"
            "🎮 لعبة التخمين\n"
            "📚 مسابقة قرآن\n"
            "🧠 اختبار معلومات\n"
            "🎪 لعبة الألغاز\n"
            "🎨 لعبة الرسم\n"
            "🎤 مسابقة غنائية\n"
            "🏆 بطولة المجموعة",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def game_callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة اختيار الألعاب"""
        query = update.callback_query
        await query.answer()
        
        game_type = query.data.split("_")[1]
        
        if game_type == "quiz":
            await self.start_quiz_game(query, context)
        elif game_type == "dice":
            await self.start_dice_game(query, context)
        elif game_type == "basketball":
            await self.start_basketball_game(query, context)
        elif game_type == "quran":
            await self.start_quran_game(query, context)
        elif game_type == "all":
            await self.show_all_games(query, context)
        else:
            await query.edit_message_text(f"🎮 لعبة {game_type} قيد التطوير!")

    async def start_quiz_game(self, query, context):
        """بدء مسابقة الذكاء"""
        questions = [
            {"question": "ما هي عاصمة فرنسا؟", "options": ["لندن", "باريس", "برلين", "روما"], "answer": 2},
            {"question": "كم عدد كواكب المجموعة الشمسية؟", "options": ["7", "8", "9", "10"], "answer": 2},
            {"question": "ما هو أكبر كوكب في المجموعة الشمسية؟", "options": ["الأرض", "المريخ", "الزهرة", "المشتري"], "answer": 4},
            {"question": "ما هي اللغة الرسمية في مصر؟", "options": ["الإنجليزية", "الفرنسية", "العربية", "الإسبانية"], "answer": 3},
            {"question": "كم عدد أيام الأسبوع؟", "options": ["5", "6", "7", "8"], "answer": 3}
        ]
        
        question = random.choice(questions)
        
        keyboard = []
        for i, option in enumerate(question["options"], 1):
            keyboard.append([InlineKeyboardButton(f"{i}. {option}", callback_data=f"answer_{i}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎯 *مسابقة الذكاء*\n\n"
            f"❓ السؤال: {question['question']}\n\n"
            f"اختر الإجابة الصحيحة:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def start_dice_game(self, query, context):
        """لعبة النرد"""
        dice_message = await context.bot.send_dice(
            chat_id=query.message.chat.id,
            emoji='🎲'
        )
        dice_value = dice_message.dice.value
        
        await query.edit_message_text(
            f"🎲 *لعبة النرد*\n\n"
            f"{query.from_user.first_name} رمى النرد!\n"
            f"🎲 النتيجة: {dice_value}\n\n"
            f"💡 {dice_value} نقطة!",
            parse_mode='Markdown'
        )

    async def start_basketball_game(self, query, context):
        """لعبة السلة"""
        basketball_message = await context.bot.send_dice(
            chat_id=query.message.chat.id,
            emoji='🏀'
        )
        score = basketball_message.dice.value
        
        if score == 5:
            result_text = "🎉 سلة ثلاثية! ممتاز!"
        elif score >= 3:
            result_text = "👍 سلة ناجحة!"
        else:
            result_text = "😅 محاولة جيدة!"
        
        await query.edit_message_text(
            f"🏀 *لعبة السلة*\n\n"
            f"{query.from_user.first_name} حاول التسجيل!\n"
            f"🏀 النتيجة: {score} نقطة\n\n"
            f"{result_text}",
            parse_mode='Markdown'
        )

    async def start_quran_game(self, query, context):
        """مسابقة قرآن"""
        verse = random.choice(self.config.QURAN_VERSES)
        
        await query.edit_message_text(
            f"📚 *مسابقة قرآنية*\n\n"
            f"✨ الآية: {verse['verse']}\n"
            f"📖 السورة: {verse['surah']}\n\n"
            f"💡 حاول حفظ هذه الآية!",
            parse_mode='Markdown'
        )

    async def show_all_games(self, query, context):
        """عرض جميع الألعاب"""
        games_text = "🎮 *جميع الألعاب المتاحة:*\n\n"
        for game in self.config.GAMES_LIST:
            games_text += f"{game['name']} - {game['command']}\n"
        
        await query.edit_message_text(games_text, parse_mode='Markdown')

    async def smart_responses(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ردود ذكية وفكاهية"""
        if not update.message or not update.message.text:
            return
        
        message_text = update.message.text.lower()
        
        # البحث عن ردود خاصة
        for keyword, responses in self.config.RESPONSES.items():
            if keyword in message_text:
                response = random.choice(responses)
                await update.message.reply_text(response)
                return
        
        # ردود عامة لطيفة
        if any(word in message_text for word in ["مرحباً", "أهلاً", "سلام", "صباح", "مساء"]):
            general_response = random.choice(self.config.RESPONSES["general"])
            await update.message.reply_text(general_response)

    async def auto_heart_for_owner(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إرسال قلب تلقائي لرسائل المالك"""
        try:
            chat = update.effective_chat
            user = update.effective_user
            
            # الحصول على قائمة المشرفين
            admins = await context.bot.get_chat_administrators(chat.id)
            
            # البحث عن المالك (الذي لديه status = 'creator')
            owner = None
            for admin in admins:
                if admin.status == 'creator':
                    owner = admin.user
                    break
            
            # إذا كان المرسل هو المالك
            if owner and user.id == owner.id:
                await update.message.reply_text("❤️")
                
                # تسجيل القلب في قاعدة البيانات
                self.db.add_heart_to_owner(chat.id, user.id, update.message.id)
                
                # إحصاء عدد القلوب
                heart_count = self.db.get_owner_hearts_count(chat.id)
                
                # رسالة إضافية بعد عدد معين من القلوب
                if heart_count % 10 == 0:
                    await update.message.reply_text(
                        f"🎉 المالك حصل على {heart_count} قلب! 💖",
                        parse_mode='Markdown'
                    )
                    
        except Exception as e:
            logger.error(f"Error in auto_heart_for_owner: {e}")

    async def welcome_new_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ترحيب متقدم بالأعضاء الجدد"""
        for member in update.message.new_chat_members:
            chat = update.effective_chat
            user = member
            
            # الحصول على معلومات المالك
            admins = await context.bot.get_chat_administrators(chat.id)
            owner = None
            for admin in admins:
                if admin.status == 'creator':
                    owner = admin.user
                    break
            
            # اختيار رسالة ترحيب
            welcome_template = random.choice(self.config.WELCOME_TEMPLATES)
            welcome_text = welcome_template.replace("{user_name}", user.first_name)
            
            # إضافة العضو إلى قاعدة البيانات
            self.db.add_new_member(chat.id, user.id, user.username, user.first_name, user.last_name)
            
            # رسالة الترحيب المتقدمة
            welcome_message = f"""
🎉 *{welcome_text}* 🎉

👤 **معلومات العضو الجديد:**
✨ **الاسم:** {user.first_name} {user.last_name or ''}
📱 **المعرف:** @{user.username or 'غير متوفر'}
🆔 **الرقم:** {user.id}
📅 **تاريخ الانضمام:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

👑 **مالك المجموعة:** @{owner.username if owner else 'غير متوفر'}
🛡️ **البوت:** @{context.bot.username}
🌟 **المجموعة:** {chat.title}

💡 **نصائح للعضو الجديد:**
1️⃣ اقرأ القواعد باستخدام /القواعد
2️⃣ شارك في الألعاب باستخدام /مسابقة
3️⃣ كن نشيطاً ومتفاعلاً
4️⃣ احترم جميع الأعضاء

🎮 **الألعاب المتاحة:** /مسابقة
📚 **مسابقة القرآن:** /قرآن
🛡️ **القواعد:** /القواعد

❤️ *نتمنى لك وقتاً ممتعاً في المجموعة!*
            """
            
            await update.message.reply_text(welcome_message, parse_mode='Markdown')
            
            # إضافة صورة البوت
            try:
                await update.message.reply_photo(
                    photo=open(self.config.BOT_IMAGE_PATH, 'rb'),
                    caption="🛡️ هذا هو بوت الحماية الخاص بمجموعتكم!"
                )
            except:
                await update.message.reply_text("🛡️ بوت الحماية الاحترافي")

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /الإحصائيات"""
        chat = update.effective_chat
        
        # الحصول على إحصائيات المجموعة (هنا يمكنك استدعاء الدالة من قاعدة البيانات)
        stats_text = f"""
📊 *إحصائيات المجموعة:* 📊

🏷️ **اسم المجموعة:** {chat.title}
👥 **عدد الأعضاء:** {chat.get_members_count()}
💬 **عدد الرسائل:** 1000+ (تقديري)
🛡️ **البوت:** @{context.bot.username}
📅 **تاريخ الإنشاء:** غير معروف

🎮 **الألعاب المنشطة:** 10 ألعاب
📚 **مسابقات القرآن:** متاحة
❤️ **قلوب المالك:** {self.db.get_owner_hearts_count(chat.id)}

🌟 **النشاط:** عالي
🛡️ **الحماية:** نشطة
🎉 **الترحيب:** متقدم

💡 **لزيادة الإحصائيات:** كن نشيطاً في المجموعة!
        """
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')

    async def hearts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /قلوب"""
        chat = update.effective_chat
        heart_count = self.db.get_owner_hearts_count(chat.id)
        
        hearts_text = f"""
❤️ *إحصائية قلوب المالك:* ❤️

📊 **عدد القلوب:** {heart_count}
🌟 **المالك:** غير معروف
🕒 **آخر قلب:** غير معروف

💖 **تفسير القلوب:**
• كل قلب = رسالة من المالك
• البوت يرسل قلباً تلقائياً لكل رسالة
• القلوب تعبر عن تقدير البوت للمالك

🎉 **عند كل 10 قلوب:** رسالة تهنئة خاصة
🎊 **عند كل 100 قلب:** ميزة خاصة

💡 **لزيادة القلوب:** المالك يرسل أكثر رسائل!
        """
        
        await update.message.reply_text(hearts_text, parse_mode='Markdown')

    async def rules_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /القواعد"""
        rules_text = """
📜 *قواعد المجموعة:* 📜

1️⃣ **الاحترام:** احترم جميع الأعضاء بدون استثناء
2️⃣ **عدم السب:** لا تستخدم كلمات غير لائقة أو سب
3️⃣ **المشاركة الإيجابية:** شارك بمواضيع مفيدة وجميلة
4️⃣ **عدم التنمر:** لا تتنمر على أي عضو في المجموعة
5️⃣ **عدم الإساءة:** لا تسيء لأي عضو بأي شكل
6️⃣ **التعاون:** تعاون مع الأعضاء في الأنشطة
7️⃣ **الهدوء:** حافظ على هدوء المجموعة
8️⃣ **الالتزام بالقواعد:** اتبع القواعد دائماً

⚠️ **العقوبات:**
• مخالفة القاعدة 1،2،3،4،5: تحذير ثم كتم ثم حظر
• مخالفة القاعدة 6،7،8: تحذير فقط

🎉 **المكافآت:**
• النشاط المستمر: ميزات خاصة
• المشاركة الإيجابية: قلوب وتقدير
• التعاون: نقاط وترقية

💡 **للاستفسار:** راسل المشرفين
        """
        
        await update.message.reply_text(rules_text, parse_mode='Markdown')

    async def is_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """التحقق إذا كان المستخدم مشرف"""
        try:
            user = update.effective_user
            chat = update.effective_chat
            
            admins = await context.bot.get_chat_administrators(chat.id)
            admin_ids = [admin.user.id for admin in admins]
            
            if user.id not in admin_ids:
                return False
            return True
        except Exception as e:
            logger.error(f"Error in is_admin: {e}")
            return False

    async def filter_bad_words(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """فلترة الكلمات السيئة"""
        if not update.message or not update.message.text:
            return
        
        message_text = update.message.text.lower()
        
        for bad_word in self.config.BAD_WORDS:
            if bad_word in message_text:
                try:
                    await update.message.delete()
                    
                    warning_text = f"""
⚠️ *تم حذف الرسالة!* ⚠️

👤 **العضو:** @{update.effective_user.username}
📝 **السبب:** استخدام كلمات غير لائقة
🕒 **التاريخ:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

📜 **القاعدة المخالفة:** عدم السب أو استخدام كلمات غير لائقة
🎯 **العقوبة:** حذف الرسالة + تحذير

💡 **نصيحة:** اقرأ القواعد باستخدام /القواعد
                    """
                    
                    await update.message.reply_text(warning_text, parse_mode='Markdown')
                    break
                    
                except Exception as e:
                    logger.error(f"Error deleting message: {e}")

    def setup_handlers(self, application):
        """إعداد جميع handlers"""
        
        # الأوامر الأساسية
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("مساعدة", self.help_command))
        
        # الأوامر العربية للحماية
        application.add_handler(CommandHandler("حظر", self.ban_command))
        application.add_handler(CommandHandler("طرد", self.kick_command))
        application.add_handler(CommandHandler("كتم", self.mute_command))
        application.add_handler(CommandHandler("قفل", self.lock_command))
        application.add_handler(CommandHandler("فتح", self.unlock_command))
        
        # الأوامر العربية للألعاب
        application.add_handler(CommandHandler("مسابقة", self.games_command))
        application.add_handler(CommandHandler("نرد", self.games_command))
        application.add_handler(CommandHandler("سلة", self.games_command))
        application.add_handler(CommandHandler("قرآن", self.games_command))
        
        # الأوامر العربية للإحصائيات
        application.add_handler(CommandHandler("الإحصائيات", self.stats_command))
        application.add_handler(CommandHandler("قلوب", self.hearts_command))
        application.add_handler(CommandHandler("القواعد", self.rules_command))
        
        # معالجة الألعاب
        application.add_handler(CallbackQueryHandler(self.game_callback_handler, pattern="^game_"))
        
        # الردود الذكية
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.smart_responses
        ))
        
        # قلب للمالك
        application.add_handler(MessageHandler(
            filters.ALL & ~filters.COMMAND,
            self.auto_heart_for_owner
        ))
        
        # فلترة الكلمات السيئة
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.filter_bad_words
        ))
        
        # الترحيب بالأعضاء الجدد
        application.add_handler(MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            self.welcome_new_member
        ))
        
        # تسجيل الرسائل للإحصائيات
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.record_message
        ))
    
    async def record_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تسجيل الرسالة للإحصائيات"""
        if update.effective_chat and update.effective_user:
            self.db.record_message(update.effective_chat.id, update.effective_user.id)

    def run(self):
        """تشغيل البوت"""
        if not self.config.BOT_TOKEN:
            logger.error("❌ BOT_TOKEN غير موجود في ملف .env!")
            return
        
        application = Application.builder().token(self.config.BOT_TOKEN).build()
        
        self.setup_handlers(application)
        
        logger.info("🚀 بدء تشغيل بوت حماية المجموعات الاحترافي...")
        logger.info(f"📊 عدد ردود 'مرام': {len(self.config.RESPONSES['مرام'])}")
        logger.info(f"🎮 عدد الألعاب: {len(self.config.GAMES_LIST)}")
        logger.info(f"📚 عدد الآيات القرآنية: {len(self.config.QURAN_VERSES)}")
        
        application.run_polling()

if __name__ == '__main__':
    bot = AdvancedGroupProtectionBot()
    bot.run()
