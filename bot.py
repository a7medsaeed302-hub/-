import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from supabase import create_client, Client
from config import SecurityConfig, MonitoringConfig

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

supabase_url = os.getenv("VITE_SUPABASE_URL")
supabase_key = os.getenv("VITE_SUPABASE_SUPABASE_ANON_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("اضافة حساب للحماية", callback_data='add_account')],
        [InlineKeyboardButton("عرض الحسابات المحمية", callback_data='view_accounts')],
        [InlineKeyboardButton("التنبيهات الامنية", callback_data='view_alerts')],
        [InlineKeyboardButton("الاعدادات", callback_data='settings')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = f"""
مرحبا {user.first_name}!

هذا البوت يوفر حماية متقدمة لحساباتك على مختلف المنصات:
- مراقبة محاولات تسجيل الدخول
- كشف الانشطة المشبوهة
- تنبيهات فورية عند اكتشاف تهديدات
- حماية ضد الاختراق والوصول غير المصرح

اختر احد الخيارات للبدء:
"""

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'add_account':
        await add_account_menu(query)
    elif query.data == 'view_accounts':
        await view_accounts(query)
    elif query.data == 'view_alerts':
        await view_alerts(query)
    elif query.data == 'settings':
        await settings_menu(query)
    elif query.data.startswith('platform_'):
        platform = query.data.split('_')[1]
        context.user_data['selected_platform'] = platform
        await query.edit_message_text(
            f"تم اختيار منصة {platform}\n\n"
            "الرجاء ارسال اسم المستخدم او البريد الالكتروني للحساب:"
        )
    elif query.data == 'back_main':
        keyboard = [
            [InlineKeyboardButton("اضافة حساب للحماية", callback_data='add_account')],
            [InlineKeyboardButton("عرض الحسابات المحمية", callback_data='view_accounts')],
            [InlineKeyboardButton("التنبيهات الامنية", callback_data='view_alerts')],
            [InlineKeyboardButton("الاعدادات", callback_data='settings')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("القائمة الرئيسية:", reply_markup=reply_markup)

async def add_account_menu(query):
    keyboard = [
        [InlineKeyboardButton("فيسبوك", callback_data='platform_facebook')],
        [InlineKeyboardButton("انستغرام", callback_data='platform_instagram')],
        [InlineKeyboardButton("تويتر", callback_data='platform_twitter')],
        [InlineKeyboardButton("تيك توك", callback_data='platform_tiktok')],
        [InlineKeyboardButton("رجوع", callback_data='back_main')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("اختر المنصة التي تريد حمايتها:", reply_markup=reply_markup)

async def view_accounts(query):
    user_id = query.from_user.id

    try:
        response = supabase.table('accounts').select('*').eq('user_id', user_id).execute()
        accounts = response.data

        if not accounts:
            await query.edit_message_text(
                "لا توجد حسابات محمية حاليا.\n\n"
                "استخدم /start لاضافة حساب جديد."
            )
            return

        text = "الحسابات المحمية:\n\n"
        for acc in accounts:
            status_emoji = "🟢" if acc['security_level'] >= 3 else "🟡" if acc['security_level'] == 2 else "🔴"
            text += f"{status_emoji} {acc['platform']}\n"
            text += f"المستخدم: {acc['username']}\n"
            text += f"مستوى الامان: {acc['security_level']}/4\n"
            text += f"المصادقة الثنائية: {'مفعلة ✓' if acc['is_2fa_enabled'] else 'غير مفعلة ✗'}\n\n"

        keyboard = [[InlineKeyboardButton("رجوع", callback_data='back_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Error viewing accounts: {e}")
        await query.edit_message_text("حدث خطأ اثناء عرض الحسابات.")

async def view_alerts(query):
    user_id = query.from_user.id

    try:
        accounts_response = supabase.table('accounts').select('id').eq('user_id', user_id).execute()
        account_ids = [acc['id'] for acc in accounts_response.data]

        if not account_ids:
            await query.edit_message_text("لا توجد حسابات لعرض التنبيهات الخاصة بها.")
            return

        alerts_response = supabase.table('security_alerts').select('*').in_('account_id', account_ids).order('created_at', desc=True).limit(10).execute()
        alerts = alerts_response.data

        if not alerts:
            await query.edit_message_text(
                "لا توجد تنبيهات امنية حاليا.\n\n"
                "هذا يعني ان حساباتك آمنة!"
            )
            return

        text = "التنبيهات الامنية الاخيرة:\n\n"
        for alert in alerts:
            threat_color = SecurityConfig.THREAT_LEVELS[alert['threat_level']]['color']
            threat_name = SecurityConfig.THREAT_LEVELS[alert['threat_level']]['name']

            text += f"{threat_color} تهديد {threat_name}\n"
            text += f"النوع: {alert['alert_type']}\n"
            text += f"الرسالة: {alert['message']}\n"
            text += f"التاريخ: {alert['created_at'][:19]}\n"
            text += f"الحالة: {'تم الحل ✓' if alert['is_resolved'] else 'قيد المعالجة'}\n\n"

        keyboard = [[InlineKeyboardButton("رجوع", callback_data='back_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Error viewing alerts: {e}")
        await query.edit_message_text("حدث خطأ اثناء عرض التنبيهات.")

async def settings_menu(query):
    keyboard = [
        [InlineKeyboardButton("تفعيل المصادقة الثنائية", callback_data='enable_2fa')],
        [InlineKeyboardButton("رفع مستوى الامان", callback_data='increase_security')],
        [InlineKeyboardButton("حظر عناوين IP", callback_data='block_ips')],
        [InlineKeyboardButton("رجوع", callback_data='back_main')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("اعدادات الحماية:", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data

    if 'selected_platform' in user_data:
        platform = user_data['selected_platform']
        username = update.message.text
        user_id = update.effective_user.id

        try:
            account_data = {
                'user_id': user_id,
                'platform': platform,
                'username': username,
                'is_2fa_enabled': False,
                'security_level': 1,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            supabase.table('accounts').insert(account_data).execute()

            del user_data['selected_platform']

            await update.message.reply_text(
                f"تم اضافة حساب {platform} بنجاح!\n\n"
                f"اسم المستخدم: {username}\n"
                "مستوى الامان الحالي: 1/4\n\n"
                "نوصي بـ:\n"
                "1. تفعيل المصادقة الثنائية\n"
                "2. رفع مستوى الامان\n"
                "3. مراجعة الاعدادات"
            )

        except Exception as e:
            logger.error(f"Error adding account: {e}")
            await update.message.reply_text("حدث خطأ اثناء اضافة الحساب. حاول مرة اخرى.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    application = Application.builder().token(SecurityConfig.BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
