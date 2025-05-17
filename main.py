import os
import asyncio
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)
from groq import Groq

# Змінні середовища
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))

# Ініціалізація
bot = Bot(token=TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)
app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

user_data = {}

# Головна сторінка (перевірка статусу)
@app.route('/')
def index():
    return "✅ Бот працює!"

# Webhook для Telegram
@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.process_update(update)
    return "ok"

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {"lang": "uk"}
    await update.message.reply_text("Привіт! Напиши мені щось!")

# Обробка повідомлень
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text

    lang = user_data.get(user_id, {}).get("lang", "uk")
    prompt = {
        "uk": f"Відповідай українською: {message}",
        "ru": f"Отвечай по-русски: {message}",
        "en": f"Answer in English: {message}",
    }[lang]

    try:
        response = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150
        )
        await update.message.reply_text(response.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text(f"❌ Помилка: {e}")

# Додаємо хендлери
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

# Запуск сервера + встановлення webhook
if __name__ == "__main__":
    async def setup():
        await bot.delete_webhook()
        await bot.set_webhook(url=f"https://tgbotai2-seui.onrender.com/webhook/{TOKEN}")
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

    asyncio.run(setup())
