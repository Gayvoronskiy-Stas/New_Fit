from aiogram.fsm.state import State, StatesGroup


class WorkoutStates(StatesGroup):
    """Состояния для записи тренировки"""
    selecting_template = State()  # Выбор шаблона
    active_workout = State()      # Активная тренировка
    selecting_exercise = State()  # Выбор упражнения
    entering_set = State()        # Ввод данных подхода
    entering_notes = State()      # Ввод заметок о тренировке


class ExerciseStates(StatesGroup):
    """Состояния для управления упражнениями"""
    entering_name = State()       # Ввод названия
    selecting_category = State()  # Выбор категории


class TemplateStates(StatesGroup):
    """Состояния для создания шаблона"""
    entering_name = State()        # Ввод названия шаблона
    entering_description = State() # Ввод описания
    adding_exercises = State()     # Добавление упражнений
    setting_targets = State()      # Настройка целей (подходы/повторы)