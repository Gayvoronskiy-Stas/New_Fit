from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards.inline import (
    templates_list_kb, template_actions_kb, exercises_list_kb,
    back_kb, main_menu_kb, confirm_kb
)
from database.db_manager import DatabaseManager
from states.workout_states import TemplateStates
import config

router = Router()
db = DatabaseManager(config.DB_PATH)


@router.callback_query(F.data == "templates_list")
async def show_templates(callback: CallbackQuery, state: FSMContext):
    """Показать список шаблонов"""
    await state.clear()

    user_id = callback.from_user.id
    templates = await db.get_user_templates(user_id)

    if not templates:
        await callback.message.edit_text(
            "📋 У тебя пока нет шаблонов.\n\n"
            "Шаблоны помогают быстро начинать тренировки по заранее составленной программе.\n\n"
            "Создать первый шаблон?",
            reply_markup=templates_list_kb([])
        )
    else:
        await callback.message.edit_text(
            f"📋 <b>Твои шаблоны</b> ({len(templates)})\n\n"
            "Выбери шаблон:",
            reply_markup=templates_list_kb(templates),
            parse_mode="HTML"
        )

    await callback.answer()


@router.callback_query(F.data == "template_create")
async def create_template_start(callback: CallbackQuery, state: FSMContext):
    """Начать создание шаблона"""
    await callback.message.edit_text(
        "✏️ <b>Создание шаблона</b>\n\n"
        "Введи название шаблона:\n"
        "<i>Например: День 1: Грудь+Трицепс, Full Body A, Ноги</i>",
        reply_markup=back_kb("templates_list"),
        parse_mode="HTML"
    )

    await state.set_state(TemplateStates.entering_name)
    await callback.answer()


@router.message(TemplateStates.entering_name)
async def template_enter_name(message: Message, state: FSMContext):
    """Получение названия шаблона"""
    template_name = message.text.strip()

    if len(template_name) < 2:
        await message.answer("❌ Название слишком короткое. Попробуй еще раз:")
        return

    # Сохраняем название
    await state.update_data(template_name=template_name)

    await message.answer(
        f"📝 Шаблон: <b>{template_name}</b>\n\n"
        "Теперь добавь упражнения в этот шаблон.\n"
        "Выбери первое упражнение:",
        reply_markup=back_kb("templates_list"),
        parse_mode="HTML"
    )

    # Показываем список упражнений
    exercises = await db.get_user_exercises(message.from_user.id)

    if not exercises:
        await message.answer(
            "❌ У тебя еще нет упражнений.\n\n"
            "Сначала добавь хотя бы одно упражнение!",
            reply_markup=exercises_list_kb([])
        )
        await state.clear()
        return

    await state.update_data(
        template_exercises=[],  # Список ID упражнений
        order_counter=1
    )

    await message.answer(
        "Выбери упражнения для шаблона:",
        reply_markup=exercises_list_kb(exercises, action="select")
    )

    await state.set_state(TemplateStates.adding_exercises)


@router.callback_query(TemplateStates.adding_exercises, F.data.startswith("exercise_select_"))
async def template_add_exercise(callback: CallbackQuery, state: FSMContext):
    """Добавление упражнения в шаблон"""
    exercise_id = int(callback.data.split("_")[2])

    data = await state.get_data()
    template_exercises = data.get('template_exercises', [])
    order_counter = data.get('order_counter', 1)

    # Проверяем, не добавлено ли уже
    if exercise_id in [ex['exercise_id'] for ex in template_exercises]:
        await callback.answer("⚠️ Это упражнение уже добавлено!", show_alert=True)
        return

    exercise = await db.get_exercise_by_id(exercise_id)

    # Добавляем упражнение
    template_exercises.append({
        'exercise_id': exercise_id,
        'exercise_name': exercise['name'],
        'order_number': order_counter
    })

    await state.update_data(
        template_exercises=template_exercises,
        order_counter=order_counter + 1
    )

    # Показываем текущий список
    ex_list = "\n".join([f"{i + 1}. {ex['exercise_name']}" for i, ex in enumerate(template_exercises)])

    text = (
        f"✅ <b>Упражнение добавлено!</b>\n\n"
        f"<b>Текущий список:</b>\n{ex_list}\n\n"
        "Добавить еще упражнение или завершить создание шаблона?"
    )

    # Кнопки
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = [
        [InlineKeyboardButton(text="➕ Добавить еще", callback_data="template_add_more")],
        [InlineKeyboardButton(text="✅ Сохранить шаблон", callback_data="template_save")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="templates_list")]
    ]

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(TemplateStates.adding_exercises, F.data == "template_add_more")
async def template_add_more_exercises(callback: CallbackQuery, state: FSMContext):
    """Добавить еще упражнения"""
    exercises = await db.get_user_exercises(callback.from_user.id)

    await callback.message.edit_text(
        "Выбери следующее упражнение:",
        reply_markup=exercises_list_kb(exercises, action="select")
    )
    await callback.answer()


@router.callback_query(TemplateStates.adding_exercises, F.data == "template_save")
async def template_save(callback: CallbackQuery, state: FSMContext):
    """Сохранить шаблон"""
    data = await state.get_data()
    template_name = data['template_name']
    template_exercises = data['template_exercises']

    if not template_exercises:
        await callback.answer("❌ Добавь хотя бы одно упражнение!", show_alert=True)
        return

    # Создаем шаблон
    user_id = callback.from_user.id
    template_id = await db.create_template(user_id, template_name)

    if not template_id:
        await callback.answer("❌ Шаблон с таким именем уже существует!", show_alert=True)
        return

    # Добавляем упражнения
    for ex in template_exercises:
        await db.add_exercise_to_template(
            template_id=template_id,
            exercise_id=ex['exercise_id'],
            order_number=ex['order_number']
        )

    ex_list = "\n".join([f"{i + 1}. {ex['exercise_name']}" for i, ex in enumerate(template_exercises)])

    await callback.message.edit_text(
        f"✅ <b>Шаблон создан!</b>\n\n"
        f"📋 <b>{template_name}</b>\n\n"
        f"<b>Упражнения:</b>\n{ex_list}\n\n"
        "Теперь ты можешь использовать этот шаблон для быстрого старта тренировок!",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )

    await state.clear()
    await callback.answer("✅ Шаблон сохранен!")


@router.callback_query(F.data.startswith("template_delete_"))
async def template_delete(callback: CallbackQuery):
    """Удаление шаблона"""
    template_id = int(callback.data.split("_")[2])

    await callback.message.edit_text(
        "⚠️ Точно хочешь удалить этот шаблон?\n\n"
        "Это действие нельзя отменить.",
        reply_markup=confirm_kb(f"delete_template_{template_id}")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_template_"))
async def confirm_template_delete(callback: CallbackQuery):
    """Подтверждение удаления шаблона"""
    template_id = int(callback.data.split("_")[-1])

    await db.delete_template(template_id)

    await callback.message.edit_text(
        "✅ Шаблон удален.",
        reply_markup=back_kb("templates_list")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cancel_delete_template_"))
async def cancel_template_delete(callback: CallbackQuery):
    """Отмена удаления шаблона"""
    template_id = int(callback.data.split("_")[-1])

    await callback.message.edit_text(
        "❌ Удаление отменено.",
        reply_markup=template_actions_kb(template_id)
    )
    await callback.answer()