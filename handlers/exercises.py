from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards.inline import exercises_list_kb, exercise_categories_kb, back_kb, main_menu_kb
from database.db_manager import DatabaseManager
from states.workout_states import ExerciseStates
import config

router = Router()
db = DatabaseManager(config.DB_PATH)


@router.callback_query(F.data == "exercises_list")
async def show_exercises_list(callback: CallbackQuery, state: FSMContext):
    """Показать список упражнений"""
    await state.clear()

    user_id = callback.from_user.id
    exercises = await db.get_user_exercises(user_id)

    if not exercises:
        await callback.message.edit_text(
            "📝 У тебя пока нет упражнений.\n\n"
            "Давай добавим первое! Нажми кнопку ниже:",
            reply_markup=exercises_list_kb([])
        )
    else:
        await callback.message.edit_text(
            f"💪 <b>Твои упражнения</b> ({len(exercises)})\n\n"
            "Выбери упражнение для просмотра или добавь новое:",
            reply_markup=exercises_list_kb(exercises, action="view"),
            parse_mode="HTML"
        )

    await callback.answer()


@router.callback_query(F.data == "exercise_add")
async def add_exercise_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления упражнения"""
    await callback.message.edit_text(
        "✏️ <b>Добавление упражнения</b>\n\n"
        "Введи название упражнения:\n"
        "<i>Например: Жим лежа, Приседания, Тяга штанги</i>",
        reply_markup=back_kb("exercises_list"),
        parse_mode="HTML"
    )

    await state.set_state(ExerciseStates.entering_name)
    await callback.answer()


@router.message(ExerciseStates.entering_name)
async def add_exercise_name(message: Message, state: FSMContext):
    """Получение названия упражнения"""
    exercise_name = message.text.strip()

    if len(exercise_name) < 2:
        await message.answer(
            "❌ Название слишком короткое. Попробуй еще раз:"
        )
        return

    # Сохраняем название
    await state.update_data(exercise_name=exercise_name)

    await message.answer(
        f"📝 Упражнение: <b>{exercise_name}</b>\n\n"
        "Теперь выбери категорию:",
        reply_markup=exercise_categories_kb(),
        parse_mode="HTML"
    )

    await state.set_state(ExerciseStates.selecting_category)


@router.callback_query(ExerciseStates.selecting_category, F.data.startswith("category_"))
async def add_exercise_category(callback: CallbackQuery, state: FSMContext):
    """Получение категории упражнения"""
    category = callback.data.split("_", 1)[1]

    # Получаем данные из состояния
    data = await state.get_data()
    exercise_name = data['exercise_name']

    # Добавляем упражнение в БД
    user_id = callback.from_user.id
    exercise_id = await db.add_exercise(
        user_id=user_id,
        name=exercise_name,
        category=category,
        exercise_type="custom"
    )

    if exercise_id:
        await callback.message.edit_text(
            f"✅ Упражнение добавлено!\n\n"
            f"📝 <b>{exercise_name}</b>\n"
            f"📂 Категория: {category}\n\n"
            "Теперь ты можешь использовать его в тренировках.",
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            f"❌ Упражнение <b>{exercise_name}</b> уже существует.\n\n"
            "Выбери другое название:",
            reply_markup=back_kb("exercises_list"),
            parse_mode="HTML"
        )
        await state.set_state(ExerciseStates.entering_name)
        await callback.answer()
        return

    await state.clear()
    await callback.answer("✅ Упражнение добавлено!")


@router.callback_query(F.data.startswith("exercise_view_"))
async def view_exercise(callback: CallbackQuery):
    """Просмотр информации об упражнении"""
    exercise_id = int(callback.data.split("_")[2])

    exercise = await db.get_exercise_by_id(exercise_id)

    if not exercise:
        await callback.answer("❌ Упражнение не найдено", show_alert=True)
        return

    # Получаем историю упражнения
    history = await db.get_exercise_history(
        user_id=callback.from_user.id,
        exercise_id=exercise_id,
        limit=5
    )

    text = f"💪 <b>{exercise['name']}</b>\n"
    text += f"📂 Категория: {exercise['category'] or 'Не указана'}\n\n"

    if history:
        text += "<b>Последние подходы:</b>\n"
        for h in history[:5]:
            weight_str = f"{h['weight']:.1f}".rstrip('0').rstrip('.')
            text += f"• {weight_str}кг × {h['reps']} повт.\n"
    else:
        text += "<i>Еще не было записей</i>"

    await callback.message.edit_text(
        text,
        reply_markup=back_kb("exercises_list"),
        parse_mode="HTML"
    )
    await callback.answer()