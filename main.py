import csv
import os
import datetime
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

DAYS = ['السبت', 'الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس']
TIMES = ['10:00', '11:00', '12:00', '16:00', '17:00', '18:00']
CSV_FILE = "bookings.csv"

# إنشاء ملف CSV إن لم يكن موجودًا
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["الاسم", "اليوم", "الوقت", "التاريخ"])

# حفظ وترتيب الحجوزات
def save_and_sort_booking(name, day, time, date):
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([name, day, time, date])

    with open(CSV_FILE, mode='r', encoding='utf-8') as file:
        reader = list(csv.reader(file))
        header, rows = reader[0], reader[1:]

    def sort_key(row):
        try:
            return datetime.datetime.strptime(f"{row[3]} {row[2]}", "%Y-%m-%d %H:%M")
        except:
            return datetime.datetime.max

    rows.sort(key=sort_key)
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(rows)

# بدء المحادثة
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(day, callback_data=day)] for day in DAYS]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 مرحباً بك في بوت الحجز عند الحلاق.\nاختر اليوم المناسب:", reply_markup=reply_markup)

# عند اختيار اليوم
async def day_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['day'] = query.data
    keyboard = [[InlineKeyboardButton(t, callback_data=f"time_{t}")] for t in TIMES]
    await query.edit_message_text(f"اختر الوقت المناسب ليوم {query.data}:", reply_markup=InlineKeyboardMarkup(keyboard))

# عند اختيار الوقت
async def time_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if 'day' not in context.user_data:
        await query.edit_message_text("⚠️ يرجى اختيار اليوم أولاً قبل تحديد الوقت.")
        return

    time = query.data.replace("time_", "")
    day = context.user_data['day']
    name = query.from_user.first_name

    today = datetime.date.today()
    weekday_index = DAYS.index(day)
    today_index = today.weekday()
    weekday_map = {5: 0, 6: 1, 0: 2, 1: 3, 2: 4, 3: 5}
    current_index = weekday_map.get(today_index, 0)
    days_ahead = (DAYS.index(day) - current_index + 7) % 7
    booking_date = today + datetime.timedelta(days=days_ahead)

    save_and_sort_booking(name, day, time, str(booking_date))
    await query.edit_message_text(f"✅ تم حجز موعدك يوم {day} الساعة {time}.\nنراك قريباً 💈")

# تشغيل البوت
if __name__ == '__main__':
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("❌ لم يتم العثور على BOT_TOKEN، تأكد من إضافته في إعدادات Render")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(time_chosen, pattern="^time_"))
    app.add_handler(CallbackQueryHandler(day_chosen))
    app.run_polling()
