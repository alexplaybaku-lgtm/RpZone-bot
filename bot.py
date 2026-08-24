import os
import asyncio
from threading import Thread

from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = 6754793977
PORT = int(os.environ.get("PORT", 10000))
RENDER_URL = os.environ["RENDER_EXTERNAL_URL"]

MAIN_LOOP = None

app = Flask(__name__)

telegram_app = Application.builder().token(BOT_TOKEN).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 👋\n"
        "Напиши сюда сообщение, и оно будет передано администратору."
    )


async def user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    username = f"@{user.username}" if user.username else "нет username"

    text = (
        "📩 Новое сообщение\n\n"
        f"👤 Имя: {user.full_name}\n"
        f"🔹 Username: {username}\n"
        f"🆔 ID: {user.id}\n\n"
        f"💬 Сообщение:\n{message.text}"
    )

    keyboard = [[
        InlineKeyboardButton(
            "💬 Ответить",
            callback_data=f"reply:{user.id}"
        )
    ]]

    await telegram_app.bot.send_message(
        chat_id=ADMIN_ID,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    await message.reply_text("✅ Сообщение отправлено!")


async def reply_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    user_id = int(query.data.split(":")[1])
    context.user_data["reply_to"] = user_id

    await query.message.reply_text(
        "✍️ Напиши сообщение, которое нужно отправить пользователю."
    )


async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    user_id = context.user_data.get("reply_to")

    if not user_id:
        return

    await telegram_app.bot.send_message(
        chat_id=user_id,
        text=f"📩 Ответ администратора:\n\n{update.message.text}",
    )

    await update.message.reply_text("✅ Ответ отправлен!")
    context.user_data.pop("reply_to", None)


telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CallbackQueryHandler(reply_button))

telegram_app.add_handler(
    MessageHandler(
        filters.TEXT & filters.User(ADMIN_ID),
        admin_reply
    )
)

telegram_app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.User(ADMIN_ID),
        user_message
    )
)


@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)

    if MAIN_LOOP is not None:
        asyncio.run_coroutine_threadsafe(
            telegram_app.update_queue.put(update),
            MAIN_LOOP
        )

    return "OK"


@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"


def run_flask():
    app.run(
        host="0.0.0.0",
        port=PORT
    )


async def start_bot():
    await telegram_app.initialize()
    await telegram_app.start()

    await telegram_app.bot.delete_webhook(
        drop_pending_updates=True
    )

    await telegram_app.bot.set_webhook(
        url=f"{RENDER_URL}/telegram",
        drop_pending_updates=True
    )

    print(
        f"Webhook set to: {RENDER_URL}/telegram"
    )


def main():
    global MAIN_LOOP

    async def runner():
        global MAIN_LOOP

        MAIN_LOOP = asyncio.get_running_loop()

        await start_bot()

        Thread(
            target=run_flask,
            daemon=True
        ).start()

        await asyncio.Event().wait()

    asyncio.run(runner())


if __name__ == "__main__":
    main()
    
        
