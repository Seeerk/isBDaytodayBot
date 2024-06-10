import os
import random
import schedule
import time
import logging
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузите переменные окружения из .env файла
load_dotenv()

# Получите токен вашего бота из переменных окружения
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

bot = Bot(token=TOKEN)


def send_message(text):
    try:
        bot.send_message(chat_id=CHAT_ID, text=text)
        logger.info(f"Sent message: {text}")
    except Exception as e:
        logger.error(f"Error sending message: {e}")


def schedule_daily_message():
    # Определяем случайное время для сообщения
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    schedule_time = f"{hour:02d}:{minute:02d}"

    # Определяем сообщение
    message = "Да" if datetime.now().month == 6 and datetime.now().day == 1 else "Нет"

    # Планируем отправку сообщения
    schedule.every().day.at(schedule_time).do(send_message, text=message)

    logger.info(f"Scheduled message '{message}' at {schedule_time}")


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


def send_test_message(update: Update, context: CallbackContext):
    test_message = "Это тестовое сообщение"
    update.message.reply_text(test_message)
    logger.info("Sent test message")


def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет!")


def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    # Добавление обработчика команды /start
    dp.add_handler(CommandHandler("start", start))

    # Добавление кнопки "Тест"
    dp.add_handler(CommandHandler("test", send_test_message))

    updater.start_polling()
    logger.info("Bot started polling")

    updater.idle()


if __name__ == "__main__":
    logger.info("Bot started")
    schedule_daily_message()
    run_scheduler()
