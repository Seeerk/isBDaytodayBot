import os
import logging
import datetime
import traceback  # Импортируем модуль traceback для работы с трассировкой стека
import schedule
import random
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

# Добавляем обработчик для записи логов в файл
log_file = 'bot.log'
file_handler = logging.FileHandler(log_file, mode='a')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

load_dotenv()

# Определяем текущее окружение
ENV = os.getenv('ENV', 'production')

if ENV == 'production':
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    CHANNEL_ID = os.getenv('TELEGRAM_CHAT_ID')
else:
    TOKEN = os.getenv('TEST_TELEGRAM_BOT_TOKEN')
    CHANNEL_ID = os.getenv('TEST_TELEGRAM_CHAT_ID')

application = Application.builder().token(TOKEN).build()


async def start(update: Update, context: CallbackContext):
    """Отправляет сообщение 'Привет!' при получении команды /start"""
    logger.info("Получена команда /start")
    await update.message.reply_text("Привет!")


async def send_test_message(update: Update, context: CallbackContext):
    """Отправляет сообщение 'test' при получении команды /test"""
    logger.info("Получена команда /test")
    await update.message.reply_text("test")


async def daily_post():
    """Отправляет ежедневный пост"""
    now = datetime.datetime.now()
    text = "Да" if now.month == 6 and now.day == 1 else "Нет"
    try:
        await application.bot.send_message(chat_id=CHANNEL_ID, text=text)
        logger.info("Ежедневный пост успешно отправлен")
        await notify_admin(
            f"Ежедневный пост, запланированный на {now.strftime('%Y-%m-%d %H:%M:%S')}, успешно отправлен.")
    except Exception as e:
        logger.error(f"Ошибка при отправке ежедневного поста: {e}")
        traceback_str = traceback.format_exc()  # Получаем трассировку стека в виде строки
        logger.error(f"Traceback:\n{traceback_str}")  # Записываем трассировку в лог
        await notify_admin(
            f"Ошибка при отправке ежедневного поста, запланированного на {now.strftime('%Y-%m-%d %H:%M:%S')}: {e}")


def schedule_daily_post():
    """Запланировать ежедневный пост"""
    now = datetime.datetime.now()
    tomorrow = now + datetime.timedelta(days=1)
    random_hour = random.randint(0, 23)
    random_minute = random.randint(0, 59)
    schedule_time = f"{random_hour:02}:{random_minute:02}"
    logger.info(f"Запланирован ежедневный пост на {tomorrow.strftime('%Y-%m-%d')} в {schedule_time}")
    schedule.every().day.at(schedule_time).do(asyncio.run, daily_post)


async def test_post(update: Update, context: CallbackContext):
    """Немедленно отправляет тестовый пост и отменяет текущий запланированный пост на сегодня, если он есть"""
    now = datetime.datetime.now()
    today = now.strftime('%Y-%m-%d')

    # Отменяем текущий запланированный пост на сегодня, если он не был опубликован
    for job in schedule.jobs:
        if job.next_run.date().strftime('%Y-%m-%d') == today:
            schedule.cancel_job(job)
            logger.info("Отменен текущий запланированный пост на сегодня")
            break

    # Запланировываем новый пост на завтра
    schedule_daily_post()

    text = "Да" if now.month == 6 and now.day == 1 else "Нет"
    try:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=text)
        logger.info("Тестовый пост успешно отправлен")
        await notify_admin(f"Тестовый пост успешно отправлен в {now.strftime('%Y-%m-%d %H:%M:%S')}.")
    except Exception as e:
        logger.error(f"Ошибка при отправке тестового поста: {e}")
        traceback_str = traceback.format_exc()  # Получаем трассировку стека в виде строки
        logger.error(f"Traceback:\n{traceback_str}")  # Записываем трассировку в лог
        await notify_admin(f"Ошибка при отправке тестового поста в {now.strftime('%Y-%m-%d %H:%M:%S')}: {e}")


async def test_bot(update: Update, context: CallbackContext):
    """Немедленно отправляет сообщение 'Да, живой я, пост будет <День>, в <Время>'"""
    scheduled_date = schedule.jobs[0].next_run.strftime('%d.%m.%Y') if schedule.jobs else 'не запланирован'
    scheduled_time = schedule.jobs[0].next_run.strftime('%H:%M:%S') if schedule.jobs else 'не запланирован'
    message = f"Да, живой я, пост будет {scheduled_date}, в {scheduled_time}."
    try:
        await update.message.reply_text(message)
        logger.info("Отправлено сообщение 'Да, живой я'")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения 'Да, живой я': {e}")
        traceback_str = traceback.format_exc()  # Получаем трассировку стека в виде строки
        logger.error(f"Traceback:\n{traceback_str}")  # Записываем трассировку в лог


async def notify_admin(message):
    """Отправить уведомление администратору"""
    admin_chat_id = os.getenv('ADMIN_CHAT_ID', CHANNEL_ID)  # Можно указать отдельный чат ID для администратора
    try:
        await application.bot.send_message(chat_id=admin_chat_id, text=message)
        logger.info("Уведомление отправлено администратору")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления администратору: {e}")
        traceback_str = traceback.format_exc()  # Получаем трассировку стека в виде строки
        logger.error(f"Traceback:\n{traceback_str}")  # Записываем трассировку в лог


def main():
    try:
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("test", send_test_message))
        application.add_handler(CommandHandler("test_post", test_post))
        application.add_handler(CommandHandler("test_bot", test_bot))

        schedule_daily_post()

        application.run_polling()
        logger.info("Бот начал работу")

    except Exception as e:
        logger.critical(f"Бот остановлен из-за необработанного исключения: {e}")
        traceback_str = traceback.format_exc()  # Получаем трассировку стека в виде строки
        logger.error(f"Traceback:\n{traceback_str}")  # Записываем трассировку в лог
        asyncio.run(notify_admin(f"Бот остановлен из-за необработанного исключения: {e}"))

    finally:
        try:
            asyncio.run(application.shutdown())
            logger.info("Бот завершил работу")
        except Exception as e:
            logger.error(f"Ошибка при завершении работы бота: {e}")
            traceback_str = traceback.format_exc()  # Получаем трассировку стека в виде строки
            logger.error(f"Traceback:\n{traceback_str}")  # Записываем трассировку в лог


if __name__ == "__main__":
    main()
