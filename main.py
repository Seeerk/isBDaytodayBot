import logging
import os
from dotenv import load_dotenv
import datetime
import random
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import traceback
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
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
scheduler = AsyncIOScheduler()


async def start(update: Update, context: CallbackContext):
    logger.info("Получена команда /start")
    await update.message.reply_text("Привет! \n каждый день я сообщаю сегодня ли у Дениса день рождения")


async def send_test_message(update: Update, context: CallbackContext):
    logger.info("Получена команда /test")
    await update.message.reply_text("test")


async def make_daily_post():
    now = datetime.datetime.now()
    text = "Да" if now.month == 6 and now.day == 1 else "Нет"
    try:
        await application.bot.send_message(chat_id=CHANNEL_ID, text=text)
        logger.info("Ежедневный пост успешно отправлен")
        await notify_admin(
            f"Ежедневный пост, запланированный на {now.strftime('%Y-%m-%d %H:%M:%S')}, успешно отправлен.")
        # Запланировать пост на следующий день
        schedule_next_post()
    except Exception as e:
        await log_and_notify_error(e, "Ошибка при отправке ежедневного поста")


def schedule_next_post():
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
    random_hour = random.randint(0, 23)
    random_minute = random.randint(0, 59)
    scheduler.add_job(make_daily_post,
                      CronTrigger(year=tomorrow.year, month=tomorrow.month, day=tomorrow.day, hour=random_hour,
                                  minute=random_minute))
    logger.info(
        f"Запланирован ежедневный пост на {tomorrow.strftime('%Y-%m-%d')} в {random_hour:02}:{random_minute:02}")


def schedule_daily_post():
    now = datetime.datetime.now()
    random_hour = random.randint(now.hour, 23)
    random_minute = random.randint(now.minute + 1, 59) if random_hour == now.hour else random.randint(0, 59)
    scheduler.add_job(make_daily_post,
                      CronTrigger(year=now.year, month=now.month, day=now.day, hour=random_hour, minute=random_minute))
    logger.info(f"Запланирован ежедневный пост на {now.strftime('%Y-%m-%d')} в {random_hour:02}:{random_minute:02}")


def reschedule_post_to_tomorrow():
    now = datetime.datetime.now()
    today = now.strftime('%Y-%m-%d')

    # Отменяем запланированный пост на сегодня, если он существует
    for job in scheduler.get_jobs():
        if job.next_run_time.strftime('%Y-%m-%d') == today:
            scheduler.remove_job(job.id)
            logger.info("Отменен текущий запланированный пост на сегодня")
            break

    # Планируем пост на завтра
    schedule_next_post()


async def make_test_post(update: Update, context: CallbackContext):
    reschedule_post_to_tomorrow()

    now = datetime.datetime.now()
    text = "Да" if now.month == 6 and now.day == 1 else "Нет"
    try:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=text)
        logger.info("Тестовый пост успешно отправлен")
        await notify_admin(f"Тестовый пост успешно отправлен в {now.strftime('%Y-%m-%d %H:%M:%S')}.")
    except Exception as e:
        await log_and_notify_error(e, "Ошибка при отправке тестового поста")


async def test_bot(update: Update, context: CallbackContext):
    if scheduler.get_jobs():
        scheduled_date = scheduler.get_jobs()[0].next_run_time.strftime('%d.%m.%Y')
        scheduled_time = scheduler.get_jobs()[0].next_run_time.strftime('%H:%M:%S')
    else:
        scheduled_date = 'не запланирован'
        scheduled_time = 'не запланирован'
    message = f"Да, живой я, пост будет {scheduled_date}, в {scheduled_time}."
    try:
        await update.message.reply_text(message)
        logger.info("Отправлено сообщение 'Да, живой я'")
    except Exception as e:
        await log_and_notify_error(e, "Ошибка при отправке сообщения 'Да, живой я'")


async def notify_admin(message):
    admin_chat_id = os.getenv('ADMIN_CHAT_ID', CHANNEL_ID)
    try:
        await application.bot.send_message(chat_id=admin_chat_id, text=message)
        logger.info("Уведомление отправлено администратору")
    except Exception as e:
        await log_and_notify_error(e, "Ошибка при отправке уведомления администратору")


async def log_and_notify_error(exception, context):
    logger.error(f"{context}: {exception}")
    traceback_str = traceback.format_exc()  # Получаем трассировку стека в виде строки
    logger.error(f"Traceback:\n{traceback_str}")  # Записываем трассировку в лог
    await notify_admin(f"{context}: {exception}")


def main():
    try:
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("test", send_test_message))
        application.add_handler(CommandHandler("test_post", make_test_post))
        application.add_handler(CommandHandler("test_bot", test_bot))

        schedule_daily_post()
        scheduler.start()

        application.run_polling()
        logger.info("Бот начал работу")

    except Exception as e:
        logger.critical(f"Бот остановлен из-за необработанного исключения: {e}")
        asyncio.run(log_and_notify_error(e, "Бот остановлен из-за необработанного исключения"))

    finally:
        try:
            asyncio.run(application.shutdown())
            logger.info("Бот завершил работу")
        except Exception as e:
            asyncio.run(log_and_notify_error(e, "Ошибка при завершении работы бота"))


if __name__ == "__main__":
    main()
