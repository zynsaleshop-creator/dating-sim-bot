import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]
LOCAL_API = os.environ["LOCAL_BOT_API"]

STORAGE_CHAT_ID = -1003947631814

EPISODES_480P = {
    1: 3, 2: 4, 3: 5, 4: 6, 5: 7, 6: 8,
    7: 9, 8: 10, 9: 11, 10: 12, 11: 13, 12: 19
}

app = (
    Application.builder()
    .token(TOKEN)
    .base_url(LOCAL_API + "/bot")
    .base_file_url(LOCAL_API + "/file/bot")
    .local_mode(True)
    .build()
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quality = context.args[0] if context.args else None

    if quality == "480p":
        keyboard = [
            [InlineKeyboardButton(f"Episode {ep}", callback_data=f"ep_{ep}")]
            for ep in EPISODES_480P
        ]

        await update.message.reply_text(
            "📺 480p — Choose an episode:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if quality in ["720p", "1080p"]:
        await update.message.reply_text(
            f"📺 {quality}\n\nEpisodes are not available yet."
        )
        return

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
        keyboard = [
            [InlineKeyboardButton(f"Episode {ep}", callback_data=f"ep_{ep}")]
            for ep in EPISODES_480P
        ]
        await query.message.reply_text(
            "📺 480p — Choose an episode:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.message.reply_text(
            f"📺 {query.data}\n\nEpisodes are not available yet."
        )

async def episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    ep = int(query.data.split("_")[1])

    await context.bot.copy_message(
        chat_id=query.from_user.id,
        from_chat_id=STORAGE_CHAT_ID,
        message_id=EPISODES_480P[ep]
    )

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(quality, pattern="^(480p|720p|1080p)$"))
app.add_handler(CallbackQueryHandler(episode, pattern="^ep_"))

app.run_polling()
