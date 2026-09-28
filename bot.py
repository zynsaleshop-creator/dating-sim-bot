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

DELETE_AFTER = 15 * 60
PENDING_FILE = "pending_deletions.json"


# =========================================================
# ANIME DATA
# =========================================================

ANIME = {

    "dating_sim": {

        "title":
        "Trapped in a Dating Sim: The World of Otome Games Is Tough for Mobs",

        "japanese_title":
        "Otomege Sekai wa Mob ni Kibishii Sekai desu",

        "description":
        "Office worker Leon is reincarnated into a particularly punishing "
        "dating sim where women reign supreme and only beautiful men have "
        "a seat at the table. But Leon has a secret weapon: he remembers "
        "his past life, including a complete playthrough of the game in "
        "which he is now trapped. Watch Leon spark a revolution to change "
        "this new world in order to fulfill his ultimate desire... of "
        "living a quiet, easy life in the countryside!",

        "genres":
        "Action, Fantasy, Mecha, Romance",

        "type":
        "TV",

        "rating":
        "71",

        "status":
        "FINISHED",

        "first_aired":
        "2022-4-3",

        "last_aired":
        "2022-6-19",

        "runtime":
        "24 minutes",

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
# RETRY BUTTON AFTER DELETION
# =========================================================

async def send_retry_message(item):

    keyboard = [[

        InlineKeyboardButton(
            "♻️ Try Again ♻️",

            callback_data=(
                f"retry|"
                f"{item['anime_id']}|"
                f"{item['season_id']}|"
                f"{item['quality']}"
            ),
        )

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


        # Delete anime files
        await delete_messages(

            item["chat_id"],

            item["message_ids"],
        )


        # Delete warning,
        # END message,
        # and follow message
        await delete_messages(

            item["chat_id"],

            item.get(
                "extra_message_ids",
                [],
            ),
        )


        global PENDING_DELETIONS

        PENDING_DELETIONS = [

            x for x in PENDING_DELETIONS

            if x["id"] != item["id"]
        ]

        save_pending(
            PENDING_DELETIONS
        )


        # Leave retry message
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

async def restore_timers(
    application
):

    for item in list(
        PENDING_DELETIONS
    ):

        asyncio.create_task(
            deletion_timer(item)
        )


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

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
# MAIN FILE REQUEST
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


    anime = ANIME.get(
        anime_id
    )

    if not anime:

        await context.bot.send_message(

            chat_id=query.from_user.id,

            text="❌ Anime not found.",
        )

        return


    season = anime["seasons"].get(
        season_id
    )

    if not season:

        await context.bot.send_message(

            chat_id=query.from_user.id,

            text="❌ Season not found.",
        )

        return


    episodes = season[
        "episodes"
    ].get(
        quality,
        {}
    )


    # =====================================================
    # QUALITY NOT UPLOADED
    # =====================================================

    if not episodes:

        await context.bot.send_message(

            chat_id=query.from_user.id,

            text=(
                f"❌ {quality} is not available yet.\n\n"
                "Please try another quality."
            ),
        )

        return


    # =====================================================
    # CHECK MEMBERSHIP
    # =====================================================

    try:

        member = await context.bot.get_chat_member(

            chat_id=REQUIRED_CHANNEL,

            user_id=query.from_user.id,
        )

        is_member = member.status in [

            "member",
            "administrator",
            "creator",
        ]

    except Exception:

        is_member = False


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

            chat_id=query.from_user.id,

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
    # DO NOT DELETE THE CHANNEL BUTTON MESSAGE
    # =====================================================
    #
    # IMPORTANT:
    # The quality button in ZynAnimeHub stays there.
    #
    # We intentionally DO NOT use:
    #
    # await query.message.delete()
    #
    # =====================================================


    # =====================================================
    # SEND TEMPORARY MESSAGE
    # =====================================================

    sending = await context.bot.send_message(

        chat_id=query.from_user.id,

        text="📤 Sending files...",
    )


    try:

        await sending.delete()

    except Exception:

        pass


    loading = await context.bot.send_message(

        chat_id=query.from_user.id,

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

                    chat_id=query.from_user.id,

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

        chat_id=query.from_user.id,

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

        chat_id=query.from_user.id,

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

        chat_id=query.from_user.id,

        text=(
            "🎬 Follow our channels for more anime:"
        ),

        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
    )


    # =====================================================
    # SAVE TIMER
    # =====================================================

    item = {

        "id": (
            f"{query.from_user.id}-"
            f"{int(time.time() * 1000)}"
        ),

        "chat_id":
        query.from_user.id,

        "message_ids":
        sent_ids,

        "extra_message_ids": [

            warning.message_id,

            end.message_id,

            follow_message.message_id,

        ],

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


    asyncio.create_task(
        deletion_timer(item)
    )


# =========================================================
# RETRY
# =========================================================

async def retry_files(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE,

):

    query = update.callback_query


    try:

        _,
        anime_id,
        season_id,
        quality = query.data.split("|")

    except Exception:

        return


    # Delete ONLY the old retry message
    # from the user's DM.

    try:

        await query.message.delete()

    except Exception:

        pass


    # Request the same anime,
    # season and quality again.

    query.data = (

        f"check|"
        f"{anime_id}|"
        f"{season_id}|"
        f"{quality}"
    )


    await check_membership(

        update,

        context,
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


    details = (

        f"🎬 {anime['title']}\n\n"

        f"🇯🇵 Japanese: "
        f"{anime['japanese_title']}\n\n"

        f"‣ Genres : "
        f"{anime['genres']}\n"

        f"‣ Type : "
        f"{anime['type']}\n"

        f"‣ Average Rating : "
        f"{anime['rating']}\n"

        f"‣ Status : "
        f"{anime['status']}\n"

        f"‣ First aired : "
        f"{anime['first_aired']}\n"

        f"‣ Last aired : "
        f"{anime['last_aired']}\n"

        f"‣ Runtime : "
        f"{anime['runtime']}\n\n"

        f"{anime['description']}"
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


        # Show ALL qualities
        # even if not uploaded.

        for quality in [

            "480p",
            "720p",
            "1080p",

        ]:

            keyboard.append([

                InlineKeyboardButton(

                    f"📥 {quality}",

                    callback_data=(

                        f"check|"
                        f"dating_sim|"
                        f"{season_id}|"
                        f"{quality}"
                    ),
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


    await context.bot.send_message(

        chat_id=CHANNEL,

        text="🎬 Tomodachi Game",
    )


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

                InlineKeyboardButton(

                    f"📥 {quality}",

                    callback_data=(

                        f"check|"
                        f"tomodachi_game|"
                        f"{season_id}|"
                        f"{quality}"
                    ),
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

        retry_files,

        pattern=r"^retry\|",
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
