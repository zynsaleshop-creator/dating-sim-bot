import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        quality = context.args[0]
        await update.message.reply_text(
            f"Selected: {quality}\n\n"
            "Episode files will appear here."
        )
    else:
        await update.message.reply_text(
            "Welcome! Choose a quality from the channel."
        )

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))

app.run_polling()
