import logging
import json
import os
import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ApplicationBuilder,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TOKEN_HERE")
DATA_FILE = "tomato_users.json"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def load_users() -> dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading users: {e}")
    return {}

def save_users(users: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    users = load_users()

    if chat_id in users:
        planting_date = users[chat_id]["planting_date"]
        await update.message.reply_text(
            f"🌱 Вы уже зарегистрированы!\n"
            f"📅 Дата посадки: {planting_date}\n\n"
            f"Напоминания о поливе приходят каждый день в 12:00.\n"
            f"Используйте /status, чтобы проверить состояние."
        )
        return

    today_dt = datetime.now()
    today_str = today_dt.strftime("%d.%m.%Y")
    users[chat_id] = {
        "planting_date": today_str,
        "planting_datetime": today_dt.isoformat(),
    }
    save_users(users)

    await update.message.reply_text(
        f"🍅 *Привет! Я помогу вырастить ваши черри!*\n\n"
        f"📅 Дата посадки: {today_str}\n\n"
        f"Что я буду делать:\n"
        f"💧 Каждый день в 12:00 — напоминание о поливе\n"
        f"🌿 На 7-й и 10-й день — проверка всходов\n\n"
        f"_Советы по уходу:_\n"
        f"• Температура: 20–25°C, светлое место\n"
        f"• Полив: 2–4 ложки, когда почва сухая\n"
        f"• Опрыскивание: когда появятся ростки\n\n"
        f"Удачи! 🌱",
        parse_mode="Markdown"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    users = load_users()

    if chat_id not in users:
        await update.message.reply_text("❌ Вы еще не начали. Введите /start!")
        return

    planting_dt = datetime.fromisoformat(users[chat_id]["planting_datetime"])
    days_passed = (datetime.now() - planting_dt).days
    planting_date = users[chat_id]["planting_date"]

    if days_passed < 7:
        sprout_status = f"⏳ Еще {7 - days_passed} дн. до всходов (обычно 7–10 дней)."
    elif days_passed <= 10:
        sprout_status = "👀 Самое время проверить ростки!"
    else:
        sprout_status = "🌿 Ростки уже должны быть! Следите за светом."

    await update.message.reply_text(
        f"📊 *Статус рассады*\n\n"
        f"📅 Посажено: {planting_date}\n"
        f"🗓 Прошло дней: {days_passed}\n\n"
        f"{sprout_status}",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🍅 *Команды:*\n/start — начать\n/status — статус\n/help — помощь",
        parse_mode="Markdown"
    )

async def send_daily_watering_reminder(application: Application):
    users = load_users()
    for chat_id in users:
        try:
            await application.bot.send_message(
                chat_id=int(chat_id),
                text="💧 *Пора проверить помидорки!*\nЕсли почва сухая — полейте (2-4 ложки).",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.warning(f"Could not send to {chat_id}: {e}")

async def send_sprout_check_reminder(application: Application, chat_id: str, day: int):
    try:
        await application.bot.send_message(
            chat_id=int(chat_id),
            text=f"🌿 *День {day}!* Проверьте всходы. Если они есть — переставьте на свет!",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.warning(f"Could not send sprout reminder to {chat_id}: {e}")

async def post_init(application: Application):
    scheduler = AsyncIOScheduler()
    
    scheduler.add_job(
        send_daily_watering_reminder,
        trigger=CronTrigger(hour=12, minute=0),
        args=[application],
        id="daily_watering",
        replace_existing=True
    )

    users = load_users()
    for chat_id, data in users.items():
        planting_dt = datetime.fromisoformat(data["planting_datetime"])
        for day in [7, 10]:
            remind_dt = planting_dt + timedelta(days=day)
            if remind_dt > datetime.now():
                scheduler.add_job(
                    send_sprout_check_reminder,
                    trigger=DateTrigger(run_date=remind_dt),
                    args=[application, chat_id, day],
                    id=f"sprout_{chat_id}_{day}",
                    replace_existing=True
                )
    
    scheduler.start()

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("help", help_command))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()