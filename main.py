import os
import logging
import random
import datetime
import schedule
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from dotenv import load_dotenv
import asyncio

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузите переменные окружения из .env файла
load_dotenv()

# Получите токен вашего бота и ID чата из переменных окружения
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = os.getenv('TELEGRAM_CHAT_ID')

# Создайте объект приложения
application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: CallbackContext):
    """Отправляет сообщение 'Привет!' при вызове команды /start"""
    await update.message.reply_text("Привет!")

async def send_test_message(update: Update, context: CallbackContext):
    """Отправляет сообщение 'test' при вызове команды /test"""
    await update.message.reply_text("test")

async def daily_post():
    """Отправляет сообщение каждый день в случайное время"""
    now = datetime.datetime.now()
    text = "Да" if now.month == 6 and now.day == 1 else "Нет"
    await application.bot.send_message(chat_id=CHANNEL_ID, text=text)

def schedule_daily_post():
    """Планирует ежедневный пост"""
    schedule.every().day.at("10:00").do(asyncio.run, daily_post())

async def test_post(update: Update, context: CallbackContext):
    """Публикует запись в канал (тестовая запись) и отменяет запланированный ежедневный пост на 1 день"""
    now = datetime.datetime.now()
    text = "Да" if now.month == 6 and now.day == 1 else "Нет"
    await context.bot.send_message(chat_id=CHANNEL_ID, text=text)
    schedule.clear("daily_post")  # Отменяем запланированный пост только на один день

def main():
    # Добавление обработчика команды /start
    application.add_handler(CommandHandler("start", start))

    # Добавление обработчика команды /test
    application.add_handler(CommandHandler("test", test_post))

    # Планирование ежедневного поста
    schedule_daily_post()

    # Запускаем бота
    application.run_polling()
    logger.info("Bot started polling")

if __name__ == "__main__":
    main()
