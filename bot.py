import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]
LOCAL_API = os.environ["LOCAL_BOT_API"]

STORAGE_CHAT_ID = -1003947631814
CHANNEL = "@ZynAnimeHub"
BOT_USERNAME = "ZynAnimeBot"


# ============================================================
# ANIME DATABASE
# Add new anime/seasons/qualities here later
# ============================================================

ANIME = {
    "dating_sim_s1": {
        "title": "Trapped in a Dating Sim",
        "season": "Season 1",

        "episodes": {
            "480p": {
                1: 3,
                2: 4,
                3: 5,
                4: 6,
                5: 7,
                6: 8,
                7: 9,
                8: 10,
                9: 11,
                10: 12,
                11: 13,
                12: 19
            },

            "720p": {},
            "1080p": {}
        }
    }
}


app = (
    Application.builder()
    .token(TOKEN)
    .base_url(LOCAL_API + "/bot")
    .base_file_url(LOCAL_API + "/file/bot")
    .local_mode(True)
    .build()
)


# ============================================================
# START
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    args = context.args

    # Someone came from an anime/quality button
    if args:
        payload = args[0]

        if "-" in payload:
            anime_id, quality_name = payload.rsplit("-", 1)

            anime = ANIME.get(anime_id)

            if anime:
                episodes = anime["episodes"].get(quality_name, {})

                if episodes:
                    keyboard = [
                        [
                            InlineKeyboardButton(
                                f"Episode {ep}",
                                callback_data=f"ep|{anime_id}|{quality_name}|{ep}"
                            )
                        ]
                        for ep in episodes
                    ]

                    await update.message.reply_text(
                        f"🎬 {anime['title']}\n"
                        f"📺 {anime['season']}\n"
                        f"🎞 Quality: {quality_name}\n\n"
                        "Choose an episode:",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    return

                await update.message.reply_text(
                    f"❌ {quality_name} is not available yet."
                )
                return

    # Normal /start
    keyboard = [
        [
            InlineKeyboardButton(
                "📺 Browse Anime",
                url="https://t.me/ZynAnimeHub"
            )
        ]
    ]

    await update.message.reply_text(
        "🎬 Welcome to Zyn Anime Bot!\n\n"
        "📚 Find your anime in our main channel:\n"
        "👉 Zyn Anime Hub\n\n"
        "Select an anime there and choose your preferred quality.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ============================================================
# POST ANIME TO CHANNEL
# ============================================================

async def post(update: Update, context: ContextTypes.DEFAULT_TYPE):

    anime_id = context.args[0] if context.args else "dating_sim_s1"

    anime = ANIME.get(anime_id)

    if not anime:
        await update.message.reply_text(
            "❌ Anime not found."
        )
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "480p",
                url=f"https://t.me/{BOT_USERNAME}?start={anime_id}-480p"
            ),
            InlineKeyboardButton(
                "720p",
                url=f"https://t.me/{BOT_USERNAME}?start={anime_id}-720p"
            )
        ],
        [
            InlineKeyboardButton(
                "1080p",
                url=f"https://t.me/{BOT_USERNAME}?start={anime_id}-1080p"
            )
        ]
    ]

    await context.bot.send_message(
        chat_id=CHANNEL,
        text=(
            f"🎬 {anime['title']} — {anime['season']}\n\n"
            "📺 Choose your quality:"
        ),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text(
        f"✅ {anime['title']} posted to Zyn Anime Hub."
    )


# ============================================================
# EPISODE DELIVERY
# ============================================================

async def episode(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    _, anime_id, quality_name, ep = query.data.split("|")

    ep = int(ep)

    anime = ANIME.get(anime_id)

    if not anime:
        await query.message.reply_text(
            "❌ Anime not found."
        )
        return

    message_id = anime["episodes"].get(quality_name, {}).get(ep)

    if not message_id:
        await query.message.reply_text(
            "❌ This episode is not available."
        )
        return

    await context.bot.copy_message(
        chat_id=query.from_user.id,
        from_chat_id=STORAGE_CHAT_ID,
        message_id=message_id
    )


# ============================================================
# HANDLERS
# ============================================================

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("post", post))

app.add_handler(
    CallbackQueryHandler(
        episode,
        pattern=r"^ep\|"
    )
)


app.run_polling()
