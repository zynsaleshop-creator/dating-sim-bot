async def episode(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    # Check required channel membership
    member = await context.bot.get_chat_member(
        chat_id=REQUIRED_CHANNEL,
        user_id=query.from_user.id
    )

    if member.status not in ["member", "administrator", "creator"]:
        keyboard = [
            [
                InlineKeyboardButton(
                    "📢 Join Zyn Anime",
                    url="https://t.me/zynanime"
                )
            ],
            [
                InlineKeyboardButton(
                    "✅ I've Joined",
                    callback_data=query.data
                )
            ]
        ]

        await query.message.reply_text(
            "⚠️ Please join Zyn Anime first.\n\n"
            "After joining, tap **I've Joined** to get your episode.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

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
