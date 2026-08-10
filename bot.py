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
# Admin roli va ID
ADMIN_RAHBAR = 206004279      # Rahbar (mr_jalilov7)
ADMIN_HR = 731698729           # HR (Zamin_Rashidov)
ADMIN_APPROVAL_PREFIX = "ariza_approval_"

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
