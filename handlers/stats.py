from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from datetime import datetime

from keyboards.inline import back_kb, main_menu_kb, exercises_list_kb
from database.db_manager import DatabaseManager
from utils.parsers import calculate_volume, format_workout_summary
import config

router = Router()
db = DatabaseManager(config.DB_PATH)


@router.message(Command("stats"))
@router.callback_query(F.data == "stats_show")
async def show_stats(event, state=None):
    """Показать общую статистику"""
    if state:
        await state.clear()

    user_id = event.from_user.id

    # Получаем последние тренировки
    workouts = await db.get_user_workouts(user_id, limit=100)

    if not workouts:
        text = (
            "📊 <b>Статистика</b>\n\n"
            "У тебя пока нет завершенных тренировок.\n\n"
            "Начни первую тренировку, чтобы увидеть статистику!"
        )

        if isinstance(event, Message):
            await event.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")
        else:
            await event.message.edit_text(text, reply_markup=main_menu_kb(), parse_mode="HTML")
            await event.answer()
        return

    # Считаем статистику
    total_workouts = len([w for w in workouts if w['end_time']])

    # Получаем все подходы
    all_sets = []
    for workout in workouts:
        if workout['end_time']:
            sets = await db.get_workout_sets(workout['id'])
            all_sets.extend(sets)

    total_sets = len(all_sets)
    total_volume = calculate_volume(all_sets)

    # Уникальные упражнения
    unique_exercises = len(set([s['exercise_name'] for s in all_sets]))

    # Последняя тренировка
    last_workout = workouts[0] if workouts else None
    last_date = "Никогда"
    if last_workout and last_workout['end_time']:
        last_dt = datetime.fromisoformat(last_workout['start_time'])
        last_date = last_dt.strftime("%d.%m.%Y")

    text = (
        f"📊 <b>Твоя статистика</b>\n\n"
        f"🏋️ Всего тренировок: <b>{total_workouts}</b>\n"
        f"💪 Всего подходов: <b>{total_sets}</b>\n"
        f"⚡ Упражнений использовано: <b>{unique_exercises}</b>\n"
        f"📦 Общий тоннаж: <b>{total_volume:.0f} кг</b>\n"
        f"📅 Последняя тренировка: <b>{last_date}</b>\n\n"
        f"Выбери упражнение, чтобы посмотреть прогресс:"
    )

    # Получаем упражнения пользователя
    exercises = await db.get_user_exercises(user_id)

    if isinstance(event, Message):
        await event.answer(text, reply_markup=exercises_list_kb(exercises, action="select"), parse_mode="HTML")
    else:
        await event.message.edit_text(text, reply_markup=exercises_list_kb(exercises, action="select"),
                                      parse_mode="HTML")
        await event.answer()


@router.callback_query(F.data == "history_show")
@router.message(Command("history"))
async def show_history(event, state=None):
    """Показать историю тренировок"""
    if state:
        await state.clear()

    user_id = event.from_user.id
    workouts = await db.get_user_workouts(user_id, limit=10)

    if not workouts:
        text = "📖 <b>История тренировок</b>\n\nУ тебя пока нет тренировок."

        if isinstance(event, Message):
            await event.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")
        else:
            await event.message.edit_text(text, reply_markup=main_menu_kb(), parse_mode="HTML")
            await event.answer()
        return

    text = "📖 <b>История тренировок</b>\n\n"

    for i, workout in enumerate(workouts, 1):
        if not workout['end_time']:
            continue

        start_dt = datetime.fromisoformat(workout['start_time'])
        date_str = start_dt.strftime("%d.%m.%Y %H:%M")

        # Получаем подходы
        sets = await db.get_workout_sets(workout['id'])
        exercises_count = len(set([s['exercise_name'] for s in sets]))
        sets_count = len(sets)
        volume = calculate_volume(sets)

        text += (
            f"<b>{i}. {date_str}</b>\n"
            f"   └ Упражнений: {exercises_count}, Подходов: {sets_count}\n"
            f"   └ Тоннаж: {volume:.0f}кг\n\n"
        )

    if isinstance(event, Message):
        await event.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")
    else:
        await event.message.edit_text(text, reply_markup=main_menu_kb(), parse_mode="HTML")
        await event.answer()


@router.callback_query(F.data.startswith("exercise_select_"))
async def show_exercise_progress(callback: CallbackQuery):
    """Показать прогресс по упражнению"""
    exercise_id = int(callback.data.split("_")[2])

    exercise = await db.get_exercise_by_id(exercise_id)
    if not exercise:
        await callback.answer("❌ Упражнение не найдено", show_alert=True)
        return

    # Получаем историю
    history = await db.get_exercise_history(
        user_id=callback.from_user.id,
        exercise_id=exercise_id,
        limit=30
    )

    if not history:
        await callback.message.edit_text(
            f"💪 <b>{exercise['name']}</b>\n\n"
            "По этому упражнению пока нет записей.",
            reply_markup=back_kb("stats_show"),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    # Находим максимальный вес
    max_weight_entry = max(history, key=lambda x: x['weight'])
    max_weight = max_weight_entry['weight']

    # Последние 5 подходов
    recent_sets = history[:5]

    text = (
        f"💪 <b>{exercise['name']}</b>\n"
        f"📂 {exercise['category']}\n\n"
        f"🏆 Рекорд: <b>{max_weight:.1f}кг</b>\n\n"
        f"<b>Последние подходы:</b>\n"
    )

    for s in recent_sets:
        weight_str = f"{s['weight']:.1f}".rstrip('0').rstrip('.')
        date = datetime.fromisoformat(s['start_time']).strftime("%d.%m")
        text += f"• {date}: {weight_str}кг × {s['reps']} повт.\n"

    await callback.message.edit_text(
        text,
        reply_markup=back_kb("stats_show"),
        parse_mode="HTML"
    )
    await callback.answer()