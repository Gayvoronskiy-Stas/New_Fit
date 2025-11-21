import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота из .env файла
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Путь к базе данных
DB_PATH = 'workout_bot.db'

# Настройки
TIMEZONE = 'Europe/Moscow'