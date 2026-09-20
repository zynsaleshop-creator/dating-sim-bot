import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]
LOCAL_API = os.environ["LOCAL_BOT_API"]

STORAGE_CHAT_ID = -1003947631814
CHANNEL = "@ZynAnimeHub"
BOT_USERNAME = "ZynAnimeBot"


ANIME = {

    "dating_sim": {
        "title": "Trapped in a Dating Sim",

        "seasons": {
            "s1": {
                "name": "Season 1",
                "episodes": {
                    "480p": {
                        1: 3, 2: 4, 3: 5, 4: 6,
                        5: 7, 6: 8, 7: 9, 8: 10,
                        9: 11, 10: 12, 11: 13, 12: 19
                    },
                    "720p": {},
                    "1080p": {}
                }
            },

            "s2": {
                "name": "Season 2",
                "episodes": {
                    "480p": {
                        1: 14, 2: 15, 3: 16, 4: 17, 5: 18,
                        6: 20, 7: 21, 8: 22, 9: 23, 10: 24
                    },
                    "720p": {},
                    "1080p": {}
                }
            }
        }
    },


    "tomodachi_game": {
        "title": "Tomodachi Game",

        "seasons": {
            "s1": {
                "name": "Season 1",
                "episodes": {
                    "480p": {},
                    "720p": {},
                    "1080p": {}
                }
            }
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    args = context.args

    if args:
        parts = args[0].split("-")

        if len(parts) == 3:
            anime_id, season_id, quality = parts

            anime = ANIME.get(anime_id)

            if anime:
                season = anime["seasons"].get(season_id)

                if season:
                    episodes = season["episodes"].get(quality, {})

                    if episodes:

                        keyboard = [
                            [
                                InlineKeyboardButton(
                                    f"Episode {ep}",
                                    callback_data=f"ep|{anime_id}|{season_id}|{quality}|{ep}"
                                )
                            ]
                            for ep in episodes
                        ]

                        await update.message.reply_text(
                            f"🎬 {anime['title']}\n"
                            f"📺 {season['name']}\n"
                            f"🎞 Quality: {quality}\n\n"
                            "Choose an episode:",
                            reply_markup=InlineKeyboardMarkup(keyboard)
                        )
                        return

                    await update.message.reply_text(
                        f"❌ {quality} is not available yet."
                    )
                    return

    keyboard = [[
        InlineKeyboardButton(
            "📺 Browse Anime",
            url="https://t.me/ZynAnimeHub"
        )
    ]]

    await update.message.reply_text(
        "🎬 Welcome to Zyn Anime Bot!\n\n"
        "📚 Find your anime in our main channel:\n"
        "👉 Zyn Anime Hub\n\n"
        "Select an anime there and choose your preferred quality.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def post(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Dating Sim — Season 1
    anime = ANIME["dating_sim"]

    for season_id, season in anime["seasons"].items():

        keyboard = [
            [
                InlineKeyboardButton(
                    "480p",
                    url=f"https://t.me/{BOT_USERNAME}?start=dating_sim-{season_id}-480p"
                ),
                InlineKeyboardButton(
                    "720p",
                    url=f"https://t.me/{BOT_USERNAME}?start=dating_sim-{season_id}-720p"
                )
            ],
            [
                InlineKeyboardButton(
                    "1080p",
                    url=f"https://t.me/{BOT_USERNAME}?start=dating_sim-{season_id}-1080p"
                )
            ]
        ]

        await context.bot.send_message(
            chat_id=CHANNEL,
            text=(
                f"🎬 {anime['title']} — {season['name']}\n\n"
                "📺 Choose your quality:"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # Tomodachi Game — Season 1
    anime = ANIME["tomodachi_game"]

    for season_id, season in anime["seasons"].items():

        keyboard = [
            [
                InlineKeyboardButton(
                    "480p",
                    url=f"https://t.me/{BOT_USERNAME}?start=tomodachi_game-{season_id}-480p"
                ),
                InlineKeyboardButton(
                    "720p",
                    url=f"https://t.me/{BOT_USERNAME}?start=tomodachi_game-{season_id}-720p"
                )
            ],
            [
                InlineKeyboardButton(
                    "1080p",
                    url=f"https://t.me/{BOT_USERNAME}?start=tomodachi_game-{season_id}-1080p"
                )
            ]
        ]

        await context.bot.send_message(
            chat_id=CHANNEL,
            text=(
                f"🎬 {anime['title']} — {season['name']}\n\n"
                "📺 Choose your quality:"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    await update.message.reply_text(
        "✅ Anime posts created successfully."
    )


async def episode(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    _, anime_id, season_id, quality, ep = query.data.split("|")

    ep = int(ep)

    anime = ANIME.get(anime_id)

    if not anime:
        await query.message.reply_text("❌ Anime not found.")
        return

    season = anime["seasons"].get(season_id)

    if not season:
        await query.message.reply_text("❌ Season not found.")
        return

    message_id = season["episodes"].get(quality, {}).get(ep)

    if not message_id:
        await query.message.reply_text(
            "❌ This episode is not available yet."
        )
        return

    await context.bot.copy_message(
        chat_id=query.from_user.id,
        from_chat_id=STORAGE_CHAT_ID,
        message_id=message_id
    )


app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("post", post))

app.add_handler(
    CallbackQueryHandler(
        episode,
        pattern=r"^ep\|"
    )
)

app.run_polling()
