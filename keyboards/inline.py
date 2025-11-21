from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict


def main_menu_kb() -> InlineKeyboardMarkup:
    """Главное меню"""
    keyboard = [
        [InlineKeyboardButton(text="🏋️ Новая тренировка", callback_data="workout_new")],
        [InlineKeyboardButton(text="📋 Мои шаблоны", callback_data="templates_list")],
        [InlineKeyboardButton(text="💪 Упражнения", callback_data="exercises_list")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats_show")],
        [InlineKeyboardButton(text="📖 История", callback_data="history_show")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def workout_start_kb(has_templates: bool = False) -> InlineKeyboardMarkup:
    """Меню начала тренировки"""
    keyboard = []

    if has_templates:
        keyboard.append([InlineKeyboardButton(text="📋 По шаблону", callback_data="workout_from_template")])

    keyboard.append([InlineKeyboardButton(text="⚡ Быстрая тренировка", callback_data="workout_quick")])
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="menu_main")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def templates_list_kb(templates: List[Dict]) -> InlineKeyboardMarkup:
    """Список шаблонов"""
    keyboard = []

    for template in templates:
        keyboard.append([
            InlineKeyboardButton(
                text=template['template_name'],
                callback_data=f"template_select_{template['id']}"
            )
        ])

    keyboard.append([InlineKeyboardButton(text="➕ Создать новый", callback_data="template_create")])
    keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="menu_main")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def template_actions_kb(template_id: int) -> InlineKeyboardMarkup:
    """Действия с шаблоном"""
    keyboard = [
        [InlineKeyboardButton(text="🏋️ Начать тренировку", callback_data=f"workout_start_{template_id}")],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"template_edit_{template_id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"template_delete_{template_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="templates_list")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def exercises_list_kb(exercises: List[Dict], action: str = "select") -> InlineKeyboardMarkup:
    """
    Список упражнений
    action: 'select' - для выбора, 'view' - для просмотра
    """
    keyboard = []

    # Группируем по категориям
    categories = {}
    for ex in exercises:
        cat = ex.get('category') or 'Без категории'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(ex)

    # Добавляем по категориям
    for cat, exs in categories.items():
        # Заголовок категории (не кликабельный)
        keyboard.append([InlineKeyboardButton(text=f"📂 {cat}", callback_data="none")])

        # Упражнения категории
        for ex in exs:
            if action == "select":
                keyboard.append([
                    InlineKeyboardButton(
                        text=f"  • {ex['name']}",
                        callback_data=f"exercise_select_{ex['id']}"
                    )
                ])
            else:
                keyboard.append([
                    InlineKeyboardButton(
                        text=f"  • {ex['name']}",
                        callback_data=f"exercise_view_{ex['id']}"
                    )
                ])

    keyboard.append([InlineKeyboardButton(text="➕ Добавить упражнение", callback_data="exercise_add")])
    keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="menu_main")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def exercise_categories_kb() -> InlineKeyboardMarkup:
    """Категории упражнений"""
    categories = [
        "Грудь", "Спина", "Ноги", "Плечи",
        "Бицепс", "Трицепс", "Пресс", "Кардио"
    ]

    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(text=cat, callback_data=f"category_{cat}")])

    keyboard.append([InlineKeyboardButton(text="◀️ Отмена", callback_data="exercises_list")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def active_workout_kb(exercise_id: int = None, has_more_exercises: bool = False) -> InlineKeyboardMarkup:
    """Меню активной тренировки"""
    keyboard = []

    if exercise_id:
        keyboard.append([InlineKeyboardButton(text="➕ Еще подход", callback_data=f"set_repeat_{exercise_id}")])

    if has_more_exercises:
        keyboard.append([InlineKeyboardButton(text="➡️ Следующее упражнение", callback_data="exercise_next")])
    else:
        keyboard.append([InlineKeyboardButton(text="➕ Добавить упражнение", callback_data="exercise_add_to_workout")])

    keyboard.append([InlineKeyboardButton(text="📝 Добавить заметку", callback_data="workout_add_note")])
    keyboard.append([InlineKeyboardButton(text="✅ Завершить тренировку", callback_data="workout_finish")])
    keyboard.append([InlineKeyboardButton(text="❌ Отменить тренировку", callback_data="workout_cancel")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def set_repeat_kb(last_weight: float = None, last_reps: int = None) -> InlineKeyboardMarkup:
    """Быстрые действия после подхода"""
    keyboard = []

    if last_weight and last_reps:
        keyboard.append([
            InlineKeyboardButton(
                text=f"🔁 Повторить ({last_weight}кг × {last_reps})",
                callback_data="set_same"
            )
        ])
        keyboard.append([
            InlineKeyboardButton(text="➕ Добавить вес", callback_data="set_add_weight"),
            InlineKeyboardButton(text="➖ Убавить вес", callback_data="set_sub_weight")
        ])

    keyboard.append([InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="set_manual")])
    keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="workout_menu")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def confirm_kb(action: str) -> InlineKeyboardMarkup:
    """Подтверждение действия"""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}"),
            InlineKeyboardButton(text="❌ Нет", callback_data=f"cancel_{action}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def back_kb(callback: str = "menu_main") -> InlineKeyboardMarkup:
    """Простая кнопка назад"""
    keyboard = [[InlineKeyboardButton(text="◀️ Назад", callback_data=callback)]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)