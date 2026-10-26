import os
import asyncio
import json
import time
import asyncpg

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)


# =========================
# SETTINGS
# =========================

TOKEN = os.environ["BOT_TOKEN"]
LOCAL_API = os.environ["LOCAL_BOT_API"].rstrip("/")

STORAGE_CHAT_ID = -1003947631814

CHANNEL = "@ZynAnimeHub"
REQUIRED_CHANNEL = "@ZynAnime"

DELETE_AFTER = 15 * 60
DATABASE_URL = os.environ["DATABASE_URL"]

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
                        9: 11, 10: 12, 11: 13, 12: 19
                    },
                    "720p": {
                        1: 53, 2: 54, 3: 55, 4: 56,
                        5: 57, 6: 58, 7: 59, 8: 60,
                        9: 110, 10: 111, 11: 112, 12: 113
                    },
                    "1080p": {}
                }
            },
            "2": {
                "episodes": {
                    "480p": {
                        1: 14, 2: 15, 3: 16, 4: 17,
                        5: 18, 6: 20, 7: 21, 8: 22,
                        9: 23, 10: 24, 11: 44, 12: 51
                    },
                    "720p": {},
                    "1080p": {}
                }
            }
        }
    },

    "tomodachi_game": {
        "title": "Tomodachi Game",
        "genres": "Drama, Mystery, Psychological",
        "type": "TV",
        "rating": "77",
        "status": "FINISHED",
        "first_aired": "2022-4-6",
        "last_aired": "2022-6-22",
        "runtime": "22 minutes",
        "episodes_count": 12,
        "seasons": {
            "1": {
                "episodes": {
                    "480p": {
                        1: 25, 2: 26, 3: 27, 4: 28,
                        5: 29, 6: 31, 7: 32, 8: 33,
                        9: 34, 10: 35, 11: 36, 12: 37
                    },
                    "720p": {
                        1: 38, 2: 39, 3: 40, 4: 41,
                        5: 42, 6: 43, 7: 45,
                        8: 105, 9: 106, 10: 107,
                        11: 108, 12: 109
                    },
                    "1080p": {}
                }
            }
        }
    },

    "goblin": {
        "title": "So What's Wrong with Getting Reborn as a Goblin?",
        "seasons": {
            "1": {
                "episodes": {
                    "480p": {
                        1: 91, 2: 92, 3: 93, 4: 94
                    },
                    "720p": {
                        1: 95, 2: 96, 3: 97, 4: 98
                    },
                    "1080p": {
                        1: 100, 2: 101, 3: 103, 4: 104
                    }
                }
            }
        }
    }
}


# =========================
# PENDING DELETIONS — POSTGRESQL
# =========================

async def restore_timers(application):
    pool = application.bot_data["db_pool"]

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM pending_deletions"
        )

    for row in rows:
        item = dict(row)

        asyncio.create_task(
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
                item["delete_at"]
            )
        )


# =========================
# DELETE MESSAGES
# =========================

async def delete_messages(context, chat_id, message_ids):
    for message_id in message_ids:
        try:
            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=message_id
            )
        except Exception:
            pass


# =========================
# MEMBERSHIP CHECK
# =========================

async def is_member(context, user_id):
    try:
        member = await context.bot.get_chat_member(
            chat_id=REQUIRED_CHANNEL,
            user_id=user_id
        )
        return member.status in [
            "member",
            "administrator",
            "creator"
        ]
    except Exception as error:
        print(f"Membership check error: {error}")
        return False


# =========================
# DELETION TIMER
# =========================

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
    delete_at
):
    await asyncio.sleep(max(0, delete_at - time.time()))

    await delete_messages(context, user_id, message_ids)

    for message_id in [warning_id, follow_id]:
        try:
            await context.bot.delete_message(
                chat_id=user_id,
                message_id=message_id
            )
        except Exception:
            pass

    pool = context.bot_data["db_pool"]

    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM pending_deletions WHERE id = $1",
            pending_id
        )

    keyboard = [[
        InlineKeyboardButton(
            "♻️ Try Again ♻️",
            callback_data=(
                f"file_retry|{anime_id}|{season_id}|{quality}"
            )
        )
    ]]

    await context.bot.send_message(
        chat_id=user_id,
        text="Files deleted successfully ✅\nYou can request them again.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# REQUEST FILES
# =========================

async def request_files(context, user_id, anime_id, season_id, quality):
    anime = ANIME.get(anime_id)

    if not anime:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Anime not found."
        )
        return

    season = anime["seasons"].get(season_id)

    if not season:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Season not found."
        )
        return

    episodes = season["episodes"].get(quality, {})

    if not episodes:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"❌ {quality} is not available yet.\n\n"
                "Please try another quality."
            )
        )
        return

    member = await is_member(context, user_id)

    if not member:
        keyboard = [
            [
                InlineKeyboardButton(
                    "📢 Join Channel",
                    url="https://t.me/zynanime"
                )
            ],
            [
                InlineKeyboardButton(
                    "♻️ Try Again",
                    callback_data=(
                        f"membership_retry|{anime_id}|"
                        f"{season_id}|{quality}"
                    )
                )
            ]
        ]

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🔒 You must join our channel "
                "before requesting anime files."
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    sending = await context.bot.send_message(
        chat_id=user_id,
        text="📤 Sending files..."
    )

    try:
        await context.bot.delete_message(
            chat_id=user_id,
            message_id=sending.message_id
        )
    except Exception:
        pass

    dots = await context.bot.send_message(
        chat_id=user_id,
        text="......."
    )

    try:
        await context.bot.delete_message(
            chat_id=user_id,
            message_id=dots.message_id
        )
    except Exception:
        pass

    sent_messages = []

    for episode, storage_message_id in sorted(episodes.items()):
        try:
            copied = await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=STORAGE_CHAT_ID,
                message_id=storage_message_id
            )
            sent_messages.append(copied.message_id)
        except Exception as error:
            print(f"Failed to send episode {episode}: {error}")

    if not sent_messages:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Unable to send the files right now."
        )
        return

    warning = await context.bot.send_message(
        chat_id=user_id,
        text=(
            "<blockquote>⚠️ <b>FILE EXPIRY NOTICE</b>\n\n"
            "These files will be deleted automatically in 15 minutes.\n"
            "Save or forward them if you want to keep them.</blockquote>"
        ),
        parse_mode="HTML"
    )

    keyboard = [[
        InlineKeyboardButton(
            "📢 Main Channel",
            url="https://t.me/ZynAnimeHub"
        ),
        InlineKeyboardButton(
            "🔄 Backup Channel",
            url="https://t.me/ZynAnime"
        )
    ]]
    follow = await context.bot.send_message(
        chat_id=user_id,
        text=(
            "🎌 <b>STAY CONNECTED WITH ZYN ANIME</b>\n\n"
            "Get new episodes, updates, and more anime "
            "from our channels!"
        ),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
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
            VALUES ($1,$2,$3,0,$4,$5,$6,$7,$8)
            RETURNING id
            """,
            user_id,
            json.dumps(sent_messages),
            warning.message_id,
            follow.message_id,
            anime_id,
            season_id,
            quality,
            delete_at
        )

    asyncio.create_task(
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
            delete_at
        )
    )


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        payload = context.args[0].lower()
        print(f"🔗 Start payload received: {payload}")

        try:
            if payload.startswith("dating-sim-"):
                values = payload[len("dating-sim-"):].split("-")

                if len(values) == 2:
                    season_id, quality = values

                    if (
                        season_id in ANIME["dating_sim"]["seasons"]
                        and quality in ["480p", "720p", "1080p"]
                    ):
                        await request_files(
                            context,
                            update.effective_user.id,
                            "dating_sim",
                            season_id,
                            quality
                        )
                        return

            if payload.startswith("tomodachi-game-"):
                values = payload[len("tomodachi-game-"):].split("-")

                if len(values) == 2:
                    season_id, quality = values

                    if (
                        season_id in ANIME["tomodachi_game"]["seasons"]
                        and quality in ["480p", "720p", "1080p"]
                    ):
                        await request_files(
                            context,
                            update.effective_user.id,
                            "tomodachi_game",
                            season_id,
                            quality
                        )
                        return

            if payload.startswith("goblin-"):
                values = payload[len("goblin-"):].split("-")

                if len(values) == 2:
                    season_id, quality = values

                    if (
                        season_id in ANIME["goblin"]["seasons"]
                        and quality in ["480p", "720p", "1080p"]
                    ):
                        await request_files(
                            context,
                            update.effective_user.id,
                            "goblin",
                            season_id,
                            quality
                        )
                        return

        except Exception as error:
            print(f"❌ Deep link error: {error}")

    keyboard = [[
        InlineKeyboardButton(
            "📚 Browse Anime",
            url="https://t.me/ZynAnimeHub"
        )
    ]]

    await update.message.reply_text(
        (
            "🎬 Welcome to Zyn Anime Bot!\n\n"
            "📚 Find your anime in our main channel:\n"
            "👉 Zyn Anime Hub\n\n"
            "Select an anime there and choose "
            "your preferred quality."
        ),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# CALLBACK HANDLERS
# =========================

async def quality_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        parts = query.data.split("|")
        anime_id, season_id, quality = parts[1], parts[2], parts[3]
    except Exception:
        return

    await request_files(
        context,
        query.from_user.id,
        anime_id,
        season_id,
        quality
    )


async def membership_retry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    try:
        parts = query.data.split("|")
        anime_id, season_id, quality = parts[1], parts[2], parts[3]
    except Exception:
        await query.answer()
        return

    user_id = query.from_user.id
    member = await is_member(context, user_id)

    if not member:
        await query.answer(
            "❌ Please join the channel first.",
            show_alert=True
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
        quality
    )


async def file_retry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    try:
        parts = query.data.split("|")
        anime_id, season_id, quality = parts[1], parts[2], parts[3]
    except Exception:
        await query.answer()
        return

    await query.answer()
    user_id = query.from_user.id

    try:
        await query.message.delete()
    except Exception:
        pass

    await request_files(
        context,
        user_id,
        anime_id,
        season_id,
        quality
    )


# =========================
# BOT USERNAME
# =========================

async def get_bot_username(context):
    bot_info = await context.bot.get_me()
    return bot_info.username


def quality_button(bot_username, anime_id, season_id, quality):
    if anime_id == "dating_sim":
        payload = f"dating-sim-{season_id}-{quality}"
    elif anime_id == "tomodachi_game":
        payload = f"tomodachi-game-{season_id}-{quality}"
    elif anime_id == "goblin":
        payload = f"goblin-{season_id}-{quality}"
    else:
        raise ValueError("Unknown anime ID")

    return InlineKeyboardButton(
        quality,
        url=f"https://t.me/{bot_username}?start={payload}"
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
        )
    )

    buttons_s1 = [[
        quality_button(bot_username, "dating_sim", "1", "480p"),
        quality_button(bot_username, "dating_sim", "1", "720p"),
        quality_button(bot_username, "dating_sim", "1", "1080p")
    ]]

    await context.bot.send_message(
        chat_id=CHANNEL,
        text="Season 1",
        reply_markup=InlineKeyboardMarkup(buttons_s1)
    )

    buttons_s2 = [[
        quality_button(bot_username, "dating_sim", "2", "480p"),
        quality_button(bot_username, "dating_sim", "2", "720p"),
        quality_button(bot_username, "dating_sim", "2", "1080p")
    ]]

    await context.bot.send_message(
        chat_id=CHANNEL,
        text="Season 2",
        reply_markup=InlineKeyboardMarkup(buttons_s2)
    )

    await update.message.reply_text("✅ Dating Sim posted.")


# =========================
# POST TOMODACHI GAME
# =========================

async def post_tomodachi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_username = await get_bot_username(context)

    text = (
        "🎬 Tomodachi Game\n\n"
        "‣ Genres : Drama, Mystery, Psychological\n"
        "‣ Type : TV\n"
        "‣ Average Rating : 77\n"
        "‣ Status : FINISHED\n"
        "‣ First aired : 2022-4-6\n"
        "‣ Last aired : 2022-6-22\n"
        "‣ Runtime : 22 minutes\n"
        "‣ No of episodes : 12\n\n"
        "High school student Yuuichi Katagiri values friendship "
        "above all else. But after the money for a school trip "
        "is stolen, Yuuichi and his four friends are dragged "
        "into a mysterious debt repayment game. To escape, "
        "they must take part in psychological games that test "
        "their trust, friendship and true nature."
    )

    await context.bot.send_message(chat_id=CHANNEL, text=text)

    buttons = [[
        quality_button(bot_username, "tomodachi_game", "1", "480p"),
        quality_button(bot_username, "tomodachi_game", "1", "720p"),
        quality_button(bot_username, "tomodachi_game", "1", "1080p")
    ]]

    await context.bot.send_message(
        chat_id=CHANNEL,
        text="Season 1 — 12 Episodes",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

    await update.message.reply_text("✅ Tomodachi Game posted.")


# =========================
# POST GOBLIN ANIME
# =========================

async def post_goblin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    anime = ANIME["goblin"]
    bot_username = await get_bot_username(context)

    await context.bot.send_message(
        chat_id=CHANNEL,
        text=(
            f"🎬 {anime['title']}\n\n"
            "Season 1 — Episodes 1–4 available\n\n"
            "📺 Choose your preferred video quality below."
        )
    )

    buttons = [[
        quality_button(bot_username, "goblin", "1", "480p"),
        quality_button(bot_username, "goblin", "1", "720p"),
        quality_button(bot_username, "goblin", "1", "1080p")
    ]]

    await context.bot.send_message(
        chat_id=CHANNEL,
        text="Season 1 — Episodes 1–4",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

    await update.message.reply_text(
        "✅ Goblin anime posted to ZynAnimeHub."
    )


# =========================
# POST INIT
# =========================

async def post_init(application):
    pool = await asyncpg.create_pool(
        DATABASE_URL,
        ssl="require"
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
# HANDLERS
# =========================

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("post", post))
application.add_handler(CommandHandler("post_tomodachi", post_tomodachi))
application.add_handler(CommandHandler("post_goblin", post_goblin))

application.add_handler(
    CallbackQueryHandler(membership_retry, pattern=r"^membership_retry\|")
)

application.add_handler(
    CallbackQueryHandler(file_retry, pattern=r"^file_retry\|")
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
