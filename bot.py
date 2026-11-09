import os
import asyncio
import json
import time
import logging
import asyncpg

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# =====================================
# SETTINGS
# =====================================

TOKEN = os.environ["BOT_TOKEN"]
LOCAL_API = os.environ["LOCAL_BOT_API"].rstrip("/")
DATABASE_URL = os.environ["DATABASE_URL"]

STORAGE_CHAT_ID = -1003947631814

CHANNEL = "@ZynAnimeHub"
REQUIRED_CHANNELS = ["@ZynAnime", "@ZynHentaiVault"]

DELETE_AFTER = 15 * 60

WEBHOOK_URL = (
    "https://dating-sim-bot-production.up.railway.app/"
    "telegram-webhook"
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =====================================
# ANIME DATABASE
# =====================================

ANIME = {
    "dating_sim": {
        "title": (
            "Trapped in a Dating Sim: The World of Otome Games "
            "Is Tough for Mobs"
        ),
        "seasons": {
            "1": {
                "episodes": {
                    "480p": {
                        1: 3, 2: 4, 3: 5, 4: 6,
                        5: 7, 6: 8, 7: 9, 8: 10,
                        9: 11, 10: 12, 11: 13, 12: 19,
                    },
                    "720p": {
                        1: 53, 2: 54, 3: 55, 4: 56,
                        5: 57, 6: 58, 7: 59, 8: 60,
                        9: 110, 10: 111, 11: 112, 12: 113,
                    },
                    "1080p": {},
                },
            },
            "2": {
                "episodes": {
                    "480p": {
                        1: 14, 2: 15, 3: 16, 4: 17,
                        5: 18, 6: 20, 7: 21, 8: 22,
                        9: 23, 10: 24, 11: 44, 12: 51,
                    },
                    "720p": {},
                    "1080p": {},
                },
            },
        },
    },

    "tomodachi_game": {
        "title": "Tomodachi Game",
        "seasons": {
            "1": {
                "episodes": {
                    "480p": {
                        1: 25, 2: 26, 3: 27, 4: 28,
                        5: 29, 6: 31, 7: 32, 8: 33,
                        9: 34, 10: 35, 11: 36, 12: 37,
                    },
                    "720p": {
                        1: 38, 2: 39, 3: 40, 4: 41,
                        5: 42, 6: 43, 7: 45, 8: 105,
                        9: 106, 10: 107, 11: 108, 12: 109,
                    },
                    "1080p": {},
                },
            },
        },
    },

    "goblin": {
        "title": "So What's Wrong with Getting Reborn as a Goblin?",
        "seasons": {
            "1": {
                "episodes": {
                    "480p": {
                        1: 91, 2: 92, 3: 93, 4: 94, 5: 115,
                    },
                    "720p": {
                        1: 95, 2: 96, 3: 97, 4: 98, 5: 116,
                    },
                    "1080p": {
                        1: 100, 2: 101, 3: 103, 4: 104, 5: 117,
                    },
                },
            },
        },
    },

    "shangri_la": {
        "title": "Shangri-La Frontier",
        "seasons": {
            "1": {
                "episodes": {
                    "480p": {
                        1: 62, 2: 63, 3: 64, 4: 65, 5: 66,
                        6: 67, 7: 68, 8: 69, 9: 70, 10: 71,
                        11: 72, 12: 73, 13: 74, 14: 75, 15: 76,
                        16: 77, 17: 118, 18: 78, 19: 79, 20: 80,
                        21: 81, 22: 82, 23: 83, 24: 84, 25: 85,
                    },
                    "720p": {},
                    "1080p": {},
                },
            },
        },
    },
}


# =====================================
# DATABASE AND EXPIRY
# =====================================

async def delete_messages(bot, chat_id, message_ids):
    for message_id in message_ids:
        try:
            await bot.delete_message(chat_id, int(message_id))
        except Exception as error:
            logger.warning("Message deletion failed: %s", error)


async def deletion_timer(
    application, pending_id, user_id, message_ids,
    warning_id, follow_id, anime_id, season_id,
    quality, delete_at,
):
    await asyncio.sleep(max(0, delete_at - time.time()))

    bot = application.bot

    await delete_messages(bot, user_id, message_ids)

    for message_id in (warning_id, follow_id):
        if message_id:
            await delete_messages(bot, user_id, [message_id])

    pool = application.bot_data["db_pool"]

    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM pending_deletions WHERE id = $1",
            pending_id,
        )

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "♻️ Try Again ♻️",
            callback_data=(
                f"file_retry|{anime_id}|{season_id}|{quality}"
            ),
        )
    ]])

    try:
        await bot.send_message(
            chat_id=user_id,
            text=(
                "<b>❌ FILES DELETED</b>\n\n"
                "Your requested files have expired.\n"
                "You can request them again below."
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
    except Exception:
        logger.exception("Could not send expiry message.")


async def restore_timers(application):
    pool = application.bot_data["db_pool"]

    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM pending_deletions")

    for row in rows:
        item = dict(row)

        application.create_task(
            deletion_timer(
                application,
                item["id"],
                item["user_id"],
                json.loads(item["message_ids"]),
                item["warning_id"],
                item["follow_id"],
                item["anime_id"],
                item["season_id"],
                item["quality"],
                item["delete_at"],
            )
        )


async def post_init(application):
    pool = await asyncpg.create_pool(
        DATABASE_URL,
        ssl="require",
    )

    application.bot_data["db_pool"] = pool

    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pending_deletions (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                message_ids TEXT NOT NULL,
                warning_id BIGINT NOT NULL,
                end_id BIGINT NOT NULL,
                follow_id BIGINT NOT NULL,
                anime_id TEXT NOT NULL,
                season_id TEXT NOT NULL,
                quality TEXT NOT NULL,
                delete_at DOUBLE PRECISION NOT NULL
            )
            """
        )

    await restore_timers(application)


async def post_shutdown(application):
    pool = application.bot_data.get("db_pool")
    if pool:
        await pool.close()


# =====================================
# MEMBERSHIP CHECK
# =====================================

async def is_member(context, user_id):
    valid = {"member", "administrator", "creator"}

    async def check(channel):
        try:
            member = await context.bot.get_chat_member(
                chat_id=channel,
                user_id=user_id,
            )
            return member.status in valid
        except Exception as error:
            logger.warning(
                "Membership check failed for %s: %s",
                channel,
                error,
            )
            return False

    results = await asyncio.gather(
        *(check(channel) for channel in REQUIRED_CHANNELS)
    )

    return all(results)


def membership_keyboard(anime_id, season_id, quality):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "📢 Join Anime Channel",
            url="https://t.me/ZynAnime",
        )],
        [InlineKeyboardButton(
            "🔞 Join Hentai Channel",
            url="https://t.me/ZynHentaiVault",
        )],
        [InlineKeyboardButton(
            "♻️ Try Again",
            callback_data=(
                f"membership_retry|{anime_id}|{season_id}|{quality}"
            ),
        )],
    ])


# =====================================
# SEND FILES
# =====================================

async def request_files(
    context, user_id, anime_id, season_id, quality
):
    anime = ANIME.get(anime_id)

    if not anime:
        await context.bot.send_message(user_id, "❌ Anime not found.")
        return

    season = anime["seasons"].get(season_id)

    if not season:
        await context.bot.send_message(user_id, "❌ Season not found.")
        return

    episodes = season["episodes"].get(quality, {})

    if not episodes:
        await context.bot.send_message(
            user_id,
            f"❌ {quality} is not available yet.\n\n"
            "Please try another quality.",
        )
        return

    if not await is_member(context, user_id):
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🔒 You must join both required channels "
                "before requesting anime files:\n\n"
                "• @ZynAnime\n"
                "• @ZynHentaiVault"
            ),
            reply_markup=membership_keyboard(
                anime_id, season_id, quality
            ),
        )
        return

    sent_messages = []

    for episode_number, storage_id in sorted(episodes.items()):
        try:
            copied = await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=STORAGE_CHAT_ID,
                message_id=storage_id,
            )
            sent_messages.append(copied.message_id)

        except Exception:
            logger.exception(
                "Failed to send %s episode %s",
                anime_id,
                episode_number,
            )

    if not sent_messages:
        await context.bot.send_message(
            user_id,
            "❌ Unable to send the files right now.",
        )
        return

    warning = await context.bot.send_message(
        chat_id=user_id,
        text=(
            "<blockquote>"
            "<b>⚠️ FILE EXPIRY NOTICE</b>\n\n"
            "These files will be deleted automatically in "
            "<b>15 minutes</b>.\n\n"
            "Save them before the timer expires."
            "</blockquote>"
        ),
        parse_mode=ParseMode.HTML,
    )

    delete_at = time.time() + DELETE_AFTER
    pool = context.application.bot_data["db_pool"]

    async with pool.acquire() as conn:
        pending_id = await conn.fetchval(
            """
            INSERT INTO pending_deletions
            (
                user_id, message_ids, warning_id, end_id,
                follow_id, anime_id, season_id, quality, delete_at
            )
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
            RETURNING id
            """,
            user_id,
            json.dumps(sent_messages),
            warning.message_id,
            0,
            0,
            anime_id,
            season_id,
            quality,
            delete_at,
        )

    context.application.create_task(
        deletion_timer(
            context.application,
            pending_id,
            user_id,
            sent_messages,
            warning.message_id,
            0,
            anime_id,
            season_id,
            quality,
            delete_at,
        )
    )


# =====================================
# START AND DEEP LINKS
# =====================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Special Zyn AfterDark link
    if context.args and context.args[0].lower() == "afterdark":
        await update.message.reply_text(
            "🌙 <b>Welcome!</b>\n\n"
            "You're just one step away from Zyn AfterDark.\n\n"
            "Tap the button below to continue and access the private channel. 👇",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "🌙 Click Here to Continue",
                    url="https://t.me/ZynAfterDarkBot",
                )
            ]]),
        )
        return

    # Existing anime deep links
    if context.args:
        payload = context.args[0].lower()

        prefixes = {
            "dating-sim-": "dating_sim",
            "tomodachi-game-": "tomodachi_game",
            "goblin-": "goblin",
            "shangri-la-": "shangri_la",
        }

        for prefix, anime_id in prefixes.items():
            if payload.startswith(prefix):
                values = payload[len(prefix):].split("-")

                if len(values) == 2:
                    season_id, quality = values

                    if (
                        season_id in ANIME[anime_id]["seasons"]
                        and quality in ("480p", "720p", "1080p")
                    ):
                        await request_files(
                            context,
                            update.effective_user.id,
                            anime_id,
                            season_id,
                            quality,
                        )
                        return

    # Normal /start remains unchanged
    await update.message.reply_text(
        "🎬 Welcome to Zyn Anime Bot!\n\n"
        "📚 Find your anime in our main channel:\n"
        "👉 Zyn Anime Hub\n\n"
        "Select an anime there and choose your preferred quality.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "📚 Browse Anime",
                url="https://t.me/ZynAnimeHub",
            )
        ]]),
    )


# =====================================
# RETRY BUTTONS
# =====================================

async def membership_retry(update, context):
    query = update.callback_query
    parts = query.data.split("|")

    if len(parts) != 4:
        await query.answer()
        return

    _, anime_id, season_id, quality = parts

    if not await is_member(context, query.from_user.id):
        await query.answer(
            "❌ Please join both channels first.",
            show_alert=True,
        )
        return

    await query.answer()

    try:
        await query.message.delete()
    except Exception:
        pass

    await request_files(
        context,
        query.from_user.id,
        anime_id,
        season_id,
        quality,
    )


async def file_retry(update, context):
    query = update.callback_query
    parts = query.data.split("|")

    if len(parts) != 4:
        await query.answer()
        return

    _, anime_id, season_id, quality = parts

    await query.answer()

    try:
        await query.message.delete()
    except Exception:
        pass

    await request_files(
        context,
        query.from_user.id,
        anime_id,
        season_id,
        quality,
    )


# =====================================
# QUALITY BUTTONS
# =====================================

PREFIXES = {
    "dating_sim": "dating-sim",
    "tomodachi_game": "tomodachi-game",
    "goblin": "goblin",
    "shangri_la": "shangri-la",
}


async def get_bot_username(context):
    return (await context.bot.get_me()).username


def quality_button(username, anime_id, season_id, quality):
    payload = f"{PREFIXES[anime_id]}-{season_id}-{quality}"

    return InlineKeyboardButton(
        quality,
        url=f"https://t.me/{username}?start={payload}",
    )


# =====================================
# CHANNEL POSTING
# =====================================

async def post_quality_buttons(
    context, username, anime_id, season_id
):
    buttons = [[
        quality_button(username, anime_id, season_id, quality)
        for quality in ("480p", "720p", "1080p")
    ]]

    await context.bot.send_message(
        chat_id=CHANNEL,
        text=f"Season {season_id}",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def post_anime(update, context, anime_id):
    username = await get_bot_username(context)
    anime = ANIME[anime_id]

    await context.bot.send_message(
        chat_id=CHANNEL,
        text=f"🎬 {anime['title']}",
    )

    for season_id in anime["seasons"]:
        await post_quality_buttons(
            context,
            username,
            anime_id,
            season_id,
        )

    await update.message.reply_text(
        f"✅ {anime['title']} posted."
    )


async def post(update, context):
    await post_anime(update, context, "dating_sim")


async def post_tomodachi(update, context):
    await post_anime(update, context, "tomodachi_game")


async def post_goblin(update, context):
    await post_anime(update, context, "goblin")


async def post_shangri(update, context):
    await post_anime(update, context, "shangri_la")


# =====================================
# APPLICATION
# =====================================

application = (
    Application.builder()
    .token(TOKEN)
    .base_url(f"{LOCAL_API}/bot")
    .base_file_url(f"{LOCAL_API}/file/bot")
    .local_mode(True)
    .post_init(post_init)
    .post_shutdown(post_shutdown)
    .build()
)

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("post", post))
application.add_handler(CommandHandler("post_tomodachi", post_tomodachi))
application.add_handler(CommandHandler("post_goblin", post_goblin))
application.add_handler(CommandHandler("post_shangri", post_shangri))

application.add_handler(
    CallbackQueryHandler(
        membership_retry,
        pattern=r"^membership_retry\|",
    )
)

application.add_handler(
    CallbackQueryHandler(
        file_retry,
        pattern=r"^file_retry\|",
    )
)

print("🤖 Zyn Anime Bot starting...")

application.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get("PORT", "8080")),
    url_path="telegram-webhook",
    webhook_url=WEBHOOK_URL,
)
