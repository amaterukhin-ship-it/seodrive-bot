"""
SEO-Драйв · Telegram-бот @SeoDriveBot
Полный рабочий код. Требования: python-telegram-bot==20.x, gspread, google-auth
"""

import logging
import os
import asyncio
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, filters, ContextTypes
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Конфигурация ─────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8705014463:AAHkZhfe18J6X_jUHu1asaR6MUs-fAFCFRs")
ADMIN_ID   = int(os.environ.get("ADMIN_ID", "1623431505"))  # @AleksandrMaterukhin
SHEETS_ID  = os.environ.get("SHEETS_ID", "")       # ID Google Sheets
YUKASSA_LINK = "https://yoomoney.ru/TO/ВАША_ССЫЛКА"  # ссылка ЮKassa
CHANNEL    = "@seodrive_ai"

# ── Состояния ConversationHandler ────────────────────────────────────────────
(
    AUDIT_DOMAIN,
    AUDIT_METRIKA,
    ONBOARD_DOMAIN,
    ONBOARD_CONTACTS,
    ONBOARD_MCP,
    ONBOARD_METRIKA,
    ONBOARD_GSC,
    ONBOARD_COMPETITORS,
    ONBOARD_KEYWORDS,
    WAIT_PAYMENT,
) = range(10)

# ── Тексты ───────────────────────────────────────────────────────────────────
WELCOME_TEXT = """
👋 Привет! Я *SEO-Драйв* — сервис, где AI-агент каждую неделю сам продвигает ваш сайт.

Что я умею:
• Анализирую позиции, трафик, конкурентов
• Нахожу новые поисковые запросы через Wordstat и подсказки
• Правлю сайт напрямую (через WordPress)
• Каждую неделю отчитываюсь вам

💰 Цена: *2 000 ₽/мес*

Выберите действие:
"""

AUDIT_START_TEXT = """
🔍 *Бесплатный аудит сайта*

Я проверю:
✓ Индексацию в Яндексе и Google
✓ Базовые SEO-ошибки
✓ Конкурентов по вашим ключевым словам
✓ Точки роста трафика

Введите адрес вашего сайта (например: mysite.ru):
"""

ONBOARD_START_TEXT = """
🚀 *Подключение к SEO-Драйв*

Отлично! Заполним короткую анкету — займёт 2 минуты.
После этого получите ссылку на оплату, и агент начнёт работу уже в этот понедельник.

Шаг 1/7 — введите адрес вашего сайта:
"""


def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Бесплатный аудит", callback_data="audit_start")],
        [InlineKeyboardButton("🚀 Подключиться (2 000 ₽/мес)", callback_data="onboard_start")],
        [InlineKeyboardButton("📺 Наш канал", url=f"https://t.me/seodrive_ai")],
    ])


# ── /start ───────────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        WELCOME_TEXT,
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )


# ══════════════════════════════════════════════════════════════════════════════
#  АУДИТ
# ══════════════════════════════════════════════════════════════════════════════
async def audit_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(AUDIT_START_TEXT, parse_mode="Markdown")
    return AUDIT_DOMAIN


async def audit_get_domain(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    domain = update.message.text.strip().replace("https://", "").replace("http://", "").strip("/")
    ctx.user_data["audit_domain"] = domain
    await update.message.reply_text(
        f"✅ Принято: *{domain}*\n\nТеперь введите счётчик Яндекс.Метрики (число) "
        f"или напишите *нет*, если его нет:",
        parse_mode="Markdown"
    )
    return AUDIT_METRIKA


async def audit_get_metrika(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    metrika = update.message.text.strip()
    domain  = ctx.user_data.get("audit_domain", "")
    user    = update.effective_user

    await update.message.reply_text("⏳ Анализирую сайт, подождите 10–15 секунд...")

    report = await run_audit(domain, metrika)

    await update.message.reply_text(report, parse_mode="Markdown")
    await update.message.reply_text(
        "Хотите, чтобы AI-агент исправил эти проблемы *автоматически каждую неделю*?\n\n"
        "Стоимость: 2 000 ₽/мес. Первый месяц — и вы увидите результат.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Подключиться", callback_data="onboard_start")],
            [InlineKeyboardButton("← Главное меню", callback_data="main_menu")],
        ])
    )

    # Уведомление администратору
    if ADMIN_ID:
        await ctx.bot.send_message(
            ADMIN_ID,
            f"📋 Новый аудит\nПользователь: @{user.username} ({user.id})\nСайт: {domain}\nМетрика: {metrika}"
        )

    return ConversationHandler.END


async def run_audit(domain: str, metrika: str) -> str:
    """
    Реальный аудит через API.
    Сейчас — шаблон с ключевыми проверками.
    В продакшне: подключить Яндекс.Метрику API, GSC API, Wordstat.
    """
    await asyncio.sleep(2)  # имитация запроса

    report = f"""📊 *Аудит сайта {domain}*
_{datetime.now().strftime("%d.%m.%Y %H:%M")}_

──────────────────────

🔴 *Найденные проблемы:*

1. *Title и Description* — требуют оптимизации под целевые запросы
2. *Скорость загрузки* — необходимо проверить PageSpeed (рекомендуем > 70)
3. *Мобильная версия* — убедитесь в адаптивности (Google Mobile-First)
4. *Структура заголовков* — H1 должен быть один и содержать главный ключ
5. *Внутренняя перелинковка* — часть страниц может быть без ссылок

🟡 *Рекомендации:*

• Добавить страницы под низкочастотные запросы (длинный хвост)
• Настроить robots.txt и sitemap.xml
• Проверить дубли страниц (www / не-www, / в конце)
• Добавить микроразметку Schema.org

🟢 *Потенциал роста:*

По нише сайта обычно есть 50–200 запросов, которые легко занять за 4–8 недель при регулярной оптимизации.

──────────────────────
⚡ *AI-агент SEO-Драйв* находит эти точки роста еженедельно и сразу правит сайт."""

    return report


# ══════════════════════════════════════════════════════════════════════════════
#  ОНБОРДИНГ (подключение)
# ══════════════════════════════════════════════════════════════════════════════
async def onboard_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(ONBOARD_START_TEXT, parse_mode="Markdown")
    return ONBOARD_DOMAIN


async def onboard_domain(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["domain"] = update.message.text.strip()
    await update.message.reply_text(
        "Шаг 2/7 — ваше имя и email для связи (через пробел или на новой строке):"
    )
    return ONBOARD_CONTACTS


async def onboard_contacts(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["contacts"] = update.message.text.strip()
    await update.message.reply_text(
        "Шаг 3/7 — *MCP-токен WordPress*\n\n"
        "Это токен для автоматического редактирования сайта. "
        "Создаётся в WordPress: Пользователи → Профиль → Пароли приложений → Добавить.\n\n"
        "Введите токен или напишите *позже* (добавите после оплаты):",
        parse_mode="Markdown"
    )
    return ONBOARD_MCP


async def onboard_mcp(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["mcp_token"] = update.message.text.strip()
    await update.message.reply_text(
        "Шаг 4/7 — *Яндекс.Метрика*\n\n"
        "Введите номер счётчика (число) или напишите *нет*:",
        parse_mode="Markdown"
    )
    return ONBOARD_METRIKA


async def onboard_metrika(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["metrika"] = update.message.text.strip()
    await update.message.reply_text(
        "Шаг 5/7 — *Google Search Console*\n\n"
        "Пришлите email, добавленный в GSC, или напишите *нет*:",
        parse_mode="Markdown"
    )
    return ONBOARD_GSC


async def onboard_gsc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["gsc"] = update.message.text.strip()
    await update.message.reply_text(
        "Шаг 6/7 — *Конкуренты*\n\n"
        "Введите 2–5 сайтов конкурентов через запятую (например: rival1.ru, rival2.ru):"
    )
    return ONBOARD_COMPETITORS


async def onboard_competitors(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["competitors"] = update.message.text.strip()
    await update.message.reply_text(
        "Шаг 7/7 — *Ключевые слова*\n\n"
        "Введите 5–10 главных поисковых запросов вашего сайта через запятую:",
        parse_mode="Markdown"
    )
    return ONBOARD_KEYWORDS


async def onboard_keywords(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["keywords"] = update.message.text.strip()
    user = update.effective_user
    data = ctx.user_data

    summary = f"""✅ *Анкета заполнена!*

📌 Сайт: {data.get('domain')}
👤 Контакт: {data.get('contacts')}
🔑 MCP-токен: {'✓ получен' if data.get('mcp_token', '').lower() != 'позже' else '⏳ добавите позже'}
📊 Метрика: {data.get('metrika')}
🌐 GSC: {data.get('gsc')}
🏁 Конкуренты: {data.get('competitors')}
🎯 Ключи: {data.get('keywords')}

──────────────────────
💳 *Осталось оплатить: 2 000 ₽/мес*

После оплаты AI-агент начнёт первый цикл в ближайший понедельник.
"""
    await update.message.reply_text(
        summary,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Оплатить 2 000 ₽", url=YUKASSA_LINK)],
            [InlineKeyboardButton("✅ Я оплатил — подтвердить", callback_data="payment_confirm")],
        ])
    )

    # Уведомление администратору
    if ADMIN_ID:
        admin_msg = (
            f"🆕 Новая заявка!\n"
            f"@{user.username} (id: {user.id})\n"
            f"Сайт: {data.get('domain')}\n"
            f"Контакт: {data.get('contacts')}\n"
            f"Метрика: {data.get('metrika')}\n"
            f"GSC: {data.get('gsc')}\n"
            f"Конкуренты: {data.get('competitors')}\n"
            f"Ключи: {data.get('keywords')}\n"
            f"MCP: {data.get('mcp_token')}"
        )
        await ctx.bot.send_message(ADMIN_ID, admin_msg)

    return WAIT_PAYMENT


async def payment_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user  = update.effective_user
    data  = ctx.user_data

    # Запись в Google Sheets
    await save_to_sheets(user, data)

    await query.message.reply_text(
        "🎉 *Отлично! Спасибо за оплату.*\n\n"
        "Ваш AI-агент уже настраивается. В ближайший понедельник он:\n"
        "• Проанализирует сайт и конкурентов\n"
        "• Найдёт лучшие запросы через Wordstat и подсказки\n"
        "• Внесёт первые правки на сайт\n"
        "• Пришлёт вам отчёт\n\n"
        f"📺 Подпишитесь на канал {CHANNEL} — там выходят советы и кейсы.\n\n"
        "Если появятся вопросы — пишите сюда.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"📺 Подписаться на {CHANNEL}", url="https://t.me/seodrive_ai")],
        ])
    )

    # Уведомление администратору
    if ADMIN_ID:
        await ctx.bot.send_message(
            ADMIN_ID,
            f"💰 ОПЛАТА ПОДТВЕРЖДЕНА!\n@{user.username} (id: {user.id})\nСайт: {data.get('domain')}"
        )

    return ConversationHandler.END


async def save_to_sheets(user, data: dict):
    """
    Запись клиента в Google Sheets.
    Требует: SHEETS_ID в .env и файл credentials.json от Google Service Account.
    """
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds  = Credentials.from_service_account_file("credentials.json", scopes=scopes)
        gc     = gspread.authorize(creds)
        sh     = gc.open_by_key(SHEETS_ID)
        ws     = sh.sheet1

        row = [
            str(user.id),
            f"@{user.username}",
            data.get("domain", ""),
            data.get("mcp_token", ""),
            data.get("metrika", ""),
            data.get("gsc", ""),
            data.get("competitors", ""),
            data.get("keywords", ""),
            data.get("contacts", ""),
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            "активен",
        ]
        ws.append_row(row)
        logger.info(f"Saved to Sheets: {user.id}")
    except Exception as e:
        logger.error(f"Sheets error: {e}")


# ── Служебные хендлеры ────────────────────────────────────────────────────────
async def main_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(WELCOME_TEXT, parse_mode="Markdown", reply_markup=main_keyboard())


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Хорошо, остановились. Возвращайтесь, когда будете готовы!",
        reply_markup=main_keyboard()
    )
    return ConversationHandler.END


async def fallback_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Используйте кнопки ниже или команду /start:",
        reply_markup=main_keyboard()
    )


# ── Сборка приложения ─────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    audit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(audit_start, pattern="^audit_start$")],
        states={
            AUDIT_DOMAIN:  [MessageHandler(filters.TEXT & ~filters.COMMAND, audit_get_domain)],
            AUDIT_METRIKA: [MessageHandler(filters.TEXT & ~filters.COMMAND, audit_get_metrika)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    onboard_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(onboard_start, pattern="^onboard_start$")],
        states={
            ONBOARD_DOMAIN:      [MessageHandler(filters.TEXT & ~filters.COMMAND, onboard_domain)],
            ONBOARD_CONTACTS:    [MessageHandler(filters.TEXT & ~filters.COMMAND, onboard_contacts)],
            ONBOARD_MCP:         [MessageHandler(filters.TEXT & ~filters.COMMAND, onboard_mcp)],
            ONBOARD_METRIKA:     [MessageHandler(filters.TEXT & ~filters.COMMAND, onboard_metrika)],
            ONBOARD_GSC:         [MessageHandler(filters.TEXT & ~filters.COMMAND, onboard_gsc)],
            ONBOARD_COMPETITORS: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboard_competitors)],
            ONBOARD_KEYWORDS:    [MessageHandler(filters.TEXT & ~filters.COMMAND, onboard_keywords)],
            WAIT_PAYMENT:        [CallbackQueryHandler(payment_confirm, pattern="^payment_confirm$")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(audit_conv)
    app.add_handler(onboard_conv)
    app.add_handler(CallbackQueryHandler(main_menu, pattern="^main_menu$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_text))

    logger.info("Бот запущен.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
