import os
import asyncio
import json
import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]
LOCAL_API = os.environ["LOCAL_BOT_API"]

STORAGE_CHAT_ID = -1003947631814
CHANNEL = "@ZynAnimeHub"
REQUIRED_CHANNEL = "@ZynAnime"
BOT_USERNAME = "ZynAnimeBot"

DELETE_AFTER = 15 * 60
PENDING_FILE = "pending_deletions.json"


ANIME = {
    "dating_sim": {
        "title": "Trapped in a Dating Sim: The World of Otome Games Is Tough for Mobs",
        "japanese_title": "Otomege Sekai wa Mob ni Kibishii Sekai desu",
        "description":
            "Office worker Leon is reincarnated into a particularly punishing dating sim "
            "where women reign supreme and only beautiful men have a seat at the table. "
            "But Leon has a secret weapon: he remembers his past life, including a complete "
            "playthrough of the game in which he is now trapped. Watch Leon spark a revolution "
            "to change this new world in order to fulfill his ultimate desire... of living a "
            "quiet, easy life in the countryside!",
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
    },

    "tomodachi_game": {
        "title": "Tomodachi Game",
        "seasons": {
            "s1": {
                "name": "Season 1",
                "episodes": {
                    "480p": {
                        1: 25, 2: 26, 3: 27, 4: 28, 5: 29,
                        6: 31, 7: 32, 8: 33, 9: 34, 10: 35,
                        11: 36, 12: 37
                    },
                    "720p": {},
                    "1080p": {}
                }
            }
        }
    }
}


def load_pending():
    if not os.path.exists(PENDING_FILE):
        return []
    try:
        with open(PENDING_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def save_pending(data):
    temp = PENDING_FILE + ".tmp"
    with open(temp, "w") as f:
        json.dump(data, f)
    os.replace(temp, PENDING_FILE)


PENDING_DELETIONS = load_pending()


async def delete_messages(chat_id, message_ids):
    for message_id in message_ids:
        try:
            await app.bot.delete_message(
                chat_id=chat_id,
                message_id=message_id
            )
        except Exception:
            pass


async def deletion_timer(item):
    wait = item["delete_at"] - time.time()

    if wait > 0:
        await asyncio.sleep(wait)

    await delete_messages(
        item["chat_id"],
        item["message_ids"]
    )

    await delete_messages(
        item["chat_id"],
        item.get("extra_message_ids", [])
    )

    global PENDING_DELETIONS

    PENDING_DELETIONS = [
        x for x in PENDING_DELETIONS
        if x["id"] != item["id"]
    ]

    save_pending(PENDING_DELETIONS)

    await app.bot.send_message(
        chat_id=item["chat_id"],
        text="Files deleted successfully ✅\nCan request files again"
    )


async def restore_timers(application):
    for item in list(PENDING_DELETIONS):
        asyncio.create_task(deletion_timer(item))


app = (
    Application.builder()
    .token(TOKEN)
    .base_url(LOCAL_API + "/bot")
    .base_file_url(LOCAL_API + "/file/bot")
    .local_mode(True)
    .post_init(restore_timers)
    .build()
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        parts = context.args[0].split("-")

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

    await update.message.reply_text(
        "🎬 Welcome to Zyn Anime Bot!\n\n"
        "📚 Find your anime in our main channel:\n"
        "👉 Zyn Anime Hub\n\n"
        "Select an anime there and choose your preferred quality.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "📺 Browse Anime",
                url="https://t.me/ZynAnimeHub"
            )
        ]])
    )


async def post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anime = ANIME["dating_sim"]
    details = anime["details"]

    text = (
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
        text=text
    )

    for season_id, season in anime["seasons"].items():
        available = sum(
            len(x) for x in season["episodes"].values()
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
                f"📺 Episodes available: {available}\n\n"
                "📥 Choose your quality:"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    await update.message.reply_text(
        "✅ Dating Sim details, Season 1 and Season 2 posted successfully."
    )


async def post_tomodachi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anime = ANIME["tomodachi_game"]

    await context.bot.send_message(
        chat_id=CHANNEL,
        text="━━━━━━━━━━━━━━━━━━━━"
    )

    await context.bot.send_message(
        chat_id=CHANNEL,
        text="━━━━━━━━━━━━━━━━━━━━"
    )

    await context.bot.send_message(
        chat_id=CHANNEL,
        text=f"🎬 {anime['title']}"
    )

    for season_id, season in anime["seasons"].items():
        available = sum(
            len(x) for x in season["episodes"].values()
        )

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
                f"🎬 {season['name']}\n\n"
                f"📺 Episodes available: {available}\n\n"
                "📥 Choose your quality:"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    await update.message.reply_text(
        "✅ Tomodachi Game posted."
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

        msg = await context.bot.send_message(
            chat_id=query.from_user.id,
            text="📤 Sending files..."
        )

        try:
            await msg.delete()
        except Exception:
            pass

        msg = await context.bot.send_message(
            chat_id=query.from_user.id,
            text="......."
        )

        try:
            await msg.delete()
        except Exception:
            pass

        sent_ids = []

        for ep in sorted(episodes):
            sent = await context.bot.copy_message(
                chat_id=query.from_user.id,
                from_chat_id=STORAGE_CHAT_ID,
                message_id=episodes[ep]
            )

            sent_ids.append(sent.message_id)
            await asyncio.sleep(1)

        warning = await context.bot.send_message(
            chat_id=query.from_user.id,
            text=(
                "⚠️ Files will be deleted in 15 minutes.\n\n"
                "Please save/download them now or send them to another chat "
                "if you want to keep them."
            )
        )

        end = await context.bot.send_message(
            chat_id=query.from_user.id,
            text=f"🎬 END OF {season['name'].upper()} 🏁"
        )

        keyboard = [[
            InlineKeyboardButton(
                "ZynAnimeHub",
                url="https://t.me/ZynAnimeHub"
            ),
            InlineKeyboardButton(
                "ZynAnime",
                url="https://t.me/zynanime"
            )
        ]]

        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="📺 Follow our channels for more anime:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        global PENDING_DELETIONS

        item = {
            "id": f"{query.from_user.id}-{int(time.time() * 1000)}",
            "chat_id": query.from_user.id,
            "message_ids": sent_ids,
            "extra_message_ids": [
                warning.message_id,
                end.message_id
            ],
            "delete_at": time.time() + DELETE_AFTER
        }

        PENDING_DELETIONS.append(item)
        save_pending(PENDING_DELETIONS)

        asyncio.create_task(
            deletion_timer(item)
        )

    except Exception as error:
        print("⚠️ Error:", error)

        try:
            await query.message.reply_text(
                "⚠️ Please make sure you joined @ZynAnime, "
                "then tap Try Again."
            )
        except Exception:
            pass


app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("post", post))
app.add_handler(CommandHandler("post_tomodachi", post_tomodachi))

app.add_handler(
    CallbackQueryHandler(
        check_membership,
        pattern=r"^check\|"
    )
)

app.run_polling()
