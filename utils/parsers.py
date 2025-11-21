import re
from typing import Optional, Tuple


def parse_set_input(text: str) -> Optional[Tuple[float, int]]:
    """
    Парсит ввод подхода в различных форматах

    Поддерживаемые форматы:
    - "80x10" -> (80.0, 10)
    - "80 x 10" -> (80.0, 10)
    - "80*10" -> (80.0, 10)
    - "80/10" -> (80.0, 10)
    - "80кг 10" -> (80.0, 10)
    - "80 10" -> (80.0, 10)

    Returns:
        Tuple[float, int] - (вес, повторения) или None если не распознано
    """
    # Убираем лишние пробелы
    text = text.strip().lower()

    # Убираем единицы измерения
    text = text.replace('кг', '').replace('kg', '')

    # Паттерны для разных форматов
    patterns = [
        r'(\d+(?:\.\d+)?)\s*[x*×/]\s*(\d+)',  # 80x10, 80*10, 80/10
        r'(\d+(?:\.\d+)?)\s+(\d+)',  # 80 10
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                weight = float(match.group(1))
                reps = int(match.group(2))
                return (weight, reps)
            except (ValueError, IndexError):
                continue

    return None


def parse_weight_modifier(text: str) -> Optional[float]:
    """
    Парсит модификатор веса (+5, -5)

    Returns:
        float - значение модификатора или None
    """
    text = text.strip()

    # Паттерн для +5 или -5
    match = re.match(r'^([+-])(\d+(?:\.\d+)?)$', text)
    if match:
        sign = 1 if match.group(1) == '+' else -1
        value = float(match.group(2))
        return sign * value

    return None


def format_set_display(weight: float, reps: int, set_number: int = None) -> str:
    """
    Форматирует отображение подхода

    Args:
        weight: вес в кг
        reps: количество повторений
        set_number: номер подхода (опционально)

    Returns:
        str - отформатированная строка
    """
    # Убираем .0 если вес целое число
    weight_str = f"{weight:.1f}".rstrip('0').rstrip('.')

    if set_number:
        return f"Подход {set_number}: {weight_str}кг × {reps} повт."
    else:
        return f"{weight_str}кг × {reps} повт."


def format_workout_summary(sets: list) -> str:
    """
    Форматирует сводку тренировки

    Args:
        sets: список подходов (словари с полями exercise_name, weight, reps, set_number)

    Returns:
        str - отформатированная сводка
    """
    if not sets:
        return "Нет записанных подходов"

    # Группируем по упражнениям
    exercises = {}
    for s in sets:
        ex_name = s['exercise_name']
        if ex_name not in exercises:
            exercises[ex_name] = []
        exercises[ex_name].append(s)

    # Формируем текст
    result = []
    for ex_name, ex_sets in exercises.items():
        result.append(f"\n💪 {ex_name}")
        for s in ex_sets:
            weight_str = f"{s['weight']:.1f}".rstrip('0').rstrip('.')
            result.append(f"  └ {s['set_number']}. {weight_str}кг × {s['reps']} повт.")

    return '\n'.join(result)


def calculate_volume(sets: list) -> float:
    """
    Рассчитывает общий объем нагрузки (тоннаж)

    Args:
        sets: список подходов с полями weight и reps

    Returns:
        float - общий тоннаж в кг
    """
    return sum(s['weight'] * s['reps'] for s in sets if s.get('weight') and s.get('reps'))