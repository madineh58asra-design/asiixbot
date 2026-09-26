import os
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

waiting_user = None
partners = {}
lock = asyncio.Lock()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 به چت ناشناس Asiix خوش اومدی!\n\n"
        "🎲 برای پیدا کردن یک نفر ناشناس، /find رو بزن.\n"
        "❌ برای پایان چت، /stop رو بزن.\n"
        "⏭️ برای نفر جدید، /next رو بزن."
    )


async def find_partner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_user

    user_id = update.effective_user.id

    async with lock:
        if user_id in partners:
            await update.message.reply_text("⚠️ تو همین الان داخل یک چت هستی.")
            return

        if waiting_user == user_id:
            await update.message.reply_text("⏳ در حال پیدا کردن یک نفر برای تو هستم...")
            return

        if waiting_user is None:
            waiting_user = user_id
            await update.message.reply_text(
                "🔎 منتظرم یک نفر دیگه وارد بشه..."
            )
            return

        partner = waiting_user
        waiting_user = None

        partners[user_id] = partner
        partners[partner] = user_id

    await context.bot.send_message(
        user_id,
        "🎉 یک نفر پیدا شد!\n\nحالا می‌تونی ناشناس چت کنی. 💬\nبرای پایان /stop"
    )

    await context.bot.send_message(
        partner,
        "🎉 یک نفر پیدا شد!\n\nحالا می‌تونی ناشناس چت کنی. 💬\nبرای پایان /stop"
    )


async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_user

    user_id = update.effective_user.id

    async with lock:
        if waiting_user == user_id:
            waiting_user = None
            await update.message.reply_text("❌ جستجو متوقف شد.")
            return

        partner = partners.pop(user_id, None)

        if partner is None:
            await update.message.reply_text("ℹ️ تو الان داخل چتی نیستی.")
            return

        partners.pop(partner, None)

    await update.message.reply_text("❌ چت تمام شد.")

    await context.bot.send_message(
        partner,
        "❌ طرف مقابل چت را ترک کرد.\n\n"
        "🎲 برای پیدا کردن یک نفر جدید /find رو بزن."
    )


async def next_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await stop_chat(update, context)
    await find_partner(update, context)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    async with lock:
        partner = partners.get(user_id)

    if partner is None:
        await update.message.reply_text(
            "💬 هنوز وارد چت نشدی.\n"
            "برای پیدا کردن یک نفر /find رو بزن."
        )
        return

    try:
        await context.bot.copy_message(
            chat_id=partner,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
        )
    except Exception:
        await update.message.reply_text(
            "⚠️ این نوع پیام فعلاً قابل ارسال نیست."
        )


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("find", find_partner))
    app.add_handler(CommandHandler("stop", stop_chat))
    app.add_handler(CommandHandler("next", next_chat))

    app.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND, message_handler)
    )

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
