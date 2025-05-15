import os
import logging
from groq import Groq
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# Logging
logging.basicConfig(level=logging.INFO)

# Groq API
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Ключі для вибору мови
LANGUAGE, CHAT = range(2)

# Створюємо кнопки
language_keyboard = ReplyKeyboardMarkup(
    [["🇺🇦 Українська", "🇷🇺 Русский", "🇬🇧 English"]],
    one_time_keyboard=True,
    resize_keyboard=True
)

# Вибір мови
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! Обери мову для спілкування:",
        reply_markup=language_keyboard
    )
    return LANGUAGE

# Зберігаємо мову
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.message.text
    if "Українська" in lang:
        context.user_data["lang"] = "uk"
    elif "Русский" in lang:
        context.user_data["lang"] = "ru"
    elif "English" in lang:
        context.user_data["lang"] = "en"
    else:
        await update.message.reply_text("Будь ласка, обери мову з кнопок.")
        return LANGUAGE

    await update.message.reply_text("Мову встановлено ✅", reply_markup=ReplyKeyboardRemove())
    return CHAT

# Відповідь AI
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    lang = context.user_data.get("lang", "uk")  # за замовчуванням — укр

    prompt = {
        "uk": f"Відповідай українською: {user_message}",
        "ru": f"Отвечай по-русски: {user_message}",
        "en": f"Answer in English: {user_message}",
    }[lang]

    try:
        response = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150
        )
        reply = response.choices[0].message.content
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f"Помилка: {e}")

# Запуск
def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_language)],
            CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)]
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
