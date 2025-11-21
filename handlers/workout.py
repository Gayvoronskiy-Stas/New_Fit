from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime

from keyboards.inline import (
    workout_start_kb, templates_list_kb, exercises_list_kb,
    active_workout_kb, set_repeat_kb, confirm_kb, main_menu_kb
)
from database.db_manager import DatabaseManager
from states.workout_states import WorkoutStates
from utils.parsers import parse_set_input, parse_weight_modifier, format_set_display, format_workout_summary
import config

router = Router()
db = DatabaseManager(config.DB_PATH)


@router.message(Command("new"))
@router.callback_query(F.data == "workout_new")
async def workout_new(event, state: FSMContext):
    """Начать новую тренировку"""
    await state.clear()

    user_id = event.from_user.id

    # Проверяем есть ли активная тренировка
    active_workout = await db.get_active_workout(user_id)
    if active_workout:
        text = (
            "⚠️ У тебя уже есть активная тренировка!\n\n"
            f"Начата: {active_workout['start_time']}\n\n"
            "Что делаем?"
        )
        keyboard = [
            [{"text": "▶️ Продолжить", "callback_data": "workout_continue"}],
            [{"text": "🗑 Отменить старую и начать новую", "callback_data": "workout_cancel_and_new"}],
        ]

        if isinstance(event, Message):
            await event.answer(text, reply_markup=confirm_kb("workout"))
        else:
            await event.message.edit_text(text, reply_markup=confirm_kb("workout"))
            await event.answer()
        return

    # Проверяем есть ли шаблоны
    templates = await db.get_user_templates(user_id)
    has_templates = len(templates) > 0

    text = (
        "🏋️ <b>Новая тренировка</b>\n\n"
        "Как хочешь начать?"
    )

    if isinstance(event, Message):
        await event.answer(text, reply_markup=workout_start_kb(has_templates), parse_mode="HTML")
    else:
        await event.message.edit_text(text, reply_markup=workout_start_kb(has_templates), parse_mode="HTML")
        await event.answer()


@router.callback_query(F.data == "workout_quick")
async def workout_quick_start(callback: CallbackQuery, state: FSMContext):
    """Быстрая тренировка без шаблона"""
    user_id = callback.from_user.id

    # Создаем тренировку
    workout_id = await db.create_workout(user_id, "Быстрая тренировка")

    # Сохраняем в состояние
    await state.update_data(
        workout_id=workout_id,
        template_id=None,
        current_exercise_id=None,
        template_exercises=[],
        current_ex_index=0
    )

    # Показываем список упражнений
    exercises = await db.get_user_exercises(user_id)

    if not exercises:
        await callback.message.edit_text(
            "❌ У тебя еще нет упражнений.\n\n"
            "Давай сначала добавим хотя бы одно!",
            reply_markup=exercises_list_kb([])
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "💪 <b>Быстрая тренировка</b>\n\n"
        "Выбери первое упражнение:",
        reply_markup=exercises_list_kb(exercises, action="select"),
        parse_mode="HTML"
    )

    await state.set_state(WorkoutStates.selecting_exercise)
    await callback.answer("✅ Тренировка начата!")


@router.callback_query(F.data == "workout_from_template")
async def workout_from_template(callback: CallbackQuery, state: FSMContext):
    """Выбор шаблона для тренировки"""
    user_id = callback.from_user.id
    templates = await db.get_user_templates(user_id)

    if not templates:
        await callback.message.edit_text(
            "❌ У тебя пока нет шаблонов.\n\n"
            "Создай первый шаблон или начни быструю тренировку!",
            reply_markup=workout_start_kb(False)
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "📋 <b>Выбери шаблон тренировки:</b>",
        reply_markup=templates_list_kb(templates),
        parse_mode="HTML"
    )

    await state.set_state(WorkoutStates.selecting_template)
    await callback.answer()


@router.callback_query(WorkoutStates.selecting_template, F.data.startswith("template_select_"))
async def start_workout_from_template(callback: CallbackQuery, state: FSMContext):
    """Начать тренировку по шаблону"""
    template_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id

    # Получаем упражнения шаблона
    template_exercises = await db.get_template_exercises(template_id)

    if not template_exercises:
        await callback.answer("❌ В шаблоне нет упражнений!", show_alert=True)
        return

    # Создаем тренировку
    workout_id = await db.create_workout(user_id)

    # Первое упражнение
    first_ex = template_exercises[0]

    await state.update_data(
        workout_id=workout_id,
        template_id=template_id,
        current_exercise_id=first_ex['exercise_id'],
        template_exercises=template_exercises,
        current_ex_index=0
    )

    # Показываем первое упражнение
    text = (
        f"💪 <b>{first_ex['exercise_name']}</b>\n"
        f"📂 {first_ex['category']}\n\n"
    )

    if first_ex['target_sets']:
        text += f"🎯 Цель: {first_ex['target_sets']} подходов"
        if first_ex['target_reps']:
            text += f" × {first_ex['target_reps']} повт."
        text += "\n\n"

    text += "Введи данные подхода в формате: <code>вес×повторения</code>\n"
    text += "Например: <code>80×10</code> или <code>80 10</code>"

    await callback.message.edit_text(
        text,
        reply_markup=active_workout_kb(first_ex['exercise_id'], has_more_exercises=len(template_exercises) > 1),
        parse_mode="HTML"
    )

    await state.set_state(WorkoutStates.active_workout)
    await callback.answer("✅ Поехали!")


@router.callback_query(WorkoutStates.selecting_exercise, F.data.startswith("exercise_select_"))
async def select_exercise_for_workout(callback: CallbackQuery, state: FSMContext):
    """Выбор упражнения для тренировки"""
    exercise_id = int(callback.data.split("_")[2])

    exercise = await db.get_exercise_by_id(exercise_id)

    # Обновляем состояние
    await state.update_data(current_exercise_id=exercise_id)

    text = (
        f"💪 <b>{exercise['name']}</b>\n"
        f"📂 {exercise['category']}\n\n"
        "Введи данные подхода в формате: <code>вес×повторения</code>\n"
        "Например: <code>80×10</code> или <code>80 10</code>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=active_workout_kb(exercise_id),
        parse_mode="HTML"
    )

    await state.set_state(WorkoutStates.active_workout)
    await callback.answer()


@router.message(WorkoutStates.active_workout)
async def process_set_input(message: Message, state: FSMContext):
    """Обработка ввода данных подхода"""
    user_input = message.text.strip()
    data = await state.get_data()

    workout_id = data['workout_id']
    exercise_id = data['current_exercise_id']

    # Получаем последний подход этого упражнения
    last_set = await db.get_last_set(workout_id, exercise_id)
    set_number = (last_set['set_number'] + 1) if last_set else 1

    weight = None
    reps = None

    # Проверяем специальные команды
    if user_input == '=' and last_set:
        # Повторить предыдущий подход
        weight = last_set['weight']
        reps = last_set['reps']
    elif user_input.startswith(('+', '-')) and last_set:
        # Модификатор веса
        modifier = parse_weight_modifier(user_input)
        if modifier:
            weight = last_set['weight'] + modifier
            reps = last_set['reps']
    else:
        # Обычный ввод
        parsed = parse_set_input(user_input)
        if parsed:
            weight, reps = parsed

    if weight is None or reps is None:
        await message.answer(
            "❌ Не могу распознать формат.\n\n"
            "Попробуй так:\n"
            "• <code>80×10</code>\n"
            "• <code>80 10</code>\n"
            "• <code>=</code> (повторить предыдущий)\n"
            "• <code>+5</code> (добавить 5кг к предыдущему)",
            parse_mode="HTML"
        )
        return

    # Сохраняем подход
    await db.add_set(
        workout_id=workout_id,
        exercise_id=exercise_id,
        set_number=set_number,
        weight=weight,
        reps=reps
    )

    # Получаем упражнение
    exercise = await db.get_exercise_by_id(exercise_id)

    # Формируем ответ
    text = (
        f"✅ Записано!\n\n"
        f"💪 <b>{exercise['name']}</b>\n"
        f"{format_set_display(weight, reps, set_number)}\n\n"
        "Что дальше?"
    )

    # Проверяем есть ли еще упражнения в шаблоне
    template_exercises = data.get('template_exercises', [])
    current_index = data.get('current_ex_index', 0)
    has_more = current_index < len(template_exercises) - 1

    await message.answer(
        text,
        reply_markup=set_repeat_kb(weight, reps) if last_set else active_workout_kb(exercise_id, has_more),
        parse_mode="HTML"
    )


    @router.callback_query(F.data == "set_same")
    async def repeat_same_set(callback: CallbackQuery, state: FSMContext):
        """Повторить предыдущий подход"""
        data = await state.get_data()
        workout_id = data['workout_id']
        exercise_id = data['current_exercise_id']

        last_set = await db.get_last_set(workout_id, exercise_id)

        if not last_set:
            await callback.answer("❌ Нет предыдущего подхода", show_alert=True)
            return

        # Сохраняем новый подход с теми же параметрами
        set_number = last_set['set_number'] + 1
        await db.add_set(
            workout_id=workout_id,
            exercise_id=exercise_id,
            set_number=set_number,
            weight=last_set['weight'],
            reps=last_set['reps']
        )

        exercise = await db.get_exercise_by_id(exercise_id)

        text = (
            f"✅ Записано!\n\n"
            f"💪 <b>{exercise['name']}</b>\n"
            f"{format_set_display(last_set['weight'], last_set['reps'], set_number)}\n\n"
            "Что дальше?"
        )

        template_exercises = data.get('template_exercises', [])
        current_index = data.get('current_ex_index', 0)
        has_more = current_index < len(template_exercises) - 1

        await callback.message.edit_text(
            text,
            reply_markup=set_repeat_kb(last_set['weight'], last_set['reps']),
            parse_mode="HTML"
        )
        await callback.answer("✅ Подход записан!")

    @router.callback_query(F.data.startswith("set_add_weight"))
    async def add_weight_to_set(callback: CallbackQuery, state: FSMContext):
        """Добавить 2.5кг к предыдущему весу"""
        data = await state.get_data()
        workout_id = data['workout_id']
        exercise_id = data['current_exercise_id']

        last_set = await db.get_last_set(workout_id, exercise_id)

        if not last_set:
            await callback.answer("❌ Нет предыдущего подхода", show_alert=True)
            return

        new_weight = last_set['weight'] + 2.5
        set_number = last_set['set_number'] + 1

        await db.add_set(
            workout_id=workout_id,
            exercise_id=exercise_id,
            set_number=set_number,
            weight=new_weight,
            reps=last_set['reps']
        )

        exercise = await db.get_exercise_by_id(exercise_id)

        text = (
            f"✅ Записано! (+2.5кг)\n\n"
            f"💪 <b>{exercise['name']}</b>\n"
            f"{format_set_display(new_weight, last_set['reps'], set_number)}\n\n"
            "Что дальше?"
        )

        await callback.message.edit_text(
            text,
            reply_markup=set_repeat_kb(new_weight, last_set['reps']),
            parse_mode="HTML"
        )
        await callback.answer("✅ Подход записан!")

    @router.callback_query(F.data.startswith("set_sub_weight"))
    async def subtract_weight_from_set(callback: CallbackQuery, state: FSMContext):
        """Убавить 2.5кг от предыдущего веса"""
        data = await state.get_data()
        workout_id = data['workout_id']
        exercise_id = data['current_exercise_id']

        last_set = await db.get_last_set(workout_id, exercise_id)

        if not last_set:
            await callback.answer("❌ Нет предыдущего подхода", show_alert=True)
            return

        new_weight = max(0, last_set['weight'] - 2.5)
        set_number = last_set['set_number'] + 1

        await db.add_set(
            workout_id=workout_id,
            exercise_id=exercise_id,
            set_number=set_number,
            weight=new_weight,
            reps=last_set['reps']
        )

        exercise = await db.get_exercise_by_id(exercise_id)

        text = (
            f"✅ Записано! (-2.5кг)\n\n"
            f"💪 <b>{exercise['name']}</b>\n"
            f"{format_set_display(new_weight, last_set['reps'], set_number)}\n\n"
            "Что дальше?"
        )

        await callback.message.edit_text(
            text,
            reply_markup=set_repeat_kb(new_weight, last_set['reps']),
            parse_mode="HTML"
        )
        await callback.answer("✅ Подход записан!")

    @router.callback_query(F.data == "exercise_next")
    async def next_exercise(callback: CallbackQuery, state: FSMContext):
        """Переход к следующему упражнению в шаблоне"""
        data = await state.get_data()
        template_exercises = data.get('template_exercises', [])
        current_index = data.get('current_ex_index', 0)

        if current_index >= len(template_exercises) - 1:
            await callback.answer("❌ Это последнее упражнение", show_alert=True)
            return

        # Следующее упражнение
        next_index = current_index + 1
        next_ex = template_exercises[next_index]

        await state.update_data(
            current_exercise_id=next_ex['exercise_id'],
            current_ex_index=next_index
        )

        text = (
            f"💪 <b>{next_ex['exercise_name']}</b>\n"
            f"📂 {next_ex['category']}\n\n"
        )

        if next_ex['target_sets']:
            text += f"🎯 Цель: {next_ex['target_sets']} подходов"
            if next_ex['target_reps']:
                text += f" × {next_ex['target_reps']} повт."
            text += "\n\n"

        text += "Введи данные подхода в формате: <code>вес×повторения</code>"

        has_more = next_index < len(template_exercises) - 1

        await callback.message.edit_text(
            text,
            reply_markup=active_workout_kb(next_ex['exercise_id'], has_more),
            parse_mode="HTML"
        )
        await callback.answer()

    @router.callback_query(F.data == "exercise_add_to_workout")
    async def add_exercise_to_active_workout(callback: CallbackQuery, state: FSMContext):
        """Добавить упражнение в активную тренировку"""
        exercises = await db.get_user_exercises(callback.from_user.id)

        if not exercises:
            await callback.answer("❌ Нет доступных упражнений", show_alert=True)
            return

        await callback.message.edit_text(
            "💪 <b>Выбери упражнение:</b>",
            reply_markup=exercises_list_kb(exercises, action="select"),
            parse_mode="HTML"
        )

        await state.set_state(WorkoutStates.selecting_exercise)
        await callback.answer()

    @router.callback_query(F.data == "workout_finish")
    async def finish_workout(callback: CallbackQuery, state: FSMContext):
        """Завершить тренировку"""
        data = await state.get_data()
        workout_id = data.get('workout_id')

        if not workout_id:
            await callback.answer("❌ Нет активной тренировки", show_alert=True)
            return

        # Получаем все подходы тренировки
        sets = await db.get_workout_sets(workout_id)

        if not sets:
            await callback.message.edit_text(
                "⚠️ Ты не записал ни одного подхода.\n\n"
                "Точно хочешь завершить тренировку?",
                reply_markup=confirm_kb("finish_empty")
            )
            await callback.answer()
            return

        # Завершаем тренировку
        await db.finish_workout(workout_id)

        # Формируем сводку
        summary = format_workout_summary(sets)
        total_sets = len(sets)

        # Группируем по упражнениям для подсчета
        exercises_count = len(set([s['exercise_name'] for s in sets]))

        text = (
            f"✅ <b>Тренировка завершена!</b>\n\n"
            f"📊 Статистика:\n"
            f"• Упражнений: {exercises_count}\n"
            f"• Подходов: {total_sets}\n\n"
            f"<b>Выполнено:</b>{summary}\n\n"
            f"🔥 Отличная работа!"
        )

        await callback.message.edit_text(
            text,
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )

        await state.clear()
        await callback.answer("💪 Отличная тренировка!")

    @router.callback_query(F.data == "confirm_finish_empty")
    async def confirm_finish_empty_workout(callback: CallbackQuery, state: FSMContext):
        """Подтверждение завершения пустой тренировки"""
        data = await state.get_data()
        workout_id = data.get('workout_id')

        await db.finish_workout(workout_id)

        await callback.message.edit_text(
            "✅ Тренировка завершена.\n\n"
            "В следующий раз будет лучше! 💪",
            reply_markup=main_menu_kb()
        )

        await state.clear()
        await callback.answer()

    @router.callback_query(F.data == "workout_cancel")
    async def cancel_workout(callback: CallbackQuery, state: FSMContext):
        """Отменить тренировку"""
        await callback.message.edit_text(
            "⚠️ Точно хочешь отменить тренировку?\n\n"
            "Все данные будут удалены.",
            reply_markup=confirm_kb("cancel_workout")
        )
        await callback.answer()

    @router.callback_query(F.data == "confirm_cancel_workout")
    async def confirm_cancel_workout(callback: CallbackQuery, state: FSMContext):
        """Подтверждение отмены тренировки"""
        data = await state.get_data()
        workout_id = data.get('workout_id')

        if workout_id:
            # Удаляем тренировку (можно оставить в БД, но пометить как отмененную)
            # Пока просто очищаем состояние
            pass

        await callback.message.edit_text(
            "❌ Тренировка отменена.",
            reply_markup=main_menu_kb()
        )

        await state.clear()
        await callback.answer()

    @router.callback_query(F.data == "cancel_cancel_workout")
    async def cancel_cancel_workout(callback: CallbackQuery):
        """Отмена отмены тренировки (вернуться к тренировке)"""
        await callback.message.edit_text(
            "✅ Продолжаем тренировку!\n\n"
            "Введи данные следующего подхода:"
        )
        await callback.answer()

    @router.callback_query(F.data == "workout_menu")
    async def show_workout_menu(callback: CallbackQuery, state: FSMContext):
        """Показать меню тренировки"""
        data = await state.get_data()
        exercise_id = data.get('current_exercise_id')
        template_exercises = data.get('template_exercises', [])
        current_index = data.get('current_ex_index', 0)

        has_more = current_index < len(template_exercises) - 1

        await callback.message.edit_text(
            "🏋️ <b>Меню тренировки</b>\n\n"
            "Выбери действие:",
            reply_markup=active_workout_kb(exercise_id, has_more),
            parse_mode="HTML"
        )
        await callback.answer()