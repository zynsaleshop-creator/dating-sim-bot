import os
import asyncio
import json
import time
import asyncpg

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# =========================
# SETTINGS
# =========================

TOKEN = os.environ["BOT_TOKEN"]
LOCAL_API = os.environ["LOCAL_BOT_API"].rstrip("/")
DATABASE_URL = os.environ["DATABASE_URL"]

STORAGE_CHAT_ID = -1003947631814

CHANNEL = "@ZynAnimeHub"
REQUIRED_CHANNEL = "@ZynAnime"
REQUIRED_HENTAI_CHANNEL = "@ZynHentaiVault"

DELETE_AFTER = 15 * 60

WEBHOOK_URL = (
    "https://dating-sim-bot-production.up.railway.app/"
    "telegram-webhook"
)

# =========================
# ANIME DATA
# =========================

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
        "genres": "Drama, Mystery, Psychological",
        "type": "TV",
        "rating": "7.7/10",
        "status": "FINISHED",
        "first_aired": "2022-04-06",
        "last_aired": "2022-06-22",
        "runtime": "22 minutes",
        "episodes_count": 12,
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

# =========================
# DATABASE / DELETION TIMERS
# =========================

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
                item["end_id"],
                item["follow_id"],
                item["anime_id"],
                item["season_id"],
                item["quality"],
                item["delete_at"],
            )
        )


async def delete_messages(context, chat_id, message_ids):
    for message_id in message_ids:
        try:
            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=message_id,
            )
        except Exception as error:
            print(f"Message deletion failed: {error}")


async def deletion_timer(
    context,
    pending_id,
    user_id,
    message_ids,
    warning_id,
    end_id,
    follow_id,
    anime_id,
    season_id,
    quality,
    delete_at,
):
    await asyncio.sleep(max(0, delete_at - time.time()))

    await delete_messages(context, user_id, message_ids)

    for message_id in (warning_id, follow_id):
        if not message_id:
            continue

        try:
            await context.bot.delete_message(
                chat_id=user_id,
                message_id=message_id,
            )
        except Exception:
            pass

    pool = context.bot_data["db_pool"]

    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM pending_deletions WHERE id = $1",
            pending_id,
        )

    keyboard = [[
        InlineKeyboardButton(
            "♻️ Try Again ♻️",
            callback_data=f"file_retry|{anime_id}|{season_id}|{quality}",
        )
    ]]

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="Files deleted successfully ✅\nYou can request them again.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    except Exception as error:
        print(f"Could not send expiry message: {error}")


# =========================
# MEMBERSHIP CHECK
# =========================

async def is_member(context, user_id):
    required_channels = [
        REQUIRED_CHANNEL,
        REQUIRED_HENTAI_CHANNEL,
    ]

    valid_statuses = {"member", "administrator", "creator"}

    for channel in required_channels:
        try:
            member = await context.bot.get_chat_member(
                chat_id=channel,
                user_id=user_id,
            )

            if member.status not in valid_statuses:
                return False

        except Exception as error:
            print(f"Membership check failed for {channel}: {error}")
            return False

    return True


# =========================
# REQUEST FILES
# =========================

async def request_files(
    context,
    user_id,
    anime_id,
    season_id,
    quality,
):
    anime = ANIME.get(anime_id)

    if not anime:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Anime not found.",
        )
        return

    season = anime["seasons"].get(season_id)

    if not season:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Season not found.",
        )
        return

    episodes = season["episodes"].get(quality, {})

    if not episodes:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"❌ {quality} is not available yet.\n\n"
                "Please try another quality."
            ),
        )
        return

    if not await is_member(context, user_id):
        keyboard = [
            [
                InlineKeyboardButton(
                    "📢 Join Anime Channel",
                    url="https://t.me/ZynAnime",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔞 Join Hentai Channel",
                    url="https://t.me/ZynHentaiVault",
                )
            ],
            [
                InlineKeyboardButton(
                    "♻️ Try Again",
                    callback_data=(
                        f"membership_retry|{anime_id}|"
                        f"{season_id}|{quality}"
                    ),
                )
            ],
        ]

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🔒 You must join both required channels "
                "before requesting anime files:\n\n"
                "• @ZynAnime\n"
                "• @ZynHentaiVault"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    sent_messages = []

    for episode_number, storage_message_id in sorted(episodes.items()):
        try:
            copied = await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=STORAGE_CHAT_ID,
                message_id=storage_message_id,
            )
            sent_messages.append(copied.message_id)

        except Exception as error:
            print(
                f"Failed to send {anime_id} episode "
                f"{episode_number}: {error}"
            )

    if not sent_messages:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Unable to send the files right now.",
        )
        return

    warning = await context.bot.send_message(
        chat_id=user_id,
        text=(
            "⚠️ FILE EXPIRY NOTICE\n\n"
            "These files will be deleted automatically in 15 minutes. "
            "Save them before the timer expires."
        ),
    )

    follow = await context.bot.send_message(
        chat_id=user_id,
        text=(
            "🎌 STAY CONNECTED WITH ZYN ANIME\n\n"
            "Get new episodes, updates, and more anime from our channels!"
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "📢 Main Channel",
                    url="https://t.me/ZynAnimeHub",
                ),
                InlineKeyboardButton(
                    "🔄 Anime Updates",
                    url="https://t.me/ZynAnime",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔞 Hentai Channel",
                    url="https://t.me/ZynHentaiVault",
                ),
            ],
        ]),
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
            follow.message_id,
            anime_id,
            season_id,
            quality,
            delete_at,
        )

    context.application.create_task(
        deletion_timer(
            context,
            pending_id,
            user_id,
            sent_messages,
            warning.message_id,
            0,
            follow.message_id,
            anime_id,
            season_id,
            quality,
            delete_at,
        )
    )


# =========================
# START / DEEP LINKS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        payload = context.args[0].lower()
        print(f"Start payload received: {payload}")

        try:
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

        except Exception as error:
            print(f"Deep-link error: {error}")

    keyboard = [[
        InlineKeyboardButton(
            "📚 Browse Anime",
            url="https://t.me/ZynAnimeHub",
        )
    ]]

    await update.message.reply_text(
        "🎬 Welcome to Zyn Anime Bot!\n\n"
        "📚 Find your anime in our main channel:\n"
        "👉 Zyn Anime Hub\n\n"
        "Select an anime there and choose your preferred quality.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# CALLBACK HANDLERS
# =========================

async def membership_retry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    try:
        parts = query.data.split("|")
        anime_id, season_id, quality = parts[1:4]
    except Exception:
        await query.answer()
        return

    user_id = query.from_user.id

    if not await is_member(context, user_id):
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
        user_id,
        anime_id,
        season_id,
        quality,
    )


async def file_retry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    try:
        parts = query.data.split("|")
        anime_id, season_id, quality = parts[1:4]
    except Exception:
        await query.answer()
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


# =========================
# BOT USERNAME / BUTTONS
# =========================

async def get_bot_username(context):
    bot_info = await context.bot.get_me()
    return bot_info.username


def quality_button(bot_username, anime_id, season_id, quality):
    prefixes = {
        "dating_sim": "dating-sim",
        "tomodachi_game": "tomodachi-game",
        "goblin": "goblin",
        "shangri_la": "shangri-la",
    }

    prefix = prefixes.get(anime_id)

    if not prefix:
        raise ValueError(f"Unknown anime ID: {anime_id}")

    payload = f"{prefix}-{season_id}-{quality}"

    return InlineKeyboardButton(
        quality,
        url=f"https://t.me/{bot_username}?start={payload}",
    )


# =========================
# POST DATING SIM
# =========================

async def post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anime = ANIME["dating_sim"]
    bot_username = await get_bot_username(context)

    await context.bot.send_message(
        chat_id=CHANNEL,
        text=(
            f"🎬 {anime['title']}\n\n"
            "Season 1 — 12 Episodes\n"
            "Season 2 — 12 Episodes"
        ),
    )

    for season_id in ("1", "2"):
        buttons = [[
            quality_button(
                bot_username,
                "dating_sim",
                season_id,
                quality,
            )
            for quality in ("480p", "720p", "1080p")
        ]]

        await context.bot.send_message(
            chat_id=CHANNEL,
            text=f"Season {season_id}",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    await update.message.reply_text("✅ Dating Sim posted.")


# =========================
# POST TOMODACHI GAME
# =========================

async def post_tomodachi(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    bot_username = await get_bot_username(context)

    await context.bot.send_message(
        chat_id=CHANNEL,
        text=(
            "🎬 Tomodachi Game\n\n"
            "‣ Genres: Drama, Mystery, Psychological\n"
            "‣ Type: TV\n"
            "‣ Average Rating: 7.7/10\n"
            "‣ Status: FINISHED\n"
            "‣ First aired: 2022-04-06\n"
            "‣ Last aired: 2022-06-22\n"
            "‣ Runtime: 22 minutes\n"
            "‣ No. of episodes: 12\n\n"
            "High school student Yuuichi Katagiri values friendship "
            "above all else. After money for a school trip is stolen, "
            "Yuuichi and his four friends are drawn into a mysterious "
            "debt repayment game. To escape, they must take part in "
            "psychological games that test their trust and friendship."
        ),
    )

    buttons = [[
        quality_button(
            bot_username,
            "tomodachi_game",
            "1",
            quality,
        )
        for quality in ("480p", "720p", "1080p")
    ]]

    await context.bot.send_message(
        chat_id=CHANNEL,
        text="Season 1 — 12 Episodes",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

    await update.message.reply_text("✅ Tomodachi Game posted.")


# =========================
# POST GOBLIN ANIME
# =========================

async def post_goblin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    anime = ANIME["goblin"]
    bot_username = await get_bot_username(context)

    await context.bot.send_message(
        chat_id=CHANNEL,
        text=(
            f"🎬 {anime['title']}\n\n"
            "Season 1 — Episodes 1–5 available\n\n"
            "📺 Choose your preferred video quality below."
        ),
    )

    buttons = [[
        quality_button(
            bot_username,
            "goblin",
            "1",
            quality,
        )
        for quality in ("480p", "720p", "1080p")
    ]]

    await context.bot.send_message(
        chat_id=CHANNEL,
        text="Season 1 — Episodes 1–5",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

    await update.message.reply_text("✅ Goblin anime posted.")


# =========================
# POST SHANGRI-LA FRONTIER
# =========================

async def post_shangri(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    anime = ANIME["shangri_la"]
    bot_username = await get_bot_username(context)

    await context.bot.send_message(
        chat_id=CHANNEL,
        text=(
            "🎬 Shangri-La Frontier\n\n"
            "‣ Type: TV\n"
            "‣ Season: 1\n"
            "‣ Episodes available: 1–25\n"
            "‣ Quality available: 480p\n\n"
            "Rakuro Hizutome, known as Sunraku, is an expert at "
            "conquering badly designed games. He takes on the "
            "popular virtual reality game Shangri-La Frontier, "
            "where his gaming skills lead him into powerful battles "
            "and extraordinary challenges."
        ),
    )

    buttons = [[
        quality_button(
            bot_username,
            "shangri_la",
            "1",
            quality,
        )
        for quality in ("480p", "720p", "1080p")
    ]]

    await context.bot.send_message(
        chat_id=CHANNEL,
        text="Season 1 — Episodes 1–25",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

    await update.message.reply_text(
        "✅ Shangri-La Frontier posted."
    )


# =========================
# POST INIT / DATABASE
# =========================

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


# =========================
# APPLICATION
# =========================

application = (
    Application.builder()
    .token(TOKEN)
    .base_url(f"{LOCAL_API}/bot")
    .post_init(post_init)
    .build()
)

# =========================
# COMMANDS
# =========================

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("post", post))
application.add_handler(
    CommandHandler("post_tomodachi", post_tomodachi)
)
application.add_handler(
    CommandHandler("post_goblin", post_goblin)
)
application.add_handler(
    CommandHandler("post_shangri", post_shangri)
)

# =========================
# CALLBACK HANDLERS
# =========================

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

# =========================
# RUN — WEBHOOK
# =========================

print("🤖 Zyn Anime Bot starting...")

application.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get("PORT", "8080")),
    url_path="telegram-webhook",
    webhook_url=WEBHOOK_URL,
)
