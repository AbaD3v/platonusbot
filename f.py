import requests
import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Конфигурация
URL = "https://aiu.c-platonus.kz"
TELEGRAM_TOKEN = "8393077875:AAFw2GDnfN_MXSaeXYjGmReZxrYDs6-9XO4"
CHAT_ID = -4806969856   # id группы

# Глобальные переменные для отслеживания состояния
last_status = None        # True = работает, False = лежит
status_since = time.time()  # когда последний раз сменился статус

# Проверка сайта
def check_site():
    try:
        response = requests.get(URL, timeout=5)
        return True, response.status_code
    except requests.exceptions.RequestException:
        return False, None

# Текстовый отчёт
def get_status_message():
    global last_status, status_since

    is_up, code = check_site()
    now = time.time()

    # Если статус изменился – сбрасываем таймер
    if last_status is None or is_up != last_status:
        last_status = is_up
        status_since = now

    # Считаем сколько минут прошло в текущем состоянии
    minutes = int((now - status_since) / 60)

    if is_up:
        return f"✅ Сайт работает: {URL}\nКод ответа: {code}\nАптайм: {minutes} мин"
    else:
        return f"❌ Сайт недоступен: {URL}\nДаунайм: {minutes} мин"

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🔍 Проверить сайт"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    message = get_status_message()
    await update.message.reply_text(
        f"Привет! Я бот для мониторинга сайта Platonus.\n\n{message}",
        reply_markup=reply_markup
    )

# Обработка кнопки "Проверить сайт"
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔍 Проверить сайт":
        message = get_status_message()
        await update.message.reply_text(message)

# Фоновая проверка каждые 5 минут
async def periodic_check(context: ContextTypes.DEFAULT_TYPE):
    message = get_status_message()
    await context.bot.send_message(chat_id=CHAT_ID, text=message)

# Основная функция
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Фоновая задача каждые 5 минут
    job_queue = app.job_queue
    job_queue.run_repeating(periodic_check, interval=300, first=5)

    # Запуск
    app.run_polling()

if __name__ == "__main__":
    main()
