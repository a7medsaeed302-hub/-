import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Client-Info, Apikey",
};

const BOT_TOKEN = "8631971512:AAHyuDK3Sr9tn14CTBfzDVWbamxfAZdcs7c";
const TELEGRAM_API = `https://api.telegram.org/bot${BOT_TOKEN}`;

interface TelegramUpdate {
  message?: {
    chat: { id: number };
    text?: string;
    from?: { first_name: string; id: number };
  };
  callback_query?: {
    id: string;
    data?: string;
    message?: {
      chat: { id: number };
      message_id: number;
    };
    from?: { first_name: string; id: number };
  };
}

async function sendMessage(chatId: number, text: string, replyMarkup?: any) {
  const response = await fetch(`${TELEGRAM_API}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text: text,
      reply_markup: replyMarkup,
      parse_mode: "HTML",
    }),
  });
  return response.json();
}

async function editMessage(chatId: number, messageId: number, text: string, replyMarkup?: any) {
  const response = await fetch(`${TELEGRAM_API}/editMessageText`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      message_id: messageId,
      text: text,
      reply_markup: replyMarkup,
      parse_mode: "HTML",
    }),
  });
  return response.json();
}

async function answerCallbackQuery(callbackQueryId: string) {
  await fetch(`${TELEGRAM_API}/answerCallbackQuery`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ callback_query_id: callbackQueryId }),
  });
}

function getMainKeyboard() {
  return {
    inline_keyboard: [
      [{ text: "اضافة حساب للحماية", callback_data: "add_account" }],
      [{ text: "عرض الحسابات المحمية", callback_data: "view_accounts" }],
      [{ text: "التنبيهات الامنية", callback_data: "view_alerts" }],
      [{ text: "الاعدادات", callback_data: "settings" }],
    ],
  };
}

function getPlatformKeyboard() {
  return {
    inline_keyboard: [
      [{ text: "فيسبوك", callback_data: "platform_facebook" }],
      [{ text: "انستغرام", callback_data: "platform_instagram" }],
      [{ text: "تويتر", callback_data: "platform_twitter" }],
      [{ text: "تيك توك", callback_data: "platform_tiktok" }],
      [{ text: "رجوع", callback_data: "back_main" }],
    ],
  };
}

async function handleStart(chatId: number, firstName: string) {
  const welcomeText = `مرحبا ${firstName}!

هذا البوت يوفر حماية متقدمة لحساباتك على مختلف المنصات:
- مراقبة محاولات تسجيل الدخول
- كشف الانشطة المشبوهة
- تنبيهات فورية عند اكتشاف تهديدات
- حماية ضد الاختراق والوصول غير المصرح

اختر احد الخيارات للبدء:`;

  await sendMessage(chatId, welcomeText, getMainKeyboard());
}

async function handleCallback(callbackQuery: any) {
  const chatId = callbackQuery.message.chat.id;
  const messageId = callbackQuery.message.message_id;
  const data = callbackQuery.data;

  await answerCallbackQuery(callbackQuery.id);

  if (data === "add_account") {
    await editMessage(
      chatId,
      messageId,
      "اختر المنصة التي تريد حمايتها:",
      getPlatformKeyboard()
    );
  } else if (data === "view_accounts") {
    const text = `الحسابات المحمية:

لا توجد حسابات محمية حاليا.

استخدم /start لاضافة حساب جديد.`;
    await editMessage(chatId, messageId, text, {
      inline_keyboard: [[{ text: "رجوع", callback_data: "back_main" }]],
    });
  } else if (data === "view_alerts") {
    const text = `التنبيهات الامنية:

لا توجد تنبيهات امنية حاليا.

هذا يعني ان حساباتك آمنة!`;
    await editMessage(chatId, messageId, text, {
      inline_keyboard: [[{ text: "رجوع", callback_data: "back_main" }]],
    });
  } else if (data === "settings") {
    const keyboard = {
      inline_keyboard: [
        [{ text: "تفعيل المصادقة الثنائية", callback_data: "enable_2fa" }],
        [{ text: "رفع مستوى الامان", callback_data: "increase_security" }],
        [{ text: "حظر عناوين IP", callback_data: "block_ips" }],
        [{ text: "رجوع", callback_data: "back_main" }],
      ],
    };
    await editMessage(chatId, messageId, "اعدادات الحماية:", keyboard);
  } else if (data.startsWith("platform_")) {
    const platform = data.replace("platform_", "");
    await editMessage(
      chatId,
      messageId,
      `تم اختيار منصة ${platform}\n\nالرجاء ارسال اسم المستخدم او البريد الالكتروني للحساب:`
    );
  } else if (data === "back_main") {
    await editMessage(chatId, messageId, "القائمة الرئيسية:", getMainKeyboard());
  }
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, {
      status: 200,
      headers: corsHeaders,
    });
  }

  try {
    const update: TelegramUpdate = await req.json();

    if (update.message) {
      const chatId = update.message.chat.id;
      const text = update.message.text || "";
      const firstName = update.message.from?.first_name || "User";

      if (text === "/start") {
        await handleStart(chatId, firstName);
      } else {
        await sendMessage(chatId, "شكرا لك! استخدم /start لعرض القائمة الرئيسية.");
      }
    } else if (update.callback_query) {
      await handleCallback(update.callback_query);
    }

    return new Response(JSON.stringify({ ok: true }), {
      headers: {
        ...corsHeaders,
        "Content-Type": "application/json",
      },
    });
  } catch (error) {
    console.error("Error:", error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: {
        ...corsHeaders,
        "Content-Type": "application/json",
      },
    });
  }
});
