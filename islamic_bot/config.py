# config.py - إعدادات بوت القنوات الدينية

import os
from dotenv import load_dotenv
from datetime import time

load_dotenv()

class BotConfig:
    """إعدادات البوت الأساسية"""
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    
    # معرفات المطورين
    ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
    
    # قاعدة البيانات
    DATABASE_PATH = os.getenv("DATABASE_PATH", "islamic_channels.db")

class PrayerTimes:
    """أوقات الصلاة والأذكار"""
    # أوقات نشر الأذكار (بالنظام 24 ساعة)
    MORNING_ADKAR_TIME = time(6, 0)    # 6:00 صباحاً
    EVENING_ADKAR_TIME = time(18, 0)   # 6:00 مساءً
    SLEEP_ADKAR_TIME = time(22, 0)     # 10:00 مساءً
    
    # أوقات التسبيح اليومي
    TASBIH_INTERVAL_HOURS = 3  # كل 3 ساعات
    
    # وقت الآية اليومية
    DAILY_VERSE_TIME = time(8, 0)  # 8:00 صباحاً
    
    # وقت الحديث اليومي
    DAILY_HADITH_TIME = time(12, 0)  # 12:00 ظهراً

class ContentLimits:
    """حدود المحتوى"""
    MAX_CHANNELS_PER_USER = 10  # أقصى عدد قنوات لكل مستخدم
    MAX_POSTS_PER_DAY = 50      # أقصى عدد منشورات يومياً
    ADKAR_COUNT_MORNING = 30    # عدد أذكار الصباح
    ADKAR_COUNT_EVENING = 30    # عدد أذكار المساء
    TASBIH_COUNT = 33           # عدد التسبيحات

class DatabaseConfig:
    """إعدادات قاعدة البيانات"""
    TABLES = {
        'channels': '''
            CREATE TABLE IF NOT EXISTS channels (
                channel_id INTEGER PRIMARY KEY,
                channel_username TEXT,
                channel_title TEXT,
                owner_id INTEGER,
                owner_username TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_post_time TIMESTAMP,
                posts_count INTEGER DEFAULT 0,
                adkar_enabled INTEGER DEFAULT 1,
                tasbih_enabled INTEGER DEFAULT 1,
                verse_enabled INTEGER DEFAULT 1,
                hadith_enabled INTEGER DEFAULT 1
            )
        ''',
        'adkar_posts': '''
            CREATE TABLE IF NOT EXISTS adkar_posts (
                post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER,
                post_type TEXT,  -- morning, evening, sleep, tasbih
                content TEXT,
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_id INTEGER
            )
        ''',
        'daily_content': '''
            CREATE TABLE IF NOT EXISTS daily_content (
                content_id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER,
                content_type TEXT,  -- verse, hadith
                content_text TEXT,
                source TEXT,
                posted_date DATE DEFAULT CURRENT_DATE,
                message_id INTEGER
            )
        ''',
        'statistics': '''
            CREATE TABLE IF NOT EXISTS statistics (
                stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER,
                date DATE DEFAULT CURRENT_DATE,
                posts_count INTEGER DEFAULT 0,
                adkar_count INTEGER DEFAULT 0,
                tasbih_count INTEGER DEFAULT 0,
                verses_count INTEGER DEFAULT 0,
                hadith_count INTEGER DEFAULT 0
            )
        ''',
        'scheduled_tasks': '''
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER,
                task_type TEXT,
                scheduled_time TIMESTAMP,
                is_executed INTEGER DEFAULT 0,
                executed_at TIMESTAMP
            )
        '''
    }

class IslamicContent:
    """محتوى إسلامي ثابت"""
    
    # أذكار الصباح
    MORNING_ADKAR = [
        "أصبحنا وأصبح الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له",
        "اللهم بك أصبحنا وبك أمسينا وبك نحيا وبك نموت وإليك النشور",
        "سبحان الله وبحمده عدد خلقه ورضا نفسه وزنة عرشه ومداد كلماته",
        "اللهم عافني في بدني، اللهم عافني في سمعي، اللهم عافني في بصري",
        "يا حي يا قيوم برحمتك أستغيث، أصلح لي شأني كله ولا تكلني إلى نفسي طرفة عين",
        "أعوذ بكلمات الله التامات من شر ما خلق",
        "بسم الله الذي لا يضر مع اسمه شيء في الأرض ولا في السماء وهو السميع العليم",
        "رضيت بالله رباً وبالإسلام ديناً وبمحمد صلى الله عليه وسلم نبياً",
        "اللهم إني أسألك العفو والعافية في الدنيا والآخرة",
        "حسبي الله لا إله إلا هو عليه توكلت وهو رب العرش العظيم"
    ]
    
    # أذكار المساء
    EVENING_ADKAR = [
        "أمسينا وأمسى الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له",
        "اللهم بك أمسينا وبك أصبحنا وبك نحيا وبك نموت وإليك المصير",
        "أعوذ بكلمات الله التامات من شر ما خلق",
        "بسم الله الذي لا يضر مع اسمه شيء في الأرض ولا في السماء وهو السميع العليم",
        "اللهم إني أمسيت أشهدك وأشهد حملة عرشك وملائكتك وجميع خلقك أنك أنت الله لا إله إلا أنت",
        "أمسينا على الفطرة وعلى كلمة الإسلام وعلى دين النبي محمد صلى الله عليه وسلم",
        "اللهم ما أمسى بي من نعمة أو بأحد من خلقك فمنك وحدك لا شريك لك",
        "يا مسهل الشديد ويا ملين الحديد ويا منجز الوعيد",
        "حسبي الله لا إله إلا هو عليه توكلت وهو رب العرش العظيم",
        "أعوذ بوجه الله الكريم وكلماته التامات من شر ما ينزل من السماء"
    ]
    
    # أذكار النوم
    SLEEP_ADKAR = [
        "باسمك ربي وضعت جنبي وبك أرفعه إن أمسكت نفسي فارحمها وإن أرسلتها فاحفظها",
        "اللهم قني عذابك يوم تبعث عبادك",
        "اللهم باسمك أموت وأحيا",
        "سبحان الله (33 مرة)، الحمد لله (33 مرة)، الله أكبر (33 مرة)",
        "آية الكرسي قبل النوم",
        "آخر آيتين من سورة البقرة",
        "قل هو الله أحد والمعوذتين"
    ]
    
    # التسبيحات
    TASBIHAT = [
        "سبحان الله",
        "الحمد لله",
        "الله أكبر",
        "لا إله إلا الله",
        "سبحان الله وبحمده",
        "أستغفر الله",
        "لا حول ولا قوة إلا بالله",
        "ما شاء الله كان",
        "بارك الله لك",
        "جزاك الله خيراً"
    ]
    
    # آيات قرآنية مختارة
    QURAN_VERSES = [
        {"verse": "وَقُل رَّبِّ زِدْنِي عِلْمًا", "surah": "طه: 114"},
        {"verse": "فَاذْكُرُونِي أَذْكُرْكُمْ وَاشْكُرُوا لِي وَلَا تَكْفُرُونِ", "surah": "البقرة: 152"},
        {"verse": "وَبَشِّرِ الصَّابِرِينَ", "surah": "البقرة: 155"},
        {"verse": "إِنَّ اللَّهَ مَعَ الصَّابِرِينَ", "surah": "البقرة: 153"},
        {"verse": "وَلَسَوْفَ يُعْطِيكَ رَبُّكَ فَتَرْضَىٰ", "surah": "الضحى: 8"},
        {"verse": "أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ", "surah": "الرعد: 28"},
        {"verse": "وَاسْتَعِينُوا بِالصَّبْرِ وَالصَّلَاةِ", "surah": "البقرة: 45"},
        {"verse": "إِنَّ الصَّلَاةَ تَنْهَىٰ عَنِ الْفَحْشَاءِ وَالْمُنكَرِ", "surah": "العنكبوت: 45"},
        {"verse": "وَأَقِمِ الصَّلَاةَ إِنَّ الصَّلَاةَ تَنْهَىٰ عَنِ الْفَحْشَاءِ وَالْمُنكَرِ", "surah": "العنكبوت: 45"},
        {"verse": "وَذَكِّرْ فَإِنَّ الذِّكْرَىٰ تَنفَعُ الْمُؤْمِنِينَ", "surah": "الذاريات: 55"}
    ]
    
    # أحاديث نبوية
    HADITHS = [
        {"text": "قال رسول الله ﷺ: «خَيْرُكُمْ مَنْ تَعَلَّمَ الْقُرْآنَ وَعَلَّمَهُ»", "source": "رواه البخاري"},
        {"text": "قال رسول الله ﷺ: «الدِّينُ النَّصِيحَةُ»", "source": "رواه مسلم"},
        {"text": "قال رسول الله ﷺ: «مَنْ صَامَ رَمَضَانَ إِيمَانًا وَاحْتِسَابًا غُفِرَ لَهُ مَا تَقَدَّمَ مِنْ ذَنْبِهِ»", "source": "متفق عليه"},
        {"text": "قال رسول الله ﷺ: «الصِّيَامُ جُنَّةٌ»", "source": "متفق عليه"},
        {"text": "قال رسول الله ﷺ: «مَنْ صَلَّى عَلَيَّ صَلَاةً صَلَّى اللَّهُ عَلَيْهِ بِهَا عَشْرًا»", "source": "رواه مسلم"},
        {"text": "قال رسول الله ﷺ: «الْكَلِمَةُ الطَّيِّبَةُ صَدَقَةٌ»", "source": "متفق عليه"},
        {"text": "قال رسول الله ﷺ: «تبسّمك في وجه أخيك صدقة»", "source": "رواه الترمذي"},
        {"text": "قال رسول الله ﷺ: «مَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الْآخِرِ فَلْيَقُلْ خَيْرًا أَوْ لِيَصْمُتْ»", "source": "متفق عليه"},
        {"text": "قال رسول الله ﷺ: «لا يُؤْمِنُ أَحَدُكُمْ حَتَّى يُحِبَّ لِأَخِيهِ مَا يُحِبُّ لِنَفْسِهِ»", "source": "متفق عليه"},
        {"text": "قال رسول الله ﷺ: «الْمُسْلِمُ مَنْ سَلِمَ الْمُسْلِمُونَ مِنْ لِسَانِهِ وَيَدِهِ»", "source": "رواه البخاري"}
    ]
