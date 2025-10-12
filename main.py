from typing import final
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from ConfigHandler import create_trial_user_api

TOKEN: final = '7300849904:AAGVUbRVtr9vj6NEgk3kdURCWvgYtWj6SVk'
BOT_USERNAME: final = '@CyvraVPN_bot'
CHANNEL_ID = "@CyvraVPN"


# ---------------------- دستورات ----------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        status = member.status
    except Exception as e:
        print("Error checking membership:", e)
        status = None

    if status not in ("member", "administrator", "creator"):
        keyboard = [
            [InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_ID[1:]}")]
        ]
        markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "⚠️ برای استفاده از ربات باید در کانال ما عضو بشی.\n\n"
            "بعد از عضویت، دستور /start رو دوباره بزن ✅",
            reply_markup=markup
        )
        return

    # اگر عضو بود، منوی اصلی نمایش داده بشه
    keyboard = [
        [KeyboardButton("🛒 خرید"), KeyboardButton("🧪 تست رایگان")],
        [KeyboardButton("💬 پشتیبانی"), KeyboardButton("ℹ️ راهنما")]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    text = (
        "👋 به ربات **Cyvra VPN** خوش اومدی!\n\n"
        "از منوی زیر می‌تونی بخش مورد نظرت رو انتخاب کنی:\n"
        "🛒 خرید اشتراک\n"
        "🧪 دریافت تست رایگان\n"
        "💬 ارتباط با پشتیبانی\n"
        "ℹ️ راهنما و توضیحات سرویس‌ها"
    )
    await update.message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "ℹ️ **راهنمای استفاده از ربات Cyvra VPN**\n\n"
        "1️⃣ از دکمه‌ی *تست رایگان* استفاده کن تا کیفیت سرور رو بررسی کنی.\n"
        "2️⃣ اگر از سرعت و پایداری راضی بودی، از بخش *خرید* اشتراک تهیه کن.\n"
        "3️⃣ برای هرگونه سوال یا مشکل، از دکمه‌ی *پشتیبانی* استفاده کن.\n\n"
        "🚀 هدف ما ارائه‌ی اینترنتی سریع، پایدار و امن برای همه‌ی کاربران ایرانیه."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🛒 خرید":
        await update.message.reply_text(
            "💳 برای خرید اشتراک، ابتدا مدت زمان مورد نظر خود را انتخاب کنید:\n"
            "۱ ماهه – 45 هزار تومان\n"
            "۳ ماهه – 120 هزار تومان\n"
            "۶ ماهه – 200 هزار تومان\n\n"
            "برای خرید لطفاً با پشتیبانی تماس بگیرید 💬"
        )

    elif text == "🧪 تست رایگان":
        await update.message.reply_text("در حال ساخت اکانت تست... لطفاً شکیبا باشید ⏳")
        user_id = f"tg_{update.effective_user.id}"
        result = await create_trial_user_api(user_id, hours=24, traffic_bytes=100 * 1024 * 1024)
        if "error" in result:
            await update.message.reply_text(f"مشکل در ساخت اکانت تست:\n{result['error']}")
        else:
            await update.message.reply_text(f"اکانت تست ساخته شد ✅\n\nلینک اتصال:\n{result['link']}\n\nاعتبار: 24 ساعت")

    elif text == "💬 پشتیبانی":
        await update.message.reply_text(
            "💬 برای ارتباط با پشتیبانی لطفاً به آی‌دی زیر پیام بده:\n"
            "@CyvraSupport"
        )

    elif text == "ℹ️ راهنما":
        await help_command(update, context)
    else:
        await update.message.reply_text("لطفاً یکی از گزینه‌های منو را انتخاب کنید ⬇️")


# ---------------------- راه‌اندازی ----------------------

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Cyvra VPN Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
