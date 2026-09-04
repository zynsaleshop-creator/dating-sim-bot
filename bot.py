import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]
LOCAL_API = os.environ["LOCAL_BOT_API"]

STORAGE_CHAT_ID = -1003947631814
EPISODE_8_MESSAGE_ID = 2

app = (
    Application.builder()
    .token(TOKEN)
    .base_url(LOCAL_API + "/bot")
    .base_file_url(LOCAL_API + "/file/bot")
    .local_mode(True)
    .build()
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton("480p", callback_data="480p"),
        InlineKeyboardButton("720p", callback_data="720p"),
        InlineKeyboardButton("1080p", callback_data="1080p")
    ]]

    await update.message.reply_text(
        "Choose your video quality:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "480p":
        await context.bot.copy_message(
            chat_id=query.from_user.id,
            from_chat_id=STORAGE_CHAT_ID,
            message_id=EPISODE_8_MESSAGE_ID
        )
    else:
        await query.message.reply_text(
            "This quality is not available yet."
        )

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(quality))

app.run_polling()
