import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]
LOCAL_API = os.environ["LOCAL_BOT_API"]

STORAGE_CHAT_ID = -1003947631814
CHANNEL = "@ZynAnimeHub"
REQUIRED_CHANNEL = "@ZynAnime"
BOT_USERNAME = "ZynAnimeBot"

ANIME = {
    "dating_sim": {
        "title": "Trapped in a Dating Sim",
        "seasons": {
            "s1": {
                "name": "Season 1",
                "episodes": {
                    "480p": {
                        1: 3, 2: 4, 3: 5, 4: 6, 5: 7, 6: 8,
                        7: 9, 8: 10, 9: 11, 10: 12, 11: 13, 12: 19
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
                        await send_quality_request(
                            update,
                            anime_id,
                            season_id,
                            quality
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


async def send_quality_request(update, anime_id, season_id, quality):

    keyboard = [
        [
            InlineKeyboardButton(
                "📢 Join Channel",
                url="https://t.me/zynanime"
            )
        ],
        [
            InlineKeyboardButton(
                "🔄 Try Again",
                callback_data=f"check|{anime_id}|{season_id}|{quality}"
            )
        ]
    ]

    await update.message.reply_text(
        "🔒 Please join our channel first to get these files.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def post(update: Update, context: ContextTypes.DEFAULT_TYPE):

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

    await update.message.reply_text(
        "✅ Season 1 and Season 2 posted successfully."
    )


async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    _, anime_id, season_id, quality = query.data.split("|")

    try:
        member = await context.bot.get_chat_member(
            chat_id=REQUIRED_CHANNEL,
            user_id=query.from_user.id
        )

        if member.status not in ["member", "administrator", "creator"]:

            keyboard = [
                [
                    InlineKeyboardButton(
                        "📢 Join Channel",
                        url="https://t.me/zynanime"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔄 Try Again",
                        callback_data=f"check|{anime_id}|{season_id}|{quality}"
                    )
                ]
            ]

            await query.message.reply_text(
                "❌ Please join this channel first to get these files.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        # Joined successfully
        anime = ANIME[anime_id]
        season = anime["seasons"][season_id]
        episodes = season["episodes"].get(quality, {})

        if not episodes:
            await query.message.reply_text(
                f"❌ {quality} is not available yet."
            )
            return

        await query.message.reply_text(
            f"✅ Joined successfully!\n\n"
            f"🎬 Sending {anime['title']} — {season['name']}\n"
            f"🎞 Quality: {quality}\n\n"
            "Please wait while I send all available episodes..."
        )

        # Send episodes in order
        for ep in sorted(episodes.keys()):

            message_id = episodes[ep]

            keyboard = [
    [
        InlineKeyboardButton(
            "ZynAnimeHub",
            url="https://t.me/ZynAnimeHub"
        ),
        InlineKeyboardButton(
            "ZynAnime",
            url="https://t.me/zynanime"
        )
    ]
]

await context.bot.send_message(
    chat_id=query.from_user.id,
    text=(
        f"🏁 END OF {season['name'].upper()}\n\n"
        f"🎬 {anime['title']}\n"
        f"🎞 Quality: {quality}\n\n"
        "📺 Follow our channels for more anime:"
    ),
    reply_markup=InlineKeyboardMarkup(keyboard)
)

    except Exception:
        await query.message.reply_text(
            "⚠️ Please make sure you joined @ZynAnime, then tap Try Again."
        )


app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("post", post))

app.add_handler(
    CallbackQueryHandler(
        check_membership,
        pattern=r"^check\|"
    )
)

app.run_polling()
