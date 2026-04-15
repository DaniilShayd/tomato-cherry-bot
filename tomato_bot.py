"""
🍅 Tomato Cherry Seedling Bot
Sends daily watering reminders at 12:00 and sprout check alerts on day 7 and 10.

Install:
    pip install python-telegram-bot apscheduler

Run:
    python tomato_bot.py
"""

import logging
import json
import os
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

# ─── Configuration ────────────────────────────────────────────────────────────

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TOKEN_HERE")  # Token from @BotFather
DATA_FILE = "tomato_users.json"  # File for storing user data

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── User Storage ─────────────────────────────────────────────────────────────

def load_users() -> dict:
    """Load user data from JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users: dict):
    """Save user data to JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# ─── Bot Commands ─────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start command — register user and record planting date."""
    chat_id = str(update.effective_chat.id)
    users = load_users()

    # If user is already registered, show existing info
    if chat_id in users:
        planting_date = users[chat_id]["planting_date"]
        await update.message.reply_text(
            f"🌱 You are already registered!\n"
            f"📅 Planting date: {planting_date}\n\n"
            f"Watering reminders are sent every day at 12:00.\n"
            f"Use /status to check your seedling status."
        )
        return

    # Register new user with today's date
    today = datetime.now().strftime("%d.%m.%Y")
    users[chat_id] = {
        "planting_date": today,
        "planting_datetime": datetime.now().isoformat(),
    }
    save_users(users)

    await update.message.reply_text(
        f"🍅 *Hello! I'll help you grow your cherry tomatoes!*\n\n"
        f"📅 Planting date: {today}\n\n"
        f"Here's what I'll do:\n"
        f"💧 Every day at 12:00 — watering reminder\n"
        f"🌿 On day 7 and day 10 — sprout check reminder\n\n"
        f"_Care instructions:_\n"
        f"• Temperature: 20–25°C, place in a bright spot\n"
        f"• Water with 2–4 tablespoons when soil is dry\n"
        f"• Use misting once sprouts appear\n\n"
        f"Good luck! 🌱",
        parse_mode="Markdown"
    )
    logger.info(f"New user registered: {chat_id}")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/status command — show current seedling status."""
    chat_id = str(update.effective_chat.id)
    users = load_users()

    if chat_id not in users:
        await update.message.reply_text(
            "❌ You are not registered yet. Send /start to begin!"
        )
        return

    planting_dt = datetime.fromisoformat(users[chat_id]["planting_datetime"])
    days_passed = (datetime.now() - planting_dt).days
    planting_date = users[chat_id]["planting_date"]

    # Determine sprout status based on days elapsed
    if days_passed < 7:
        days_left = 7 - days_passed
        sprout_status = f"⏳ {days_left} more day(s) until sprouts may appear (7–10 days)"
    elif days_passed <= 10:
        sprout_status = "👀 Now is the time — check if sprouts have appeared!"
    else:
        sprout_status = "🌿 Sprouts should have appeared by now! Watch them grow."

    await update.message.reply_text(
        f"📊 *Seedling Status*\n\n"
        f"📅 Planted: {planting_date}\n"
        f"🗓 Days passed: {days_passed}\n\n"
        f"{sprout_status}\n\n"
        f"💧 Don't forget to check soil moisture every day!",
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help command — show available commands."""
    await update.message.reply_text(
        "🍅 *Bot Commands:*\n\n"
        "/start — register and record your planting date\n"
        "/status — check current seedling status\n"
        "/help — show this help message\n\n"
        "Reminders are sent automatically every day at 12:00 🕛",
        parse_mode="Markdown"
    )


# ─── Scheduler: Daily Reminders ───────────────────────────────────────────────

async def send_daily_watering_reminder(application):
    """Send watering reminder to all registered users at 12:00."""
    users = load_users()
    if not users:
        return

    for chat_id in users:
        try:
            await application.bot.send_message(
                chat_id=int(chat_id),
                text=(
                    "💧 *Time to check your tomato seedlings!*\n\n"
                    "Touch the soil — if it's dry, water with 2–4 tablespoons.\n"
                    "🌡 Make sure the temperature is 20–25°C.\n\n"
                    "Send /status to see your sprout progress 🌱"
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.warning(f"Failed to send message to {chat_id}: {e}")


async def send_sprout_check_reminder(application, chat_id: str, day: int):
    """Send sprout check reminder on day 7 or day 10 after planting."""
    users = load_users()
    if chat_id not in users:
        return

    try:
        await application.bot.send_message(
            chat_id=int(chat_id),
            text=(
                f"🌿 *Day {day} after planting!*\n\n"
                "Take a look at your pot — "
                "check if the first sprouts have appeared!\n\n"
                "If you see green shoots:\n"
                "• Switch to misting instead of direct watering 💦\n"
                "• Move the pot to the brightest spot available 🌞\n\n"
                "Good luck! 🍅"
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.warning(f"Failed to send sprout reminder to {chat_id}: {e}")


def schedule_sprout_reminders(scheduler: AsyncIOScheduler, application):
    """
    Schedule sprout check reminders for all existing users on bot startup.
    Only schedules reminders that haven't passed yet (within 10 days of planting).
    """
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
                    id=f"sprout_{chat_id}_day{day}",
                    replace_existing=True,
                )
                logger.info(f"Scheduled sprout reminder for {chat_id} on day {day}: {remind_dt}")


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    """Initialize and start the bot."""
    app = Application.builder().token(BOT_TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("help", help_command))

    # Initialize scheduler
    scheduler = AsyncIOScheduler()

    # Schedule daily watering reminder at 12:00
    scheduler.add_job(
        send_daily_watering_reminder,
        trigger=CronTrigger(hour=12, minute=0),
        args=[app],
        id="daily_watering",
    )

    # On startup, reschedule any pending sprout reminders for existing users
    async def post_init(application):
        schedule_sprout_reminders(scheduler, application)

    app.post_init = post_init
    scheduler.start()

    logger.info("🍅 Bot is running! Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()