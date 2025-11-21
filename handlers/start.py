from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from keyboards.inline import main_menu_kb
from database.db_manager import DatabaseManager
from utils.default_exercises import add_default_exercises
import config

router = Router()
db = DatabaseManager(config.DB_PATH)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Команда /start"""
    # Очищаем состояние
    await state.clear()

    # Регистрируем пользователя
    await db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )

    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "🏋️ Я помогу тебе вести дневник тренировок.\n\n"
        "Что умею:\n"
        "• Записывать подходы и упражнения\n"
        "• Сохранять шаблоны тренировок\n"
        "• Показывать статистику и прогресс\n"
        "• Хранить историю всех тренировок\n\n"
        "Выбери действие:",
        reply_markup=main_menu_kb()
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help"""
    help_text = """
📖 <b>Справка по боту</b>

<b>Основные команды:</b>
/start - Главное меню
/new - Начать новую тренировку
/stats - Посмотреть статистику
/history - История тренировок
/help - Эта справка

<b>Как записывать подходы:</b>
Просто напиши вес и количество повторений в любом формате:
• <code>80x10</code> - 80кг на 10 повторений
• <code>80 10</code> - то же самое
• <code>80*10</code> или <code>80/10</code> - тоже работает

<b>Быстрые команды во время тренировки:</b>
• <code>=</code> - повторить предыдущий подход
• <code>+5</code> - добавить 5кг к предыдущему весу
• <code>-5</code> - убавить 5кг

<b>Шаблоны:</b>
Создай шаблоны своих программ тренировок, чтобы не добавлять упражнения каждый раз заново.

<b>Статистика:</b>
Смотри прогресс по каждому упражнению, отслеживай рост весов и объем нагрузки.

Если есть вопросы - просто пиши! 💪
    """
    await message.answer(help_text, parse_mode="HTML")


@router.callback_query(F.data == "menu_main")
async def show_main_menu(callback: CallbackQuery, state: FSMContext):
    """Показать главное меню"""
    await state.clear()

    await callback.message.edit_text(
        "🏋️ <b>Главное меню</b>\n\n"
        "Выбери действие:",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "none")
async def callback_none(callback: CallbackQuery):
    """Обработка нефункциональных кнопок (заголовки)"""
    await callback.answer()