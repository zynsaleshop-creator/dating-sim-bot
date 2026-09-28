import os
import asyncio
import json
import time

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
LOCAL_API = os.environ["LOCAL_BOT_API"]

STORAGE_CHAT_ID = -1003947631814

CHANNEL = "@ZynAnimeHub"
REQUIRED_CHANNEL = "@ZynAnime"

BOT_USERNAME = "ZynAnimeBot"

DELETE_AFTER = 15 * 60
PENDING_FILE = "pending_deletions.json"


# =========================
# ANIME DATA
# =========================

ANIME = {

    "dating_sim": {

        "title":
            "Trapped in a Dating Sim: The World of Otome Games Is Tough for Mobs",

        "seasons": {

            "1": {
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

            "2": {
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
    },


    "tomodachi_game": {

        "title": "Tomodachi Game",

        "description":
            "High school student Yuuichi Katagiri values friendship "
            "above all else. But after the money for a school trip is "
            "stolen, Yuuichi and his four friends are dragged into a "
            "mysterious debt repayment game. To escape, they must take "
            "part in psychological games that test their trust, "
            "friendship and true nature.",

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
                        1: 25,
                        2: 26,
                        3: 27,
                        4: 28,
                        5: 29,
                        6: 31,
                        7: 32,
                        8: 33,
                        9: 34,
                        10: 35,
                        11: 36,
                        12: 37
                    },

                    "720p": {},

                    "1080p": {}
                }
            }
        }
    }
}


# =========================
# PENDING DELETIONS
# =========================

def load_pending():

    try:

        with open(PENDING_FILE, "r") as f:
            return json.load(f)

    except Exception:

        return []


def save_pending(data):

    with open(PENDING_FILE, "w") as f:
        json.dump(data, f)


# =========================
# DELETE MESSAGES
# =========================

async def delete_messages(
    context,
    chat_id,
    message_ids
):

    for message_id in message_ids:

        try:

            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=message_id
            )

        except Exception:

            pass


# =========================
# DELETION TIMER
# =========================

async def deletion_timer(
    context,
    user_id,
    message_ids,
    warning_id,
    end_id,
    follow_id,
    anime_id,
    season_id,
    quality
):

    await asyncio.sleep(DELETE_AFTER)

    # Delete episode files
    await delete_messages(
        context,
        user_id,
        message_ids
    )

    # Delete warning
    try:

        await context.bot.delete_message(
            chat_id=user_id,
            message_id=warning_id
        )

    except Exception:

        pass

    # Delete END message
    try:

        await context.bot.delete_message(
            chat_id=user_id,
            message_id=end_id
        )

    except Exception:

        pass

    # Delete follow message
    try:

        await context.bot.delete_message(
            chat_id=user_id,
            message_id=follow_id
        )

    except Exception:

        pass

    # Remove this timer from pending
    pending = load_pending()

    pending = [
        item
        for item in pending
        if not (
            item.get("user_id") == user_id
            and item.get("message_ids") == message_ids
        )
    ]

    save_pending(pending)

    # Retry button
    keyboard = [

        [
            InlineKeyboardButton(
                "♻️ Try Again ♻️",
                callback_data=(
                    f"file_retry|"
                    f"{anime_id}|"
                    f"{season_id}|"
                    f"{quality}"
                )
            )
        ]

    ]

    await context.bot.send_message(
        chat_id=user_id,
        text=(
            "Files deleted successfully ✅\n"
            "Can request files again"
        ),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# RESTORE TIMERS
# =========================

async def restore_timers(application):

    pending = load_pending()

    now = time.time()

    for item in pending:

        remaining = item["delete_at"] - now

        if remaining <= 0:
            remaining = 1

        async def restored_timer(
            item=item,
            remaining=remaining
        ):

            await asyncio.sleep(remaining)

            user_id = item["user_id"]

            # Delete episode files
            for message_id in item["message_ids"]:

                try:

                    await application.bot.delete_message(
                        chat_id=user_id,
                        message_id=message_id
                    )

                except Exception:

                    pass

            # Delete warning
            try:

                await application.bot.delete_message(
                    chat_id=user_id,
                    message_id=item["warning_id"]
                )

            except Exception:

                pass

            # Delete END
            try:

                await application.bot.delete_message(
                    chat_id=user_id,
                    message_id=item["end_id"]
                )

            except Exception:

                pass

            # Delete follow message
            try:

                await application.bot.delete_message(
                    chat_id=user_id,
                    message_id=item["follow_id"]
                )

            except Exception:

                pass

            # Remove from pending
            current = load_pending()

            current = [
                x
                for x in current
                if x != item
            ]

            save_pending(current)

            # Send retry button
            keyboard = [

                [
                    InlineKeyboardButton(
                        "♻️ Try Again ♻️",
                        callback_data=(
                            f"file_retry|"
                            f"{item['anime_id']}|"
                            f"{item['season_id']}|"
                            f"{item['quality']}"
                        )
                    )
                ]

            ]

            await application.bot.send_message(
                chat_id=user_id,
                text=(
                    "Files deleted successfully ✅\n"
                    "Can request files again"
                ),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        asyncio.create_task(
            restored_timer()
        )


# =========================
# MEMBERSHIP CHECK
# =========================

async def is_member(
    context,
    user_id
):

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

    except Exception:

        return False


# =========================
# REQUEST FILES
# =========================

async def request_files(
    context,
    user_id,
    anime_id,
    season_id,
    quality
):

    anime = ANIME.get(anime_id)

    if not anime:

        return

    season = anime["seasons"].get(season_id)

    if not season:

        return

    episodes = season["episodes"].get(
        quality,
        {}
    )

    # =========================
    # QUALITY NOT AVAILABLE
    # =========================

    if not episodes:

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"❌ {quality} is not available yet.\n\n"
                "Please try another quality."
            )
        )

        return

    # =========================
    # MEMBERSHIP CHECK
    # =========================

    member = await is_member(
        context,
        user_id
    )

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
                        f"membership_retry|"
                        f"{anime_id}|"
                        f"{season_id}|"
                        f"{quality}"
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

    # =========================
    # SENDING MESSAGE
    # =========================

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

    # =========================
    # SEND EPISODES
    # =========================

    sent_messages = []

    for episode, storage_message_id in sorted(
        episodes.items()
    ):

        try:

            copied = await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=STORAGE_CHAT_ID,
                message_id=storage_message_id
            )

            sent_messages.append(
                copied.message_id
            )

        except Exception as error:

            print(
                f"Failed to send episode {episode}: {error}"
            )

    # =========================
    # NOTHING SENT
    # =========================

    if not sent_messages:

        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Unable to send the files right now."
        )

        return

    # =========================
    # WARNING
    # =========================

    warning = await context.bot.send_message(
        chat_id=user_id,
        text=(
            "⚠️ Files will be deleted in 15 minutes.\n\n"
            "Please save/download them now or send them "
            "to another chat if you want to keep them."
        )
    )

    # =========================
    # END OF SEASON
    # =========================

    end_message = await context.bot.send_message(
        chat_id=user_id,
        text=f"🎬 END OF SEASON {season_id} 🏁"
    )

    # =========================
    # FOLLOW CHANNELS
    # =========================

    keyboard = [

        [
            InlineKeyboardButton(
                "ZynAnimeHub",
                url="https://t.me/ZynAnimeHub"
            ),

            InlineKeyboardButton(
                "ZynAnime",
                url="https://t.me/ZynAnime"
            )
        ]

    ]

    follow = await context.bot.send_message(
        chat_id=user_id,
        text="🎬 Follow our channels for more anime:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    # =========================
    # SAVE TIMER
    # =========================

    delete_at = time.time() + DELETE_AFTER

    pending = load_pending()

    pending.append({

        "user_id": user_id,

        "message_ids": sent_messages,

        "warning_id": warning.message_id,

        "end_id": end_message.message_id,

        "follow_id": follow.message_id,

        "anime_id": anime_id,

        "season_id": season_id,

        "quality": quality,

        "delete_at": delete_at

    })

    save_pending(pending)

    # Start deletion timer
    asyncio.create_task(

        deletion_timer(
            context,
            user_id,
            sent_messages,
            warning.message_id,
            end_message.message_id,
            follow.message_id,
            anime_id,
            season_id,
            quality
        )

    )


# =========================
# START COMMAND
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    # =========================
    # DEEP LINK REQUEST
    # =========================

    if context.args:

        payload = context.args[0]

        if payload.startswith("request_"):

            parts = payload.split("_")

            if len(parts) >= 4:

                quality = parts[-1]

                season_id = parts[-2]

                anime_id = "_".join(
                    parts[1:-2]
                )

                await request_files(
                    context,
                    user_id,
                    anime_id,
                    season_id,
                    quality
                )

                return

    # =========================
    # NORMAL START
    # =========================

    keyboard = [

        [
            InlineKeyboardButton(
                "📚 Browse Anime",
                url="https://t.me/ZynAnimeHub"
            )
        ]

    ]

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
# MEMBERSHIP TRY AGAIN
# =========================

async def membership_retry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    try:

        parts = query.data.split("|")

        anime_id = parts[1]
        season_id = parts[2]
        quality = parts[3]

    except Exception:

        return

    user_id = query.from_user.id

    # Check membership again
    member = await is_member(
        context,
        user_id
    )

    if not member:

        await query.answer(
            "❌ Please join the channel first.",
            show_alert=True
        )

        return

    # Delete ONLY the DM membership message
    try:

        await query.message.delete()

    except Exception:

        pass

    # Automatically send the same files
    await request_files(
        context,
        user_id,
        anime_id,
        season_id,
        quality
    )


# =========================
# FILE RETRY
# =========================

async def file_retry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    try:

        parts = query.data.split("|")

        anime_id = parts[1]
        season_id = parts[2]
        quality = parts[3]

    except Exception:

        return

    user_id = query.from_user.id

    # Delete old retry message
    try:

        await query.message.delete()

    except Exception:

        pass

    # Request the exact same files again
    await request_files(
        context,
        user_id,
        anime_id,
        season_id,
        quality
    )


# =========================
# POST DATING SIM
# =========================

async def post(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    anime = ANIME["dating_sim"]

    await context.bot.send_message(
        chat_id=CHANNEL,
        text=(
            f"🎬 {anime['title']}\n\n"
            "Season 1 — 12 Episodes\n"
            "Season 2 — 10 Episodes"
        )
    )

    # =========================
    # SEASON 1
    # =========================

    buttons_s1 = [

        [

            InlineKeyboardButton(
                "480p",
                url=(
                    f"https://t.me/{BOT_USERNAME}"
                    "?start=request_dating_sim_1_480p"
                )
            ),

            InlineKeyboardButton(
                "720p",
                url=(
                    f"https://t.me/{BOT_USERNAME}"
                    "?start=request_dating_sim_1_720p"
                )
            ),

            InlineKeyboardButton(
                "1080p",
                url=(
                    f"https://t.me/{BOT_USERNAME}"
                    "?start=request_dating_sim_1_1080p"
                )
            )

        ]

    ]

    await context.bot.send_message(
        chat_id=CHANNEL,
        text="Season 1",
        reply_markup=InlineKeyboardMarkup(
            buttons_s1
        )
    )

    # =========================
    # SEASON 2
    # =========================

    buttons_s2 = [

        [

            InlineKeyboardButton(
                "480p",
                url=(
                    f"https://t.me/{BOT_USERNAME}"
                    "?start=request_dating_sim_2_480p"
                )
            ),

            InlineKeyboardButton(
                "720p",
                url=(
                    f"https://t.me/{BOT_USERNAME}"
                    "?start=request_dating_sim_2_720p"
                )
            ),

            InlineKeyboardButton(
                "1080p",
                url=(
                    f"https://t.me/{BOT_USERNAME}"
                    "?start=request_dating_sim_2_1080p"
                )
            )

        ]

    ]

    await context.bot.send_message(
        chat_id=CHANNEL,
        text="Season 2",
        reply_markup=InlineKeyboardMarkup(
            buttons_s2
        )
    )


# =========================
# POST TOMODACHI GAME
# =========================

async def post_tomodachi(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    anime = ANIME["tomodachi_game"]

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

    await context.bot.send_message(
        chat_id=CHANNEL,
        text=text
    )

    buttons = [

        [

            InlineKeyboardButton(
                "480p",
                url=(
                    f"https://t.me/{BOT_USERNAME}"
                    "?start=request_tomodachi_game_1_480p"
                )
            ),

            InlineKeyboardButton(
                "720p",
                url=(
                    f"https://t.me/{BOT_USERNAME}"
                    "?start=request_tomodachi_game_1_720p"
                )
            ),

            InlineKeyboardButton(
                "1080p",
                url=(
                    f"https://t.me/{BOT_USERNAME}"
                    "?start=request_tomodachi_game_1_1080p"
                )
            )

        ]

    ]

    await context.bot.send_message(
        chat_id=CHANNEL,
        text="Season 1",
        reply_markup=InlineKeyboardMarkup(
            buttons
        )
    )


# =========================
# APPLICATION
# =========================

async def post_init(
    application
):

    await restore_timers(
        application
    )


application = (
    Application.builder()
    .token(TOKEN)

    # IMPORTANT:
    # Local Telegram Bot API requires /bot here.
    .base_url(
        f"{LOCAL_API}/bot"
    )

    .post_init(
        post_init
    )

    .build()
)


# =========================
# HANDLERS
# =========================

application.add_handler(
    CommandHandler(
        "start",
        start
    )
)

application.add_handler(
    CommandHandler(
        "post",
        post
    )
)

application.add_handler(
    CommandHandler(
        "post_tomodachi",
        post_tomodachi
    )
)

application.add_handler(
    CallbackQueryHandler(
        membership_retry,
        pattern=r"^membership_retry\|"
    )
)

application.add_handler(
    CallbackQueryHandler(
        file_retry,
        pattern=r"^file_retry\|"
    )
)


# =========================
# START BOT
# =========================

print(
    "🤖 Zyn Anime Bot starting..."
)

application.run_polling()
