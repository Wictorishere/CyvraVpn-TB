import asyncio
from typing import Final
from telegram import (
    Update, KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
import datetime

# ------------------- تنظیمات -------------------
TOKEN: Final = "7300849904:AAGVUbRVtr9vj6NEgk3kdURCWvgYtWj6SVk"
BOT_USERNAME: Final = "@CyvraVPN_bot"
ADMIN_ID: Final = 5859015821
CHANNEL_USERNAME: Final = "@CyvraVPN"

# ------------------- دیتابیس اصلی برای خریدها -------------------
engine_main = create_engine("sqlite:///bot.db")
BaseMain = declarative_base()

class PurchaseRequest(BaseMain):
    __tablename__ = "purchase_requests"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    plan = Column(String)
    status = Column(String)  # pending, paid, approved

BaseMain.metadata.create_all(engine_main)
SessionMain = sessionmaker(bind=engine_main)

# ------------------- دیتابیس برای تست رایگان -------------------
engine_test = create_engine("sqlite:///configs.db", connect_args={"check_same_thread": False})
BaseTest = declarative_base()

class Config(BaseTest):
    __tablename__ = "configs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    test_configs = Column(String)

class TrialUsed(BaseTest):
    __tablename__ = "trial_used"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True)
    date = Column(String, default=str(datetime.date.today()))

BaseTest.metadata.create_all(engine_test)
SessionTest = sessionmaker(bind=engine_test)

# ------------------- بررسی عضویت -------------------
async def is_user_in_channel(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

# ------------------- فرمان /start -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    in_channel = await is_user_in_channel(context, user_id)
    if not in_channel:
        keyboard = [
            [InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}")],
            [InlineKeyboardButton("✅ بررسی عضویت", callback_data="check_membership")]
        ]
        await update.message.reply_text(
            "🚫 برای استفاده از ربات، ابتدا باید در کانال ما عضو شوی.\n\n"
            "👇 روی دکمه زیر بزن و بعد از عضویت، دکمه بررسی عضویت را بزن.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    keyboard = [
        [KeyboardButton("🛒 خرید"), KeyboardButton("🧪 تست رایگان")],
        [KeyboardButton("💬 پشتیبانی"), KeyboardButton("ℹ️ راهنما")]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "👋 به ربات Cyvra VPN خوش اومدی!\n\n"
        "از منوی زیر انتخاب کن 👇",
        reply_markup=markup
    )

# ------------------- بررسی مجدد عضویت -------------------
async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    in_channel = await is_user_in_channel(context, user_id)
    if in_channel:
        keyboard = [
            [KeyboardButton("🛒 خرید"), KeyboardButton("🧪 تست رایگان")],
            [KeyboardButton("💬 پشتیبانی"), KeyboardButton("ℹ️ راهنما")]
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await query.message.reply_text(
            "✅ عضویت تایید شد!\n\nحالا می‌تونی از ربات استفاده کنی 👇",
            reply_markup=markup,
        )

    else:
        await query.message.reply_text("🚫 هنوز عضو کانال نیستی! لطفاً عضو شو و دوباره امتحان کن.")

# ------------------- راهنما -------------------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📘 راهنما:\n\n"
        "1️⃣ تمام کانفیگ ها در حال حاضر روی سرور هلند قرار دارند.\n"
        "2️⃣ کانفیگ ها بدون قطعی هستند و تا اتمام حجم یا زمانتون می تونید بهشون متصل بشید و در صورت قطعی به زمان شما اضافه خواهد شد\n"
        "3️⃣ برای اطلاع از حجم باقی مانده خود به پشتیبانی پیام دهید"
    )

# ------------------- تست رایگان -------------------
def get_one_test_config(session: SessionTest):
    cfg = session.query(Config).first()
    if not cfg:
        return None
    text = cfg.test_configs
    session.delete(cfg)
    session.commit()
    return text

def user_has_trial(session: SessionTest, user_id: int) -> bool:
    return session.query(TrialUsed).filter_by(user_id=user_id).first() is not None

def register_trial(session: SessionTest, user_id: int):
    trial = TrialUsed(user_id=user_id)
    session.add(trial)
    session.commit()

async def handle_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = SessionTest()

    if user_has_trial(session, user_id):
        await update.message.reply_text("⚠️ شما قبلاً تست رایگان دریافت کرده‌اید!")
        session.close()
        return

    config = get_one_test_config(session)
    if not config:
        await update.message.reply_text("❌ متاسفانه در حال حاضر هیچ کانفیگ تستی موجود نیست.")
        session.close()
        return

    register_trial(session, user_id)
    session.close()

    await update.message.reply_text(
        f"✅ این هم کانفیگ تست شما:\n\n<code>{config}</code>\n\n⚠️ این تست فقط برای ۲۴ ساعت معتبر است.",
        parse_mode="HTML"
    )

# ------------------- خرید -------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🛒 خرید":
        keyboard = [
            [InlineKeyboardButton("۱ ماهه 10 گیگ – 25 هزار تومان", callback_data="plan_1")],
            [InlineKeyboardButton("۱ ماهه 20 گیگ – 45 هزار تومان", callback_data="plan_2")],
            [InlineKeyboardButton( "۱ ماهه نامحدود – 85 هزار تومان", callback_data="plan_3")]
        ]
        await update.message.reply_text(
            "📦 لطفاً پلن مورد نظر را انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif text == "🧪 تست رایگان":
        await handle_test(update, context)

    elif text == "💬 پشتیبانی":
        await update.message.reply_text("💬 ارتباط با پشتیبانی: @CyvraSupport")

    elif text == "ℹ️ راهنما":
        await help_command(update, context)

# ------------------- انتخاب پلن -------------------
async def plan_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    plan_map = {
        "plan_1": "۱ ماهه 10 گیگ – 25 هزار تومان",
        "plan_2": "۱ ماهه 20 گیگ – 45 هزار تومان",
        "plan_3": "۱ ماهه نامحدود(مصرف منصفانه) – 85 هزار تومان"
    }

    plan = plan_map.get(query.data)
    context.user_data["selected_plan"] = plan

    keyboard = [
        [InlineKeyboardButton("تأیید و پرداخت ✅", callback_data="confirm_purchase")],
        [InlineKeyboardButton("انصراف ❌", callback_data="cancel_purchase")]
    ]
    await query.message.reply_text(
        f"پلن انتخابی: {plan}\n\nآیا تایید می‌کنی که قصد خرید داری؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ------------------- تایید خرید -------------------
async def confirm_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    plan = context.user_data.get("selected_plan", "نامشخص")

    session = SessionMain()
    pr = PurchaseRequest(user_id=user_id, plan=plan, status="pending")
    session.add(pr)
    session.commit()
    pr_id = pr.id
    session.close()

    await query.message.reply_text(
        "💳 لطفاً مبلغ مربوطه را به کارت زیر واریز کرده و فیش را ارسال کنید:\n\n"
        "**6104-3310-3440-6174**\n\n"
        "بعد از ارسال فیش منتظر تایید ادمین بمانید.",
        parse_mode=ParseMode.MARKDOWN
    )

    context.user_data["purchase_id"] = pr_id

# ------------------- لغو خرید -------------------
async def cancel_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("خرید لغو شد.❌")

# ------------------- دریافت عکس فیش -------------------
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    photo = update.message.photo[-1]

    pr_id = context.user_data.get("purchase_id")
    if not pr_id:
        await update.message.reply_text("❗ فیش مربوط به خرید ثبت‌شده‌ای نیست.")
        return

    # پیام برای ادمین
    caption = f"📥 فیش پرداخت از کاربر `{user_id}`\nشناسه خرید: {pr_id}"
    keyboard = [
        [InlineKeyboardButton("تایید و ارسال کانفیگ ✅", callback_data=f"admin_approve_{user_id}_{pr_id}")]
    ]
    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo.file_id,
        caption=caption,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    # تغییر وضعیت خرید به 'paid'
    try:
        session = SessionMain()
        purchase = session.query(PurchaseRequest).filter_by(id=pr_id).first()
        if purchase:
            purchase.status = "paid"
            session.commit()
        else:
            await update.message.reply_text("⚠️ خرید مربوطه در دیتابیس پیدا نشد.")
    except Exception as e:
        print(f"[Error updating status]: {e}")
        await update.message.reply_text("🚫 خطایی در ثبت فیش پیش آمد، لطفاً بعداً دوباره امتحان کنید.")
    finally:
        session.close()

    await update.message.reply_text("فیش شما برای بررسی ادمین ارسال شد. ✅")


# ------------------- تایید ادمین -------------------
async def admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")

    if len(data) != 4:
        return

    user_id = int(data[2])
    pr_id = int(data[3])

    session = SessionMain()
    purchase = session.query(PurchaseRequest).filter_by(user_id=user_id).order_by(PurchaseRequest.id.desc()).first()
    if purchase:
        purchase.status = "approved"
        session.commit()
    session.close()

    await query.message.reply_text(
        f"✉️ لطفاً کانفیگ مربوط به کاربر `{user_id}` را با دستور زیر ارسال کنید:\n\n"
        f"/sendconfig {user_id}\n<متن کانفیگ>",
        parse_mode=ParseMode.MARKDOWN
    )

# ------------------- ارسال کانفیگ توسط ادمین -------------------
async def send_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط ادمین می‌تواند از این دستور استفاده کند.")

    args = context.args
    if len(args) < 2:
        return await update.message.reply_text("❗ فرمت درست: `/sendconfig <user_id> <config>`", parse_mode=ParseMode.MARKDOWN)

    user_id = args[0]
    config_text = " ".join(args[1:])

    try:
        await context.bot.send_message(
            chat_id=int(user_id),
            text=f"✅ خرید شما تایید شد.\n\nکانفیگ شما:\n```\n{config_text}\n```",
            parse_mode=ParseMode.MARKDOWN
        )
        await update.message.reply_text(f"📤 کانفیگ برای کاربر {user_id} ارسال شد.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در ارسال کانفیگ:\n{e}")

# ------------------- اجرای ربات -------------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_membership, pattern="^check_membership$"))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("sendconfig", send_config))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(CallbackQueryHandler(plan_selected, pattern="^plan_"))
    app.add_handler(CallbackQueryHandler(confirm_purchase, pattern="^confirm_purchase$"))
    app.add_handler(CallbackQueryHandler(cancel_purchase, pattern="^cancel_purchase$"))
    app.add_handler(CallbackQueryHandler(admin_approve, pattern="^admin_approve_"))

    print("✅ Cyvra VPN Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
