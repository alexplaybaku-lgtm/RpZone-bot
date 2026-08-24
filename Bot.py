import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

ADMIN_ID = 6754793977


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 👋\nНапиши сюда своё сообщение, и оно будет передано администратору."
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
            callback_data=f"reply_{user.id}"
        )
    ]]

    await context.bot.send_message(
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

    user_id = int(query.data.split("_")[1])

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

    await context.bot.send_message(
        chat_id=user_id,
        text=f"📩 Ответ администратора:\n\n{update.message.text}",
    )

    await update.message.reply_text("✅ Ответ отправлен!")

    context.user_data.pop("reply_to", None)


def main():
    token = os.environ["BOT_TOKEN"]

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(reply_button))
    app.add_handler(
        MessageHandler(
            filters.TEXT & filters.User(ADMIN_ID),
            admin_reply
        )
    )
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.User(ADMIN_ID),
            user_message
        )
    )

    app.run_polling()


if __name__ == "__main__":
    main()
