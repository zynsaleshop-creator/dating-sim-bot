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
        "title": "Trapped in a Dating Sim: The World of Otome Games Is Tough for Mobs",
        "japanese_title": "Otomege Sekai wa Mob ni Kibishii Sekai desu",

        "description":
            "Office worker Leon is reincarnated into a particularly punishing dating sim "
            "where women reign supreme and only beautiful men have a seat at the table. "
            "But Leon has a secret weapon: he remembers everything from his past life, "
            "including a complete playthrough of the game in which he is now trapped. "
            "Watch Leon spark a revolution to change this new world in order to fulfill "
            "his ultimate desire... of living a quiet, easy life in the countryside!",

        "details": {
            "genres": "Action, Fantasy, Mecha, Romance",
            "type": "TV",
            "rating": "71",
            "status": "FINISHED",
            "first_aired": "2022-4-3",
            "last_aired": "2022-6-19",
            "runtime": "24 minutes"
        },

        "seasons": {

            "s1": {
                "name": "Season 1",
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
            },

            "s2": {
                "name": "Season 2",
                "episodes": {
                    "480p": {
                        1: 14,
                        2: 15,
                        3: 16,
                        4: 17,
                        5: 18,
                        6: 20,
                        7: 21,
                        8: 22,
                        9: 23,
                        10: 24
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

    anime = ANIME["dating_sim"]
    details = anime["details"]

    # 1️⃣ POST ANIME DETAILS
    details_text = (
        f"🎬 {anime['title']} | {anime['japanese_title']}\n\n"

        f"‣ Genres : {details['genres']}\n"
        f"‣ Type : {details['type']}\n"
        f"‣ Average Rating : {details['rating']}\n"
        f"‣ Status : {details['status']}\n"
        f"‣ First aired : {details['first_aired']}\n"
        f"‣ Last aired : {details['last_aired']}\n"
        f"‣ Runtime : {details['runtime']}\n"
        f"‣ No of episodes : 24\n\n"

        f"{anime['description']}"
    )

    await context.bot.send_message(
        chat_id=CHANNEL,
        text=details_text
    )

    # 2️⃣ POST EACH SEASON WITH QUALITY BUTTONS
    for season_id, season in anime["seasons"].items():

        available_episodes = sum(
            len(episodes)
            for episodes in season["episodes"].values()
        )

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
                f"🎬 {season['name']}\n\n"
                f"📺 Episodes available: {available_episodes}\n\n"
                "📥 Choose your quality:"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    await update.message.reply_text(
        "✅ Dating Sim details, Season 1 and Season 2 posted successfully."
    )


async def post_tomodachi(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Space before Tomodachi Game
    await context.bot.send_message(
        chat_id=CHANNEL,
        text="\n\n\n"
    )

    # Tomodachi Game details only
    await context.bot.send_message(
        chat_id=CHANNEL,
        text=(
            "🎬 Tomodachi Game | Tomodachi Gēmu\n\n"

            "‣ Genres : Psychological, Mystery, Drama, Thriller, Game\n"
            "‣ Type : TV\n"
            "‣ Average Rating : 75\n"
            "‣ Status : FINISHED\n"
            "‣ First aired : 2022-4-6\n"
            "‣ Last aired : 2022-6-22\n"
            "‣ Runtime : 23 minutes\n"
            "‣ No of episodes : 12\n\n"

            "Yuuichi Katagiri values friendship above everything, "
            "but when he and his four closest friends are dragged "
            "into a mysterious debt-repayment game, their friendship "
            "is put to the ultimate test. Forced to participate in "
            "psychological games involving money, trust, and betrayal, "
            "they must work together while uncovering the hidden "
            "secrets each of them carries."
        )
    )

    await update.message.reply_text(
        "✅ Tomodachi Game details posted."
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

        # Delete the Join / Try Again message
        try:
            await query.message.delete()
        except Exception:
            pass

        anime = ANIME[anime_id]
        season = anime["seasons"][season_id]
        episodes = season["episodes"].get(quality, {})

        if not episodes:

            await context.bot.send_message(
                chat_id=query.from_user.id,
                text=f"❌ {quality} is not available yet."
            )

            return

        # Sending files
        sending_message = await context.bot.send_message(
            chat_id=query.from_user.id,
            text="📤 Sending files..."
        )

        try:
            await sending_message.delete()
        except Exception:
            pass

        # Loading message
        loading_message = await context.bot.send_message(
            chat_id=query.from_user.id,
            text="......."
        )

        try:
            await loading_message.delete()
        except Exception:
            pass

        # Send all episodes
        for ep in sorted(episodes.keys()):

            message_id = episodes[ep]

            await context.bot.copy_message(
                chat_id=query.from_user.id,
                from_chat_id=STORAGE_CHAT_ID,
                message_id=message_id
            )

            await asyncio.sleep(1)

        # End of season
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text=f"🎬 END OF {season['name'].upper()} 🏁"
        )

        # Channel buttons
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
            text="📺 Follow our channels for more anime:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception:

        await query.message.reply_text(
            "⚠️ Please make sure you joined @ZynAnime, then tap Try Again."
        )


app.add_handler(
    CommandHandler("start", start)
)

app.add_handler(
    CommandHandler("post", post)
)

app.add_handler(
    CommandHandler("post_tomodachi", post_tomodachi)
)

app.add_handler(
    CallbackQueryHandler(
        check_membership,
        pattern=r"^check\|"
    )
)


app.run_polling()
