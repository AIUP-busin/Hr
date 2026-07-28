import os
import logging
import requests
import sqlite3
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
ADMIN_USERNAME = "mr_jalilov7"
ADMIN_CHAT_ID = 206004279

# ===================== TIL SOZLAMALARI =====================
TEXTS = {
    "uz": {
        "welcome": "Salom, {}!\n\nOttimo Cafe HR botiga xush kelibsiz!\n\nQuyidagi bo'limlardan birini tanlang:",
        "menu": [
            ["👷 Ishchi qabul qilish", "🌐 Til tanlash", "⏰ Ish vaqti"],
            ["📊 Ish ma'lumotlari", "🤝 Xodimlar muammolari", "📍 Filiallar"],
            ["📞 Qo'llab-quvvatlash", "👨‍💼 Admin", "🗑️ Suhbatni tozalash"]
        ],
        "savol_javob": "Ottimo Cafe haqida istalgan savolingizni yozing!\n\nMasalan:\n— Filiallar qayerda?\n— Ish vaqti qanday?\n— Qanday hujjatlar kerak?",
        "til_tanlash": "Tilni tanlang / Выберите язык / Choose language:",
        "til_tanlash_menu": [["🇺🇿 O'zbek tili"], ["🇷🇺 Русский язык"], ["🇬🇧 English"]],
        "til_tanlandi": "O'zbek tili tanlandi!",
        "admin": "Admin bilan bog'lanish:\n\nTelegram: @Ottimo_hr\nTelefon: +998 99 060 33 53\n\nIsh vaqti: 09:00 — 18:00",
        "yordam": "Menyudan bo'lim tanlang yoki istalgan savolingizni yozing!",
        "tozalandi": "Suhbat tozalandi!",
        "xatolik": "Hozirda texnik nosozlik yuz berdi. Iltimos, @Ottimo_hr ga murojaat qiling.",
        "filiallar": (
            "OTTIMO CAFE FILIALLARI\n\n"
            "1. Nukus kinoteatri yonida\n"
            "   Toshkent, Shifer ko'chasi, 71\n"
            "   https://yandex.uz/maps/org/144255252741/?ll=69.218418%2C41.350783&z=16.54\n\n"
            "2. Parus ostida\n"
            "   Toshkent, Katartal ko'chasi, 60A/1\n"
            "   https://yandex.uz/maps/org/45535920435/?ll=69.211087%2C41.292054&z=16.54\n\n"
            "3. Talant International School ro'parasida\n"
            "   Toshkent, Mirzo Ulug'bek tumani, Buyuk Ipak Yo'li, 31\n"
            "   https://yandex.uz/maps/10335/tashkent/?ll=69.293312%2C41.313048&mode=poi&poi%5Bpoint%5D=69.293235%2C41.313153&poi%5Buri%5D=ymapsbm1%3A%2F%2Forg%3Foid%3D67180596093&z=19.79\n\n"
            "Telefon: +998 99 060 33 53\n"
            "Telegram: @Ottimo_hr"
        ),
        "qollab": "Qo'llab-quvvatlash:\n\nTelefon: +998 99 060 33 53\nTelegram: @Ottimo_hr",
        "anketa_boshlash": "OTTIMO CAFE — ISH UCHUN ARIZA\n\nJami {} ta savol.\nBekor qilish: /bekor\n\n",
        "bekor": "Ariza bekor qilindi.",
        "tasdiqlash": "Tasdiqlaysizmi?",
        "tasdiq_btn": "✅ Tasdiqlash",
        "bekor_btn": "❌ Bekor qilish",
        "rahmat": "Anketani to'ldirganingiz uchun katta rahmat!\n\nMa'lumotlaringiz muvaffaqiyatli saqlandi.\n\nKo'rib chiqish muddati: 1-3 ish kuni\n@Ottimo_hr tez orada siz bilan bog'lanadi\n\nOmad tilaymiz!\n\nMurojaat uchun: https://t.me/ottimo_uz",
        "bekor_xabar": "Ariza bekor qilindi.",
        "bosh_menyu": "Bosh menyu:",
        "anketa_tayyor": "ANKETANGIZ TAYYOR! Iltimos, tekshirib ko'ring:\n\n",
        "ish_vaqti": "ISH VAQTI\n\n☀️ 1-smena: 07:30 — 16:30 (kunduzi)\n🌙 2-smena: 16:00 — 24:00 (kechki payt)\n\nJadval har dushanba yangilanadi\nSmena o'zgarishi 1 kun oldin xabar beriladi\n\n⚠️ Kechikish jarima: 50 000 so'm\n🍽 Har smenada bepul ovqat",
        "ish_malumot": "OTTIMO CAFE HAQIDA\n\nOttimo — Toshkentdagi zamonaviy va qulay kafe.\nMaqsadimiz — mijozlarga yoqimli muhit va sifatli xizmat ko'rsatish.\n\n✅ Rasmiy mehnat shartnomasi\n✅ Maosh har 10 kunda to'lanadi\n✅ Har smenada bepul ovqat\n✅ Karyera o'sishi imkoniyati\n✅ Do'stona jamoa (25+ xodim)\n✅ Barqaror ish joyi\n\nBo'sh ish o'rinlari:\n☕ Barista\n💳 Kassir\n🍰 Konditer-sotuvchi\n\nFiliallar:\n1. Nukus kinoteatri yonida — Shifer ko'chasi, 71\n2. Parus ostida — Katartal ko'chasi, 60A/1\n3. Talant school ro'parasida — Buyuk Ipak Yo'li, 31\n\nTelefon: +998 99 060 33 53 | @Ottimo_hr",
        "xodimlar_muammo": "XODIMLAR MUAMMOLARINI HAL QILISH\n\n1-qadam: Hamkasbingiz bilan muhokama qiling\n2-qadam: Smena menejeriga murojaat qiling\n3-qadam: HR ga yozing: @Ottimo_hr\n\n⚠️ Ish joyida janjallashish man etiladi\n\n✅ Har murojaat ko'rib chiqiladi\n\nTelefon: +998 99 060 33 53",
        "mehnat_qonun": "MEHNAT QONUNLARI\n\n✅ HUQUQLAR:\n• Belgilangan maosh o'z vaqtida to'lanadi\n• Yillik mehnat ta'tili (15-21 kun)\n• Kasallik varag'i hisobga olinadi\n• Ijtimoiy sug'urta\n\n⚠️ MAJBURIYATLAR:\n• Ish tartibiga rioya qilish\n• O'z vaqtida kelish\n\n🚫 MAN ETILADI:\n• Chekish\n• Alkogol\n• Mijozga qo'pollik\n\nTelegram: @Ottimo_hr",
        "smena_menu": [["☀️ Kunduzi (07:30-16:30)"], ["🌙 Kechki payt (16:00-24:00)"], ["🔄 Ikkalasi ham bo'ladi"]],
        "system_prompt": "Sen Ottimo Cafe uchun HR agentisan. Faqat o'zbek tilida javob ber. Faqat Ottimo Cafe haqidagi savollarga javob ber. Boshqa savollarga: 'Kechirasiz, men faqat Ottimo Cafe haqida javob bera olaman' de.\n\nOttimo haqida:\n- 3 ta filial: Shifer 71, Katartal 60A/1, Buyuk Ipak Yo'li 31\n- Bo'sh o'rinlar: Barista, Kassir, Konditer\n- Ish vaqti: 07:30-16:30 va 16:00-24:00\n- Yosh: 20-35, Rus tili shart\n- Maosh har 10 kunda\n- Telefon: +998 99 060 33 53, @Ottimo_hr\nDo'stona va ijodiy javob ber.",
    },
    "ru": {
        "welcome": "Привет, {}!\n\nДобро пожаловать в HR бот Ottimo Cafe!\n\nВыберите один из разделов:",
        "menu": [
            ["👷 Приём на работу", "🌐 Выбор языка", "⏰ Рабочее время"],
            ["📊 О работе", "🤝 Проблемы сотрудников", "📍 Филиалы"],
            ["📞 Поддержка", "👨‍💼 Админ", "🗑️ Очистить чат"]
        ],
        "savol_javob": "Задайте любой вопрос об Ottimo Cafe!\n\nНапример:\n— Где находятся филиалы?\n— Какой график работы?\n— Какие документы нужны?",
        "til_tanlash": "Tilni tanlang / Выберите язык / Choose language:",
        "til_tanlash_menu": [["🇺🇿 O'zbek tili"], ["🇷🇺 Русский язык"], ["🇬🇧 English"]],
        "til_tanlandi": "Выбран русский язык!",
        "admin": "Связаться с администратором:\n\nTelegram: @Ottimo_hr\nТелефон: +998 99 060 33 53\n\nРабочее время: 09:00 — 18:00",
        "yordam": "Выберите раздел из меню или задайте вопрос!",
        "tozalandi": "Чат очищен!",
        "xatolik": "Произошла техническая ошибка. Обратитесь к @Ottimo_hr.",
        "filiallar": "ФИЛИАЛЫ OTTIMO CAFE\n\n1. У кинотеатра Нукус\n   Ташкент, ул. Шифернур, 71\n   https://yandex.uz/maps/org/144255252741/?ll=69.218418%2C41.350783&z=16.54\n\n2. Под Парусом\n   Ташкент, ул. Катартал, 60А/1\n   https://yandex.uz/maps/org/45535920435/?ll=69.211087%2C41.292054&z=16.54\n\n3. Напротив Talant International School\n   Ташкент, Мирзо-Улугбекский р-н, Buyuk Ipak Yoli, 31\n   https://yandex.uz/maps/10335/tashkent/?ll=69.293312%2C41.313048&mode=poi&poi%5Bpoint%5D=69.293235%2C41.313153&poi%5Buri%5D=ymapsbm1%3A%2F%2Forg%3Foid%3D67180596093&z=19.79\n\nТел: +998 99 060 33 53\nTelegram: @Ottimo_hr",
        "qollab": "Служба поддержки:\n\nТелефон: +998 99 060 33 53\nTelegram: @Ottimo_hr",
        "anketa_boshlash": "OTTIMO CAFE — АНКЕТА ДЛЯ ТРУДОУСТРОЙСТВА\n\nВсего {} вопросов.\nДля отмены напишите /bekor\n\n",
        "bekor": "Анкета отменена.",
        "tasdiqlash": "Подтверждаете?",
        "tasdiq_btn": "✅ Подтвердить",
        "bekor_btn": "❌ Отменить",
        "rahmat": "Большое спасибо за заполнение анкеты!\n\nВаши данные успешно сохранены.\n\nСрок рассмотрения: 1-3 рабочих дня\n@Ottimo_hr свяжется с вами в ближайшее время\n\nЖелаем удачи!\n\nДля связи: https://t.me/ottimo_uz",
        "bekor_xabar": "Анкета отменена.",
        "bosh_menyu": "Главное меню:",
        "anketa_tayyor": "ВАША АНКЕТА ГОТОВА! Пожалуйста, проверьте:\n\n",
        "ish_vaqti": "РАБОЧЕЕ ВРЕМЯ\n\n☀️ 1-смена: 07:30 — 16:30 (дневная)\n🌙 2-смена: 16:00 — 24:00 (вечерняя)\n\nГрафик обновляется каждый понедельник\nОб изменениях сообщается за 1 день\n\n⚠️ Штраф за опоздание: 50 000 сум\n🍽 Бесплатное питание в каждую смену",
        "ish_malumot": "ОБ OTTIMO CAFE\n\nOttimo — современное кафе в Ташкенте.\nНаша цель — создать приятную атмосферу и качественный сервис.\n\n✅ Официальный трудовой договор\n✅ Зарплата каждые 10 дней\n✅ Бесплатное питание\n✅ Карьерный рост\n✅ Дружный коллектив (25+ сотрудников)\n\nВакансии:\n☕ Бариста\n💳 Кассир\n🍰 Кондитер-продавец\n\nФилиалы:\n1. У кинотеатра Нукус — ул. Шифернур, 71\n2. Под Парусом — ул. Катартал, 60А/1\n3. Напротив Talant school — Buyuk Ipak Yoli, 31\n\nТел: +998 99 060 33 53 | @Ottimo_hr",
        "xodimlar_muammo": "РЕШЕНИЕ ПРОБЛЕМ СОТРУДНИКОВ\n\nШаг 1: Поговорите с коллегой\nШаг 2: Обратитесь к менеджеру смены\nШаг 3: Напишите в HR: @Ottimo_hr\n\n⚠️ Конфликты на рабочем месте запрещены\n\n✅ Каждое обращение рассматривается\n\nТел: +998 99 060 33 53",
        "mehnat_qonun": "ТРУДОВОЕ ЗАКОНОДАТЕЛЬСТВО\n\n✅ ПРАВА:\n• Зарплата выплачивается вовремя\n• Ежегодный отпуск (15-21 день)\n• Больничный лист\n• Социальное страхование\n\n⚠️ ОБЯЗАННОСТИ:\n• Соблюдение трудового распорядка\n• Своевременное появление на работе\n\n🚫 ЗАПРЕЩЕНО:\n• Курение\n• Алкоголь\n• Грубость с клиентами\n\nTelegram: @Ottimo_hr",
        "smena_menu": [["☀️ Дневная (07:30-16:30)"], ["🌙 Вечерняя (16:00-24:00)"], ["🔄 Любая смена"]],
        "system_prompt": "Ты HR-ассистент Ottimo Cafe. Отвечай только на русском языке. Отвечай только на вопросы об Ottimo Cafe. На другие вопросы говори: 'Извините, я могу отвечать только на вопросы об Ottimo Cafe'.\n\nОб Ottimo:\n- 3 филиала: Шифернур 71, Катартал 60А/1, Buyuk Ipak Yoli 31\n- Вакансии: Бариста, Кассир, Кондитер\n- График: 07:30-16:30 и 16:00-24:00\n- Возраст: 20-35, знание русского обязательно\n- Зарплата каждые 10 дней\n- Тел: +998 99 060 33 53, @Ottimo_hr\nОтвечай дружелюбно и творчески.",
    },
    "en": {
        "welcome": "Hello, {}!\n\nWelcome to Ottimo Cafe HR Bot!\n\nPlease choose a section:",
        "menu": [
            ["👷 Apply for Job", "🌐 Language", "⏰ Working Hours"],
            ["📊 About Work", "🤝 Employee Issues", "📍 Branches"],
            ["📞 Support", "👨‍💼 Admin", "🗑️ Clear Chat"]
        ],
        "savol_javob": "Ask any question about Ottimo Cafe!\n\nFor example:\n— Where are the branches?\n— What are the working hours?\n— What documents are needed?",
        "til_tanlash": "Tilni tanlang / Выберите язык / Choose language:",
        "til_tanlash_menu": [["🇺🇿 O'zbek tili"], ["🇷🇺 Русский язык"], ["🇬🇧 English"]],
        "til_tanlandi": "English selected!",
        "admin": "Contact Admin:\n\nTelegram: @Ottimo_hr\nPhone: +998 99 060 33 53\n\nWorking hours: 09:00 — 18:00",
        "yordam": "Choose a section from the menu or ask any question!",
        "tozalandi": "Chat cleared!",
        "xatolik": "Technical error occurred. Please contact @Ottimo_hr.",
        "filiallar": "OTTIMO CAFE BRANCHES\n\n1. Near Nukus Cinema\n   Tashkent, Shifernur St., 71\n   https://yandex.uz/maps/org/144255252741/?ll=69.218418%2C41.350783&z=16.54\n\n2. Under Parus\n   Tashkent, Katartal St., 60A/1\n   https://yandex.uz/maps/org/45535920435/?ll=69.211087%2C41.292054&z=16.54\n\n3. Opposite Talant International School\n   Tashkent, Mirzo-Ulugbek district, Buyuk Ipak Yoli, 31\n   https://yandex.uz/maps/10335/tashkent/?ll=69.293312%2C41.313048&mode=poi&poi%5Bpoint%5D=69.293235%2C41.313153&poi%5Buri%5D=ymapsbm1%3A%2F%2Forg%3Foid%3D67180596093&z=19.79\n\nPhone: +998 99 060 33 53\nTelegram: @Ottimo_hr",
        "qollab": "Support:\n\nPhone: +998 99 060 33 53\nTelegram: @Ottimo_hr",
        "anketa_boshlash": "OTTIMO CAFE — JOB APPLICATION\n\nTotal {} questions.\nTo cancel type /bekor\n\n",
        "bekor": "Application cancelled.",
        "tasdiqlash": "Do you confirm?",
        "tasdiq_btn": "✅ Confirm",
        "bekor_btn": "❌ Cancel",
        "rahmat": "Thank you for completing the application!\n\nYour information has been saved successfully.\n\nReview period: 1-3 working days\n@Ottimo_hr will contact you soon\n\nGood luck!\n\nContact: https://t.me/ottimo_uz",
        "bekor_xabar": "Application cancelled.",
        "bosh_menyu": "Main menu:",
        "anketa_tayyor": "YOUR APPLICATION IS READY! Please check:\n\n",
        "ish_vaqti": "WORKING HOURS\n\n☀️ Shift 1: 07:30 — 16:30 (daytime)\n🌙 Shift 2: 16:00 — 24:00 (evening)\n\nSchedule updated every Monday\nChanges announced 1 day in advance\n\n⚠️ Late arrival fine: 50,000 sum\n🍽 Free meals every shift",
        "ish_malumot": "ABOUT OTTIMO CAFE\n\nOttimo is a modern cafe in Tashkent.\nOur goal — pleasant atmosphere and quality service.\n\n✅ Official employment contract\n✅ Salary every 10 days\n✅ Free meals\n✅ Career growth\n✅ Friendly team (25+ employees)\n\nVacancies:\n☕ Barista\n💳 Cashier\n🍰 Pastry seller\n\nBranches:\n1. Near Nukus Cinema — Shifernur St., 71\n2. Under Parus — Katartal St., 60A/1\n3. Opposite Talant school — Buyuk Ipak Yoli, 31\n\nPhone: +998 99 060 33 53 | @Ottimo_hr",
        "xodimlar_muammo": "SOLVING EMPLOYEE ISSUES\n\nStep 1: Talk with your colleague\nStep 2: Contact shift manager\nStep 3: Write to HR: @Ottimo_hr\n\n⚠️ Workplace conflicts are prohibited\n\n✅ Every complaint is reviewed\n\nPhone: +998 99 060 33 53",
        "mehnat_qonun": "LABOR LAW\n\n✅ RIGHTS:\n• Salary paid on time\n• Annual leave (15-21 days)\n• Sick leave\n• Social insurance\n\n⚠️ DUTIES:\n• Follow work regulations\n• Be on time\n\n🚫 PROHIBITED:\n• Smoking\n• Alcohol\n• Rudeness to customers\n\nTelegram: @Ottimo_hr",
        "smena_menu": [["☀️ Daytime (07:30-16:30)"], ["🌙 Evening (16:00-24:00)"], ["🔄 Either shift"]],
        "system_prompt": "You are an HR assistant for Ottimo Cafe. Reply only in English. Only answer questions about Ottimo Cafe. For other questions say: 'Sorry, I can only answer questions about Ottimo Cafe'.\n\nAbout Ottimo:\n- 3 branches: Shifernur 71, Katartal 60A/1, Buyuk Ipak Yoli 31\n- Vacancies: Barista, Cashier, Pastry seller\n- Hours: 07:30-16:30 and 16:00-24:00\n- Age: 20-35, Russian required\n- Salary every 10 days\n- Phone: +998 99 060 33 53, @Ottimo_hr\nBe friendly and creative.",
    }
}

# Foydalanuvchi tillari
user_lang = {}
user_sessions = {}
user_anketa = {}
admin_state = {}

def get_lang(user_id):
    return user_lang.get(user_id, "uz")

def get_text(user_id, key):
    lang = get_lang(user_id)
    return TEXTS[lang].get(key, TEXTS["uz"].get(key, ""))

def get_menu(user_id):
    lang = get_lang(user_id)
    return ReplyKeyboardMarkup(TEXTS[lang]["menu"], resize_keyboard=True)

def get_smena_menu(user_id):
    lang = get_lang(user_id)
    return ReplyKeyboardMarkup(TEXTS[lang]["smena_menu"], resize_keyboard=True, one_time_keyboard=True)

# ===================== DATABASE =====================
def init_db():
    conn = sqlite3.connect("ottimo.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS xodimlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ism TEXT, lavozim TEXT, telefon TEXT, smena TEXT,
        qoshilgan_sana TEXT, holat TEXT DEFAULT "aktiv"
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS kechikishlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        xodim_id INTEGER, sana TEXT, minut INTEGER, izoh TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS arizalar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ism TEXT, telefon TEXT, lavozim TEXT, smena TEXT,
        sana TEXT, holat TEXT DEFAULT "kutilmoqda"
    )''')
    conn.commit()
    conn.close()

def db_query(sql, params=(), fetchall=False, fetchone=False):
    conn = sqlite3.connect("ottimo.db")
    c = conn.cursor()
    c.execute(sql, params)
    conn.commit()
    if fetchall:
        result = c.fetchall(); conn.close(); return result
    if fetchone:
        result = c.fetchone(); conn.close(); return result
    conn.close()
    return c.lastrowid

# ===================== ANKETA SAVOLLARI =====================
ANKETA_STEPS = {
    "uz": [
        ("ism_familiya_sharif", "👤 1/31 — Ism, Familiya va Sharifingizni kiriting:\n(Masalan: Ibrohim Karimov Aliyevich)"),
        ("tug_sana",            "📅 2/31 — Tug'ilgan sanangizni kiriting:\n(Masalan: 15.03.2000)"),
        ("millat",              "🌍 3/31 — Millatingizni kiriting:\n(Masalan: O'zbek)"),
        ("tug_joy",             "🗺 4/31 — Tug'ilgan joyingizni kiriting (viloyat, tuman):"),
        ("yashash_joy",         "🏠 5/32 — Doimiy yashash manzilingizni kiriting:\n(Ko'cha, uy raqami, tuman, shahar)"),
        ("turar_joy",           "🏘 6/32 — Turar joy turingizni belgilang:\n(Dom / Hovli)"),
        ("telefon",             "📱 7/32 — Telefon raqamingizni kiriting:\n(+998 90 123 45 67)"),
        ("talim",               "🎓 8/32 — Ta'lim darajangizni belgilang:\n(Maktab / Kollej / Universitet)"),
        ("oquv_yurti",          "🏫 9/32 — Qaysi o'quv yurtini qachon tamomlagansiz?\n(Nomi, fakultet, yillar. Yo'q — Yo'q)"),
        ("oldingi_ish",         "💼 10/32 — Oldingi ishlagan joylaringiz:\n(Korxona nomi, lavozim, ishlagan yillar, bo'shash sababi.\nYo'q bo'lsa — Yo'q deb yozing)"),
        ("chet_safari",         "✈️ 11/32 — Chet el safariga chiqqanmisiz?\n(Ha — qayerga? / Yo'q)"),
        ("oilaviy_holat",       "💑 12/32 — Oilaviy holatingizni belgilang:\n\nTurmush qurmagan\nTurmush qurgan\nAjrashgan"),
        ("oila_azosi",          "👨‍👩‍👧 13/32 — Oila a'zolaringiz:\n(Ism, tug'ilgan sana, ish joyi, telefon.\nYo'q bo'lsa — Yo'q deb yozing)"),
        ("sudlanganmi",         "⚖️ 14/31 — Sudlanganmisiz?\n(Yo'q / Ha — sababi)"),
        ("avtomobil",           "🚗 15/31 — Shaxsiy avtomobilingiz bormi?\n(Yo'q / Ha — rusumi)"),
        ("haydovchilik",        "🪪 16/31 — Haydovchilik guvohnomangiz bormi?\n(Yo'q / Ha — turi: A/B/C/D/E)"),
        ("uzbek_tili",          "🗣 17/31 — O'zbek tilini qay darajada bilasiz?\n(A'lo / Yaxshi / Past)"),
        ("rus_tili",            "🗣 18/31 — Rus tilini qay darajada bilasiz?\n(A'lo / Yaxshi / Past / Bilmayman)"),
        ("ingliz_tili",         "🗣 19/31 — Ingliz tilini qay darajada bilasiz?\n(A'lo / Yaxshi / Past / Bilmayman)"),
        ("boshqa_til",          "🗣 20/31 — Boshqa tillarni bilasizmi?\n(Yo'q / Ha — qaysi va darajasi)"),
        ("qobiliyat",           "⭐ 21/32 — Alohida qobiliyatlaringiz:\n(Masalan: oshpazlik, musiqa, sport...\nYo'q bo'lsa — Yo'q deb yozing)"),
        ("bosh_vaqt",           "🎯 22/32 — Bo'sh vaqtingizni qanday o'tkazasiz?"),
        ("kompyuter",           "💻 23/32 — Kompyuterda ishlash darajangiz:\n(Erkin / O'rta / Bilmayman)"),
        ("qayerdan_bildingiz",  "📢 24/32 — Kompaniyamiz haqida qayerdan bildingiz?"),
        ("kafil",               "🤝 25/32 — Ishlashingizga kafolat bera oladigan shaxs:\n(Ismi, siz bilan aloqasi, ish joyi, telefon raqami.\nYo'q bo'lsa — Yo'q deb yozing)"),
        ("tavsiya",             "📄 26/32 — Oxirgi ish joyingizdan tavsiya xati bera oladimi?\n(Ha bo'lsa — ismi, lavozimi, telefon raqami.\nYo'q bo'lsa — Yo'q deb yozing)"),
        ("surushtirishga_rozi", "🔍 27/32 — Oxirgi ish joyingizdan surishtirishimizga rozimisiz?\n(Ha / Yo'q)"),
        ("oldingi_maosh",       "💵 28/32 — Oxirgi ish joyingizda qancha maosh olgan edingiz?"),
        ("kutilayotgan_maosh",  "💰 29/32 — Bizdan qancha maosh kutasiz?"),
        ("ishlash_muddati",     "📆 30/32 — Bizda qancha muddat ishlashni rejalashtirasiz?"),
        ("smena",               "⏰ 31/32 — Qaysi vaqtda ishlashni xohlaysiz?\n\n☀️ Kunduzi (07:30-16:30)\n🌙 Kechki payt (16:00-24:00)\n🔄 Ikkalasi ham bo'ladi"),
        ("rasm",                "📸 32/32 — Shaxsiy rasmingizni yuboring:\n\nIltimos, yuz aniq ko'rinadigan rasmiy surat yuboring."),
    ],
    "ru": [
        ("ism_familiya_sharif", "👤 1/31 — Введите Имя, Фамилию и Отчество:\n(Например: Ибрагим Каримов Алиевич)"),
        ("tug_sana",            "📅 2/31 — Введите дату рождения:\n(Например: 15.03.2000)"),
        ("millat",              "🌍 3/31 — Введите национальность:\n(Например: Узбек)"),
        ("tug_joy",             "🗺 4/31 — Место рождения (область, район):"),
        ("yashash_joy",         "🏠 5/31 — Постоянное место проживания:"),
        ("turar_joy",           "🏘 6/31 — Тип жилья:\n(Квартира / Дом)"),
        ("telefon",             "📱 7/31 — Введите номер телефона:\n(+998 90 123 45 67)"),
        ("talim",               "🎓 8/31 — Уровень образования:\n(Школа / Колледж / Университет)"),
        ("oquv_yurti",          "🏫 9/31 — Какое учебное заведение и когда закончили?\n(Название, факультет, годы. Нет — Нет)"),
        ("oldingi_ish",         "💼 10/31 — Предыдущие места работы:\n(Компания, должность, годы, причина ухода. Нет — Нет)"),
        ("chet_safari",         "✈️ 11/31 — Выезжали ли за рубеж?\n(Да — куда? / Нет)"),
        ("oilaviy_holat",       "💑 12/31 — Семейное положение:\n(Холост/Не замужем / Женат/Замужем / Разведён/а)"),
        ("oila_azosi",          "👨‍👩‍👧 13/31 — Члены семьи:\n(Имя, дата рождения, место работы, телефон. Нет — Нет)"),
        ("sudlanganmi",         "⚖️ 14/31 — Были ли судимы?\n(Нет / Да — причина)"),
        ("avtomobil",           "🚗 15/31 — Есть ли личный автомобиль?\n(Нет / Да — марка)"),
        ("haydovchilik",        "🪪 16/31 — Есть ли водительские права?\n(Нет / Да — категория: A/B/C/D/E)"),
        ("uzbek_tili",          "🗣 17/31 — Уровень узбекского языка?\n(Отлично / Хорошо / Слабо)"),
        ("rus_tili",            "🗣 18/31 — Уровень русского языка?\n(Отлично / Хорошо / Слабо / Не знаю)"),
        ("ingliz_tili",         "🗣 19/31 — Уровень английского языка?\n(Отлично / Хорошо / Слабо / Не знаю)"),
        ("boshqa_til",          "🗣 20/31 — Знаете ли другие языки?\n(Нет / Да — какой и уровень)"),
        ("qobiliyat",           "⭐ 21/31 — Особые навыки и умения:\n(Нет — Нет)"),
        ("bosh_vaqt",           "🎯 22/31 — Как проводите свободное время?"),
        ("kompyuter",           "💻 23/31 — Уровень работы с компьютером:\n(Свободно / Средне / Не умею)"),
        ("qayerdan_bildingiz",  "📢 24/31 — Откуда узнали о нашей компании?"),
        ("kafil",               "🤝 25/31 — Есть ли поручитель?\n(Имя, связь, место работы, телефон. Нет — Нет)"),
        ("tavsiya",             "📄 26/31 — Может ли кто-то дать рекомендательное письмо?\n(Да — имя, должность, телефон. Нет — Нет)"),
        ("surushtirishga_rozi", "🔍 27/31 — Согласны ли на проверку последнего места работы?\n(Да / Нет)"),
        ("oldingi_maosh",       "💵 28/31 — Какую зарплату получали на последнем месте работы?"),
        ("kutilayotgan_maosh",  "💰 29/31 — Какую зарплату ожидаете от нас?"),
        ("ishlash_muddati",     "📆 30/31 — На какой срок планируете работать у нас?"),
        ("smena",               "⏰ 31/31 — В какое время хотите работать?\n\n☀️ Дневная (07:30-16:30)\n🌙 Вечерняя (16:00-24:00)\n🔄 Любая смена"),
    ],
    "en": [
        ("ism_familiya_sharif", "👤 1/31 — Enter your Full Name:\n(Example: Ibrahim Karimov Aliyevich)"),
        ("tug_sana",            "📅 2/31 — Enter your date of birth:\n(Example: 15.03.2000)"),
        ("millat",              "🌍 3/31 — Enter your nationality:\n(Example: Uzbek)"),
        ("tug_joy",             "🗺 4/31 — Place of birth (region, district):"),
        ("yashash_joy",         "🏠 5/31 — Permanent address:"),
        ("turar_joy",           "🏘 6/31 — Type of residence:\n(Apartment / House)"),
        ("telefon",             "📱 7/31 — Enter your phone number:\n(+998 90 123 45 67)"),
        ("talim",               "🎓 8/31 — Education level:\n(School / College / University)"),
        ("oquv_yurti",          "🏫 9/31 — Which institution and when did you graduate?\n(Name, faculty, years. None — None)"),
        ("oldingi_ish",         "💼 10/31 — Previous work experience:\n(Company, position, years, reason for leaving. None — None)"),
        ("chet_safari",         "✈️ 11/31 — Have you traveled abroad?\n(Yes — where? / No)"),
        ("oilaviy_holat",       "💑 12/31 — Marital status:\n(Single / Married / Divorced)"),
        ("oila_azosi",          "👨‍👩‍👧 13/31 — Family members:\n(Name, date of birth, workplace, phone. None — None)"),
        ("sudlanganmi",         "⚖️ 14/31 — Have you ever been convicted?\n(No / Yes — reason)"),
        ("avtomobil",           "🚗 15/31 — Do you have a personal car?\n(No / Yes — model)"),
        ("haydovchilik",        "🪪 16/31 — Do you have a driver's license?\n(No / Yes — category: A/B/C/D/E)"),
        ("uzbek_tili",          "🗣 17/31 — Uzbek language level?\n(Excellent / Good / Poor)"),
        ("rus_tili",            "🗣 18/31 — Russian language level?\n(Excellent / Good / Poor / None)"),
        ("ingliz_tili",         "🗣 19/31 — English language level?\n(Excellent / Good / Poor / None)"),
        ("boshqa_til",          "🗣 20/31 — Do you know any other languages?\n(No / Yes — which and level)"),
        ("qobiliyat",           "⭐ 21/31 — Special skills or talents:\n(None — None)"),
        ("bosh_vaqt",           "🎯 22/31 — How do you spend your free time?"),
        ("kompyuter",           "💻 23/31 — Computer skills level:\n(Proficient / Basic / None)"),
        ("qayerdan_bildingiz",  "📢 24/31 — How did you find out about our company?"),
        ("kafil",               "🤝 25/31 — Do you have a guarantor?\n(Name, relation, workplace, phone. None — None)"),
        ("tavsiya",             "📄 26/31 — Can someone provide a reference letter?\n(Yes — name, position, phone. None — None)"),
        ("surushtirishga_rozi", "🔍 27/31 — Do you agree to background check from last job?\n(Yes / No)"),
        ("oldingi_maosh",       "💵 28/31 — What was your salary at your last job?"),
        ("kutilayotgan_maosh",  "💰 29/31 — What salary do you expect from us?"),
        ("ishlash_muddati",     "📆 30/31 — How long are you planning to work with us?"),
        ("smena",               "⏰ 31/31 — Which shift do you prefer?\n\n☀️ Daytime (07:30-16:30)\n🌙 Evening (16:00-24:00)\n🔄 Either shift"),
    ]
}

ADMIN_MENU = ReplyKeyboardMarkup([
    ["👥 Xodimlar ro'yxati", "➕ Xodim qo'shish"],
    ["⚠️ Kechikish belgilash", "📋 Arizalar ro'yxati"],
    ["📊 Statistika", "🔙 Bosh menyu"]
], resize_keyboard=True)

ADMIN_ADD_STEPS = [
    ("ism",     "👤 Xodimning ismi:"),
    ("lavozim", "🎯 Lavozimi:"),
    ("telefon", "📱 Telefon:"),
    ("smena",   "⏰ Smenasi:"),
]

# ===================== ADMIN =====================
async def show_xodimlar(update, context):
    xodimlar = db_query("SELECT id, ism, lavozim, smena FROM xodimlar WHERE holat='aktiv'", fetchall=True)
    if not xodimlar:
        await update.message.reply_text("Xodimlar ro'yxati bo'sh.", reply_markup=ADMIN_MENU); return
    text = "XODIMLAR\n\n"
    for x in xodimlar:
        text += f"#{x[0]} {x[1]} | {x[2]} | {x[3]}\n"
    await update.message.reply_text(text, reply_markup=ADMIN_MENU)

async def show_statistika(update, context):
    jami = db_query("SELECT COUNT(*) FROM xodimlar WHERE holat='aktiv'", fetchone=True)[0]
    arizalar = db_query("SELECT COUNT(*) FROM arizalar WHERE holat='kutilmoqda'", fetchone=True)[0]
    kechikish = db_query("SELECT COUNT(*) FROM kechikishlar", fetchone=True)[0]
    await update.message.reply_text(
        f"STATISTIKA\n\nXodimlar: {jami}\nArizalar: {arizalar}\nKechikishlar: {kechikish}",
        reply_markup=ADMIN_MENU)

async def show_arizalar(update, context):
    arizalar = db_query("SELECT id, ism, telefon, lavozim, smena, sana FROM arizalar WHERE holat='kutilmoqda'", fetchall=True)
    if not arizalar:
        await update.message.reply_text("Ariza yo'q.", reply_markup=ADMIN_MENU); return
    text = "ARIZALAR\n\n"
    for a in arizalar:
        text += f"#{a[0]} {a[1]} | {a[2]} | {a[3]} | {a[4]} | {a[5]}\n"
    await update.message.reply_text(text, reply_markup=ADMIN_MENU)

async def start_add_xodim(update, context):
    user_id = update.effective_user.id
    admin_state[user_id] = {"action": "add_xodim", "step": 0, "data": {}}
    await update.message.reply_text(ADMIN_ADD_STEPS[0][1], reply_markup=ReplyKeyboardRemove())

async def process_add_xodim(update, context):
    user_id = update.effective_user.id
    state = admin_state[user_id]
    key, _ = ADMIN_ADD_STEPS[state["step"]]
    state["data"][key] = update.message.text
    next_step = state["step"] + 1
    if next_step < len(ADMIN_ADD_STEPS):
        state["step"] = next_step
        await update.message.reply_text(ADMIN_ADD_STEPS[next_step][1], reply_markup=ReplyKeyboardRemove())
    else:
        data = state["data"]
        db_query("INSERT INTO xodimlar (ism, lavozim, telefon, smena, qoshilgan_sana) VALUES (?,?,?,?,?)",
                 (data['ism'], data['lavozim'], data['telefon'], data['smena'], datetime.now().strftime("%d.%m.%Y")))
        admin_state.pop(user_id, None)
        await update.message.reply_text(f"{data['ism']} qo'shildi!", reply_markup=ADMIN_MENU)

async def start_kechikish(update, context):
    xodimlar = db_query("SELECT id, ism FROM xodimlar WHERE holat='aktiv'", fetchall=True)
    if not xodimlar:
        await update.message.reply_text("Xodimlar yo'q.", reply_markup=ADMIN_MENU); return
    keyboard = [[InlineKeyboardButton(x[1], callback_data=f"kechik_{x[0]}")] for x in xodimlar]
    await update.message.reply_text("Qaysi xodim kechikdi?", reply_markup=InlineKeyboardMarkup(keyboard))

async def kechikish_callback(update, context):
    query = update.callback_query
    await query.answer()
    xodim_id = int(query.data.split("_")[1])
    xodim = db_query("SELECT ism FROM xodimlar WHERE id=?", (xodim_id,), fetchone=True)
    db_query("INSERT INTO kechikishlar (xodim_id, sana, minut) VALUES (?,?,?)",
             (xodim_id, datetime.now().strftime("%d.%m.%Y"), 15))
    await query.edit_message_text(f"{xodim[0]} — jarima: 50 000 so'm")

# ===================== ANKETA =====================
async def start_anketa(update, context):
    user_id = update.effective_user.id
    lang = get_lang(user_id)
    user_anketa[user_id] = {"step": 0, "data": {}}
    steps = ANKETA_STEPS[lang]
    await update.message.reply_text(
        get_text(user_id, "anketa_boshlash").format(len(steps)) + steps[0][1],
        reply_markup=ReplyKeyboardRemove())

async def process_anketa(update, context):
    user_id = update.effective_user.id
    lang = get_lang(user_id)
    steps = ANKETA_STEPS[lang]
    step_data = user_anketa[user_id]
    current_step = step_data["step"]
    key, _ = steps[current_step]

    # Rasm qabul qilish
    if key == "rasm":
        if update.message.photo:
            photo_id = update.message.photo[-1].file_id
            step_data["data"]["rasm"] = photo_id
            step_data["data"]["rasm_file_id"] = photo_id
        elif update.message.text == "/bekor":
            user_anketa.pop(user_id, None)
            await update.message.reply_text(get_text(user_id, "bekor"), reply_markup=get_menu(user_id)); return
        else:
            await update.message.reply_text("Iltimos, rasm yuboring (3x4 razmer):", reply_markup=ReplyKeyboardRemove()); return
    else:
        text = update.message.text
        if text == "/bekor":
            user_anketa.pop(user_id, None)
            await update.message.reply_text(get_text(user_id, "bekor"), reply_markup=get_menu(user_id)); return
        step_data["data"][key] = text

    next_step = current_step + 1

    if next_step < len(steps):
        step_data["step"] = next_step
        next_key, next_question = steps[next_step]
        if next_key == "smena":
            await update.message.reply_text(next_question, reply_markup=get_smena_menu(user_id))
        elif next_key == "rasm":
            await update.message.reply_text(next_question, reply_markup=ReplyKeyboardRemove())
        else:
            await update.message.reply_text(next_question, reply_markup=ReplyKeyboardRemove())
    else:
        data = step_data["data"]
        db_query("INSERT INTO arizalar (ism, telefon, lavozim, smena, sana) VALUES (?,?,?,?,?)",
                 (data.get('ism_familiya_sharif'), data.get('telefon'), "—",
                  data.get('smena'), datetime.now().strftime("%d.%m.%Y")))

        summary = get_text(user_id, "anketa_tayyor")
        fields = [
            ("Ism / Name / Имя", "ism_familiya_sharif"),
            ("Tug'ilgan sana", "tug_sana"),
            ("Millat", "millat"),
            ("Tug'ilgan joy", "tug_joy"),
            ("Yashash joyi", "yashash_joy"),
            ("Turar joy", "turar_joy"),
            ("Telefon", "telefon"),
            ("Ta'lim", "talim"),
            ("O'quv yurti", "oquv_yurti"),
            ("Ish tajribasi", "oldingi_ish"),
            ("Chet safari", "chet_safari"),
            ("Oilaviy holat", "oilaviy_holat"),
            ("Oila a'zolari", "oila_azosi"),
            ("Sudlanganmi", "sudlanganmi"),
            ("Avtomobil", "avtomobil"),
            ("Haydovchilik", "haydovchilik"),
            ("O'zbek tili", "uzbek_tili"),
            ("Rus tili", "rus_tili"),
            ("Ingliz tili", "ingliz_tili"),
            ("Boshqa til", "boshqa_til"),
            ("Qobiliyat", "qobiliyat"),
            ("Bo'sh vaqt", "bosh_vaqt"),
            ("Kompyuter", "kompyuter"),
            ("Qayerdan bildingiz", "qayerdan_bildingiz"),
            ("Kafil", "kafil"),
            ("Tavsiya", "tavsiya"),
            ("Surishtirish", "surushtirishga_rozi"),
            ("Oldingi maosh", "oldingi_maosh"),
            ("Kutilayotgan maosh", "kutilayotgan_maosh"),
            ("Ishlash muddati", "ishlash_muddati"),
            ("Smena", "smena"),
        ]
        for label, key in fields:
            val = data.get(key, "—")
            summary += f"{label}: {val}\n"

        summary += f"\n{get_text(user_id, 'tasdiqlash')}"

        confirm_keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(get_text(user_id, "tasdiq_btn"), callback_data="anketa_confirm"),
            InlineKeyboardButton(get_text(user_id, "bekor_btn"), callback_data="anketa_cancel")
        ]])
        await update.message.reply_text(summary, reply_markup=confirm_keyboard)

async def anketa_callback(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "anketa_confirm":
        data = user_anketa.get(user_id, {}).get("data", {})
        username = query.from_user.username or "username_yoq"
        msg = "YANGI ARIZA!\n\n"
        fields = [
            ("Ism", "ism_familiya_sharif"), ("Telefon", "telefon"),
            ("Tug'ilgan sana", "tug_sana"), ("Millat", "millat"),
            ("Tug'ilgan joy", "tug_joy"), ("Yashash joyi", "yashash_joy"),
            ("Turar joy", "turar_joy"), ("Ta'lim", "talim"),
            ("O'quv yurti", "oquv_yurti"), ("Ish tajribasi", "oldingi_ish"),
            ("Chet safari", "chet_safari"), ("Oilaviy holat", "oilaviy_holat"),
            ("Oila a'zolari", "oila_azosi"), ("Sudlanganmi", "sudlanganmi"),
            ("Avtomobil", "avtomobil"), ("Haydovchilik", "haydovchilik"),
            ("O'zbek tili", "uzbek_tili"), ("Rus tili", "rus_tili"),
            ("Ingliz tili", "ingliz_tili"), ("Boshqa til", "boshqa_til"),
            ("Qobiliyat", "qobiliyat"), ("Bo'sh vaqt", "bosh_vaqt"),
            ("Kompyuter", "kompyuter"), ("Qayerdan", "qayerdan_bildingiz"),
            ("Kafil", "kafil"), ("Tavsiya", "tavsiya"),
            ("Surishtirish", "surushtirishga_rozi"), ("Oldingi maosh", "oldingi_maosh"),
            ("Kutilayotgan maosh", "kutilayotgan_maosh"), ("Muddati", "ishlash_muddati"),
            ("Smena", "smena"),
        ]
        for label, key in fields:
            msg += f"{label}: {data.get(key, '—')}\n"
        msg += f"\nTelegram: @{username}"

        try:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg)
            logger.info(f"Admin ga xabar yuborildi")
            # Rasmni ham yuborish
            rasm_id = data.get("rasm_file_id")
            if rasm_id:
                await context.bot.send_photo(
                    chat_id=ADMIN_CHAT_ID,
                    photo=rasm_id,
                    caption=f"Ariza beruvchi rasmi: {data.get('ism_familiya_sharif', '')}"
                )
        except Exception as e:
            logger.error(f"Admin ga xato: {e}")

        user_anketa.pop(user_id, None)
        try:
            await query.message.delete()
        except Exception:
            pass
        await context.bot.send_message(
            chat_id=user_id,
            text=get_text(user_id, "rahmat"),
            reply_markup=get_menu(user_id))

    elif query.data == "anketa_cancel":
        user_anketa.pop(user_id, None)
        await query.edit_message_text(get_text(user_id, "bekor_xabar"))
        await context.bot.send_message(
            chat_id=user_id,
            text=get_text(user_id, "bosh_menyu"),
            reply_markup=get_menu(user_id))

# ===================== GEMINI =====================
def ask_gemini(user_id, user_text):
    lang = get_lang(user_id)
    history = user_sessions.get(user_id, [])

    # Savol mode tekshirish
    savol_mode = any(h.get("user") == "__savol_mode__" for h in history)

    # Toza tarix (mode flaglarni olib tashlash)
    clean = [h for h in history if h.get("user") not in ("__savol_mode__",)]
    history_text = ""
    if clean:
        history_text = "\n\n" + "\n".join([
            f"Foydalanuvchi: {h['user']}\nAgent: {h['agent']}" for h in clean[-5:]])

    ottimo_info = (
        "Ottimo Cafe haqida ma'lumot:\n"
        "- Toshkentda 3 ta filiali bor\n"
        "- 1-filial: Nukus kinoteatri yonida, Shifer ko'chasi 71\n"
        "- 2-filial: Parus ostida, Katartal ko'chasi 60A/1\n"
        "- 3-filial: Talant International School ro'parasida, Buyuk Ipak Yo'li 31\n"
        "- Bo'sh ish o'rinlari: Barista, Kassir, Konditer-sotuvchi\n"
        "- Ish vaqti: Kunduzi 07:30-16:30, Kechki payt 16:00-24:00\n"
        "- Yosh talabi: 20-35\n"
        "- Rus tilini bilish shart\n"
        "- Chekmaydigan va spirtli ichimlik iste'mol qilmaydigan bo'lishi kerak\n"
        "- Probatsiya: 1 oy\n"
        "- Maosh har 10 kunda to'lanadi\n"
        "- Har smenada bepul ovqat beriladi\n"
        "- Telefon: +998 99 060 33 53\n"
        "- Telegram: @Ottimo_hr"
    )

    if lang == "ru":
        lang_instr = "Отвечай только на русском языке."
        restrict = "Отвечай только на вопросы об Ottimo Cafe. На другие темы говори: 'Извините, я отвечаю только на вопросы об Ottimo Cafe.'"
    elif lang == "en":
        lang_instr = "Reply only in English."
        restrict = "Answer only questions about Ottimo Cafe. For other topics say: 'Sorry, I only answer questions about Ottimo Cafe.'"
    else:
        lang_instr = "Faqat o'zbek tilida javob ber."
        restrict = "Faqat Ottimo Cafe haqidagi savollarga javob ber. Boshqa mavzularga: 'Kechirasiz, men faqat Ottimo Cafe haqida javob bera olaman.' de."

    if savol_mode:
        system = (
            f"{lang_instr}\n"
            f"Sen Ottimo Cafe uchun aqlli HR yordamchisisisan.\n"
            f"{restrict}\n\n"
            f"{ottimo_info}\n\n"
            "Savollarga chiroyli, to'liq va ijodiy tarzda javob ber. "
            "Agar foydalanuvchi filiallar so'rasa — uchala filialning manzilini batafsil ko'rsat. "
            "Agar maosh so'rasa — barcha ma'lumotlarni ayt."
        )
    else:
        system = (
            f"{lang_instr}\n"
            f"Sen Ottimo Cafe uchun HR agentisan.\n"
            f"{ottimo_info}\n"
            "Har doim do'stona va aniq javob ber."
        )

    full_prompt = system + history_text + f"\n\nFoydalanuvchi: {user_text}\nAgent:"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"

    # 3 marta urinish
    for attempt in range(3):
        try:
            r = requests.post(
                url,
                json={"contents": [{"parts": [{"text": full_prompt}]}],
                      "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1000}},
                timeout=30
            )
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            logger.error(f"Gemini urinish {attempt+1}: {e}")
            if attempt < 2:
                import time; time.sleep(2)
    raise Exception("Gemini 3 marta ham javob bermadi")

# ===================== ASOSIY =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "Foydalanuvchi"
    lang_menu = ReplyKeyboardMarkup(
        TEXTS["uz"]["til_tanlash_menu"], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        f"Salom, {user_name}!\n\nIltimos, tilni tanlang:\nПожалуйста, выберите язык:\nPlease choose language:",
        reply_markup=lang_menu)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_anketa:
        await process_anketa(update, context)
    else:
        await update.message.reply_text(
            "Rasm qabul qilindi, lekin hozir anketa to'ldirilmayapti.",
            reply_markup=get_menu(user_id))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    if user_id in user_anketa:
        await process_anketa(update, context); return
    if user_id in admin_state and admin_state[user_id].get("action") == "add_xodim":
        await process_add_xodim(update, context); return

    # Admin tugmalari
    admin_map = {
        "👥 Xodimlar ro'yxati": show_xodimlar,
        "➕ Xodim qo'shish": start_add_xodim,
        "⚠️ Kechikish belgilash": start_kechikish,
        "📋 Arizalar ro'yxati": show_arizalar,
        "📊 Statistika": show_statistika,
    }
    if user_text in admin_map:
        await admin_map[user_text](update, context); return
    if user_text == "🔙 Bosh menyu":
        await update.message.reply_text(get_text(user_id, "bosh_menyu"), reply_markup=get_menu(user_id)); return

    # Til tanlash
    if user_text in ["🌐 Til tanlash", "🌐 Выбор языка", "🌐 Language"]:
        lang_menu = ReplyKeyboardMarkup(
            TEXTS["uz"]["til_tanlash_menu"], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(get_text(user_id, "til_tanlash"), reply_markup=lang_menu); return

    if user_text == "🇺🇿 O'zbek tili":
        user_lang[user_id] = "uz"
        await update.message.reply_text(TEXTS["uz"]["til_tanlandi"], reply_markup=get_menu(user_id)); return
    if user_text == "🇷🇺 Русский язык":
        user_lang[user_id] = "ru"
        await update.message.reply_text(TEXTS["ru"]["til_tanlandi"], reply_markup=get_menu(user_id)); return
    if user_text == "🇬🇧 English":
        user_lang[user_id] = "en"
        await update.message.reply_text(TEXTS["en"]["til_tanlandi"], reply_markup=get_menu(user_id)); return

    # Asosiy tugmalar — barcha tillarda
    all_keys = {
        "👷 Ishchi qabul qilish": "anketa",
        "👷 Приём на работу": "anketa",
        "👷 Apply for Job": "anketa",
        "❓ Savol va Javob": "savol",
        "❓ Вопрос и Ответ": "savol",
        "❓ Q&A": "savol",
        "⏰ Ish vaqti": "ish_vaqti",
        "⏰ Рабочее время": "ish_vaqti",
        "⏰ Working Hours": "ish_vaqti",
        "📊 Ish ma'lumotlari": "ish_malumot",
        "📊 О работе": "ish_malumot",
        "📊 About Work": "ish_malumot",
        "🤝 Xodimlar muammolari": "xodimlar_muammo",
        "🤝 Проблемы сотрудников": "xodimlar_muammo",
        "🤝 Employee Issues": "xodimlar_muammo",
        "⚖️ Mehnat qonunlari": "mehnat_qonun",
        "⚖️ Трудовое законодательство": "mehnat_qonun",
        "⚖️ Labor Law": "mehnat_qonun",
        "📍 Filiallar": "filiallar",
        "📍 Филиалы": "filiallar",
        "📍 Branches": "filiallar",
        "📞 Qo'llab-quvvatlash": "qollab",
        "📞 Поддержка": "qollab",
        "📞 Support": "qollab",
        "👨‍💼 Admin": "admin",
        "👨‍💼 Админ": "admin",
        "🆘 Yordam": "yordam",
        "🆘 Помощь": "yordam",
        "🆘 Help": "yordam",
        "🗑️ Suhbatni tozalash": "tozala",
        "🗑️ Очистить чат": "tozala",
        "🗑️ Clear Chat": "tozala",
    }

    action = all_keys.get(user_text)

    if action == "anketa":
        await start_anketa(update, context); return

    if action == "savol":
        user_sessions[user_id] = [{"user": "__savol_mode__", "agent": "__savol_mode__"}]
        lang = get_lang(user_id)
        if lang == "ru":
            msg = "Задайте любой вопрос об Ottimo Cafe — я отвечу!"
        elif lang == "en":
            msg = "Ask any question about Ottimo Cafe — I'll answer!"
        else:
            msg = "Ottimo Cafe haqida savolingizni yozing — javob beraman!"
        await update.message.reply_text(msg, reply_markup=get_menu(user_id)); return

    if action in ["ish_vaqti", "ish_malumot", "xodimlar_muammo", "mehnat_qonun", "filiallar", "qollab"]:
        await update.message.reply_text(get_text(user_id, action), reply_markup=get_menu(user_id)); return
    if action == "admin":
        await update.message.reply_text(get_text(user_id, "admin"), reply_markup=get_menu(user_id)); return
    if action == "yordam":
        await update.message.reply_text(get_text(user_id, "yordam"), reply_markup=get_menu(user_id)); return
    if action == "tozala":
        user_sessions[user_id] = []
        await update.message.reply_text(get_text(user_id, "tozalandi"), reply_markup=get_menu(user_id)); return

    # Har qanday matn — Gemini ga yuborish (savol mode ham, erkin savol ham)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    if user_id not in user_sessions:
        user_sessions[user_id] = []
    try:
        reply = ask_gemini(user_id, user_text)
        # Faqat haqiqiy savol-javobni saqlash (mode flaglarni emas)
        user_sessions[user_id] = [h for h in user_sessions[user_id] if h.get("user") != "__savol_mode__"]
        user_sessions[user_id].append({"user": user_text, "agent": reply})
        await update.message.reply_text(reply, reply_markup=get_menu(user_id))
    except Exception as e:
        logger.error(f"Xato: {e}")
        await update.message.reply_text(get_text(user_id, "xatolik"), reply_markup=get_menu(user_id))

def main():
    init_db()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(anketa_callback, pattern="^anketa_"))
    app.add_handler(CallbackQueryHandler(kechikish_callback, pattern="^kechik_"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
