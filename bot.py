import os
import asyncio
import json
import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.environ["BOT_TOKEN"]
LOCAL_API = os.environ["LOCAL_BOT_API"]

STORAGE_CHAT_ID = -1003947631814

CHANNEL = "@ZynAnimeHub"
REQUIRED_CHANNEL = "@ZynAnime"

BOT_USERNAME = "ZynAnimeBot"

DELETE_AFTER = 15 * 60
PENDING_FILE = "pending_deletions.json"


# =========================================================
# ANIME DATA
# =========================================================

ANIME = {

    "dating_sim": {

        "title":
        "Trapped in a Dating Sim: The World of Otome Games Is Tough for Mobs",

        "seasons": {

            "s1": {

                "name":
                "Season 1",

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
                        12: 19,
                    },

                    "720p": {},

                    "1080p": {},
                },
            },

            "s2": {

                "name":
                "Season 2",

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
                        10: 24,
                    },

                    "720p": {},

                    "1080p": {},
                },
            },
        },
    },


    "tomodachi_game": {

        "title":
        "Tomodachi Game",

        "seasons": {

            "s1": {

                "name":
                "Season 1",

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
                        12: 37,
                    },

                    "720p": {},

                    "1080p": {},
                },
            },
        },
    },
}


# =========================================================
# PENDING DELETIONS
# =========================================================

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


# =========================================================
# DELETE MESSAGES
# =========================================================

async def delete_messages(chat_id, message_ids):

    for message_id in message_ids:

        try:

            await app.bot.delete_message(
                chat_id=chat_id,
                message_id=message_id,
            )

        except Exception:
            pass


# =========================================================
# CREATE RETRY BUTTON
# =========================================================

def create_retry_button(item):

    payload = (
        f"retry_"
        f"{item['anime_id']}_"
        f"{item['season_id']}_"
        f"{item['quality']}"
    )

    return InlineKeyboardButton(
        "♻️ Try Again ♻️",
        url=(
            f"https://t.me/"
            f"{BOT_USERNAME}"
            f"?start={payload}"
        ),
    )


# =========================================================
# SEND RETRY MESSAGE
# =========================================================

async def send_retry_message(item):

    keyboard = [[
        create_retry_button(item)
    ]]

    await app.bot.send_message(

        chat_id=item["chat_id"],

        text=(
            "Files deleted successfully ✅\n"
            "Can request files again"
        ),

        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
    )


# =========================================================
# DELETION TIMER
# =========================================================

async def deletion_timer(item):

    try:

        wait_time = (
            item["delete_at"] -
            time.time()
        )

        if wait_time > 0:

            await asyncio.sleep(
                wait_time
            )


        # -------------------------------------------------
        # DELETE ANIME FILES
        # -------------------------------------------------

        await delete_messages(

            item["chat_id"],

            item["message_ids"],
        )


        # -------------------------------------------------
        # DELETE WARNING / END / FOLLOW
        # -------------------------------------------------

        await delete_messages(

            item["chat_id"],

            item.get(
                "extra_message_ids",
                [],
            ),
        )


        # -------------------------------------------------
        # REMOVE FROM PENDING
        # -------------------------------------------------

        global PENDING_DELETIONS

        PENDING_DELETIONS = [

            x for x in PENDING_DELETIONS

            if x["id"] != item["id"]
        ]

        save_pending(
            PENDING_DELETIONS
        )


        # -------------------------------------------------
        # LEAVE RETRY BUTTON
        # -------------------------------------------------

        await send_retry_message(
            item
        )


    except Exception as e:

        print(
            "⚠️ Deletion timer error:",
            e,
        )


# =========================================================
# RESTORE TIMERS
# =========================================================

async def restore_timers(application):

    for item in list(
        PENDING_DELETIONS
    ):

        asyncio.create_task(
            deletion_timer(item)
        )


# =========================================================
# PARSE DEEP LINK
# =========================================================

def parse_request(payload):

    try:

        parts = payload.split("_")


        # -------------------------------------------------
        # check_dating_sim_s1_480p
        # -------------------------------------------------

        if parts[0] == "check":

            quality = parts[-1]
            season_id = parts[-2]

            anime_id = "_".join(
                parts[1:-2]
            )

            return (
                anime_id,
                season_id,
                quality,
            )


        # -------------------------------------------------
        # retry_dating_sim_s1_480p
        # -------------------------------------------------

        if parts[0] == "retry":

            quality = parts[-1]
            season_id = parts[-2]

            anime_id = "_".join(
                parts[1:-2]
            )

            return (
                anime_id,
                season_id,
                quality,
            )


    except Exception:

        pass


    return None


# =========================================================
# START
# =========================================================

async def start(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE,

):

    args = context.args


    # =====================================================
    # DEEP LINK REQUEST
    # =====================================================

    if args:

        request = parse_request(
            args[0]
        )


        if request:

            anime_id, season_id, quality = request


            await send_files(

                update,

                context,

                anime_id,

                season_id,

                quality,
            )

            return


    # =====================================================
    # NORMAL START
    # =====================================================

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

        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
    )


# =========================================================
# SEND FILES
# =========================================================

async def send_files(

    update,

    context,

    anime_id,

    season_id,

    quality,

):

    user_id = update.effective_user.id


    # =====================================================
    # FIND ANIME
    # =====================================================

    anime = ANIME.get(
        anime_id
    )


    if not anime:

        await context.bot.send_message(

            chat_id=user_id,

            text="❌ Anime not found.",
        )

        return


    # =====================================================
    # FIND SEASON
    # =====================================================

    season = anime["seasons"].get(
        season_id
    )


    if not season:

        await context.bot.send_message(

            chat_id=user_id,

            text="❌ Season not found.",
        )

        return


    # =====================================================
    # FIND QUALITY
    # =====================================================

    episodes = season[
        "episodes"
    ].get(
        quality,
        {}
    )


    # =====================================================
    # QUALITY NOT AVAILABLE
    # =====================================================

    if not episodes:

        await context.bot.send_message(

            chat_id=user_id,

            text=(
                f"❌ {quality} is not available yet.\n\n"
                "Please try another quality."
            ),
        )

        return


    # =====================================================
    # MEMBERSHIP CHECK
    # =====================================================

    try:

        member = await context.bot.get_chat_member(

            chat_id=REQUIRED_CHANNEL,

            user_id=user_id,
        )

        is_member = member.status in [

            "member",
            "administrator",
            "creator",
        ]

    except Exception:

        is_member = False


    # =====================================================
    # NOT A MEMBER
    # =====================================================

    if not is_member:

        keyboard = [

            [

                InlineKeyboardButton(

                    "📢 Join Channel",

                    url="https://t.me/zynanime",
                )

            ],

            [

                InlineKeyboardButton(

                    "♻️ Try Again",

                    callback_data=(
                        f"check|"
                        f"{anime_id}|"
                        f"{season_id}|"
                        f"{quality}"
                    ),
                )

            ],
        ]


        await context.bot.send_message(

            chat_id=user_id,

            text=(
                "🔒 You must join our channel "
                "before requesting anime files."
            ),

            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )

        return


    # =====================================================
    # SENDING MESSAGE
    # =====================================================

    sending = await context.bot.send_message(

        chat_id=user_id,

        text="📤 Sending files...",
    )


    try:

        await sending.delete()

    except Exception:

        pass


    loading = await context.bot.send_message(

        chat_id=user_id,

        text=".......",
    )


    try:

        await loading.delete()

    except Exception:

        pass


    # =====================================================
    # SEND EPISODES
    # =====================================================

    sent_ids = []


    for episode, storage_message_id in episodes.items():

        try:

            sent_message = (
                await context.bot.copy_message(

                    chat_id=user_id,

                    from_chat_id=STORAGE_CHAT_ID,

                    message_id=storage_message_id,
                )
            )


            sent_ids.append(
                sent_message.message_id
            )


        except Exception as e:

            print(
                f"⚠️ Error sending episode "
                f"{episode}: {e}"
            )


    # =====================================================
    # WARNING
    # =====================================================

    warning = await context.bot.send_message(

        chat_id=user_id,

        text=(
            "⚠️ Files will be deleted in 15 minutes.\n\n"
            "Please save/download them now or send them "
            "to another chat if you want to keep them."
        ),
    )


    # =====================================================
    # END OF SEASON
    # =====================================================

    end = await context.bot.send_message(

        chat_id=user_id,

        text=(
            f"🎬 END OF "
            f"{season['name'].upper()} 🏁"
        ),
    )


    # =====================================================
    # FOLLOW CHANNELS
    # =====================================================

    keyboard = [[

        InlineKeyboardButton(

            "ZynAnimeHub",

            url="https://t.me/ZynAnimeHub",
        ),

        InlineKeyboardButton(

            "ZynAnime",

            url="https://t.me/zynanime",
        ),

    ]]


    follow_message = await context.bot.send_message(

        chat_id=user_id,

        text=(
            "🎬 Follow our channels for more anime:"
        ),

        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
    )


    # =====================================================
    # SAVE DELETION TIMER
    # =====================================================

    item = {

        "id": (
            f"{user_id}-"
            f"{int(time.time() * 1000)}"
        ),

        "chat_id":
        user_id,

        "message_ids":
        sent_ids,

        "extra_message_ids": [

            warning.message_id,

            end.message_id,

            follow_message.message_id,

        ],

        # EXACT ORIGINAL REQUEST
        "anime_id":
        anime_id,

        "season_id":
        season_id,

        "quality":
        quality,

        "delete_at":
        time.time() + DELETE_AFTER,
    }


    PENDING_DELETIONS.append(
        item
    )

    save_pending(
        PENDING_DELETIONS
    )


    # Start fresh 15-minute timer
    asyncio.create_task(
        deletion_timer(item)
    )


# =========================================================
# CALLBACK MEMBERSHIP TRY AGAIN
# =========================================================

async def check_membership(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE,

):

    query = update.callback_query

    await query.answer()


    try:

        _,
        anime_id,
        season_id,
        quality = query.data.split("|")

    except Exception:

        return


    # Delete only the membership
    # Try Again message.

    try:

        await query.message.delete()

    except Exception:

        pass


    await send_files(

        update,

        context,

        anime_id,

        season_id,

        quality,
    )


# =========================================================
# QUALITY BUTTON
# =========================================================

def quality_button(

    anime_id,

    season_id,

    quality,

):

    payload = (

        f"check_"
        f"{anime_id}_"
        f"{season_id}_"
        f"{quality}"
    )


    return InlineKeyboardButton(

        f"📥 {quality}",

        url=(
            f"https://t.me/"
            f"{BOT_USERNAME}"
            f"?start={payload}"
        ),
    )


# =========================================================
# POST DATING SIM
# =========================================================

async def post(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE,

):

    anime = ANIME[
        "dating_sim"
    ]


    # No Dating Sim description/details.
    # Only title + seasons + quality buttons.

    for season_id, season in anime[
        "seasons"
    ].items():

        keyboard = []


        for quality in [

            "480p",
            "720p",
            "1080p",

        ]:

            keyboard.append([

                quality_button(

                    "dating_sim",

                    season_id,

                    quality,
                )

            ])


        episodes = season[
            "episodes"
        ][
            "480p"
        ]


        await context.bot.send_message(

            chat_id=CHANNEL,

            text=(

                f"🎬 {anime['title']}\n\n"

                f"📚 {season['name']}\n\n"

                f"📺 Episodes: "
                f"{len(episodes)}"
            ),

            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )


    await update.message.reply_text(

        "✅ Dating Sim posted."
    )


# =========================================================
# POST TOMODACHI GAME
# =========================================================

async def post_tomodachi(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE,

):

    anime = ANIME[
        "tomodachi_game"
    ]


    await context.bot.send_message(

        chat_id=CHANNEL,

        text="━━━━━━━━━━━━━━━━━━",
    )


    # =====================================================
    # DETAILS
    # =====================================================

    details = (

        "🎬 Tomodachi Game\n\n"

        "‣ Genres : Drama, Mystery, Psychological\n"
        "‣ Type : TV\n"
        "‣ Average Rating : 77\n"
        "‣ Status : FINISHED\n"
        "‣ First aired : 2022-4-6\n"
        "‣ Last aired : 2022-6-22\n"
        "‣ Runtime : 22 minutes\n"
        "‣ No of episodes : 12\n\n"

        "High school student Yuuichi Katagiri values "
        "friendship above all else. But after the money "
        "for a school trip is stolen, Yuuichi and his "
        "four friends are dragged into a mysterious debt "
        "repayment game. To escape, they must take part "
        "in psychological games that test their trust, "
        "friendship and true nature."
    )


    await context.bot.send_message(

        chat_id=CHANNEL,

        text=details,
    )


    # =====================================================
    # SEASONS
    # =====================================================

    for season_id, season in anime[
        "seasons"
    ].items():

        keyboard = []


        for quality in [

            "480p",
            "720p",
            "1080p",

        ]:

            keyboard.append([

                quality_button(

                    "tomodachi_game",

                    season_id,

                    quality,
                )

            ])


        episodes = season[
            "episodes"
        ][
            "480p"
        ]


        await context.bot.send_message(

            chat_id=CHANNEL,

            text=(

                f"🎬 {season['name']}\n\n"

                f"📺 Episodes: "
                f"{len(episodes)}"
            ),

            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )


    await context.bot.send_message(

        chat_id=CHANNEL,

        text="━━━━━━━━━━━━━━━━━━",
    )


    await update.message.reply_text(

        "✅ Tomodachi Game posted."
    )


# =========================================================
# APPLICATION
# =========================================================

app = (

    Application.builder()

    .token(TOKEN)

    .base_url(
        LOCAL_API + "/bot"
    )

    .base_file_url(
        LOCAL_API + "/file/bot"
    )

    .local_mode(True)

    .post_init(
        restore_timers
    )

    .build()
)


# =========================================================
# HANDLERS
# =========================================================

app.add_handler(

    CommandHandler(
        "start",
        start,
    )
)


app.add_handler(

    CommandHandler(
        "post",
        post,
    )
)


app.add_handler(

    CommandHandler(
        "post_tomodachi",
        post_tomodachi,
    )
)


app.add_handler(

    CallbackQueryHandler(

        check_membership,

        pattern=r"^check\|",
    )
)


# =========================================================
# RUN
# =========================================================

app.run_polling()
