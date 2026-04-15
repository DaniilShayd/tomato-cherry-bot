# 🍅 Tomato Cherry Bot

A Telegram bot for tracking cherry tomato seedlings.  
Sends daily watering reminders and alerts you when sprouts are expected.

---

## Features

- 💧 Every day at **12:00** — reminder to check soil moisture
- 🌿 On **day 7 and day 10** after planting — reminder to check for sprouts
- 📊 `/status` command — shows how many days have passed since planting

## Commands

| Command   | Description                            |
| --------- | -------------------------------------- |
| `/start`  | Register and record your planting date |
| `/status` | Check current seedling status          |
| `/help`   | Show help                              |

## Run Locally

```bash
pip install -r requirements.txt
python tomato_bot.py
```

## Deploy on Railway

1. Fork this repository
2. Create a new project on [railway.app](https://railway.app)
3. Connect the repository
4. Add the environment variable:
   ```
   BOT_TOKEN=your_token_from_BotFather
   ```
