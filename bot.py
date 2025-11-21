import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import config
from database.db_manager import DatabaseManager

# Импортируем роутеры
from handlers import start, exercises, workout, templates, stats

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""

    # Проверяем наличие токена
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN не найден! Создай файл .env с токеном бота.")
        return

    # Инициализируем бота
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Инициализируем диспетчер
    dp = Dispatcher()

    # Инициализируем базу данных
    db = DatabaseManager(config.DB_PATH)
    await db.init_db()
    logger.info("База данных инициализирована")

    # Регистрируем роутеры
    dp.include_router(start.router)
    dp.include_router(exercises.router)
    dp.include_router(workout.router)

    logger.info("Бот запущен!")

    try:
        # Запускаем polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")