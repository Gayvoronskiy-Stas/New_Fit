# SQL запросы для создания таблиц

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    timezone TEXT DEFAULT 'Europe/Moscow'
)
"""

CREATE_EXERCISES_TABLE = """
CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    category TEXT,
    exercise_type TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    UNIQUE(user_id, name)
)
"""

CREATE_WORKOUTS_TABLE = """
CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    workout_name TEXT,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    notes TEXT,
    energy_level INTEGER,
    sleep_quality INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
)
"""

CREATE_SETS_TABLE = """
CREATE TABLE IF NOT EXISTS sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,
    set_number INTEGER NOT NULL,
    weight REAL,
    reps INTEGER,
    rpe INTEGER,
    rest_time INTEGER,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workout_id) REFERENCES workouts (id),
    FOREIGN KEY (exercise_id) REFERENCES exercises (id)
)
"""

CREATE_WORKOUT_TEMPLATES_TABLE = """
CREATE TABLE IF NOT EXISTS workout_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    template_name TEXT NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    UNIQUE(user_id, template_name)
)
"""

CREATE_TEMPLATE_EXERCISES_TABLE = """
CREATE TABLE IF NOT EXISTS template_exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,
    order_number INTEGER NOT NULL,
    target_sets INTEGER,
    target_reps TEXT,
    notes TEXT,
    FOREIGN KEY (template_id) REFERENCES workout_templates (id),
    FOREIGN KEY (exercise_id) REFERENCES exercises (id)
)
"""

ALL_TABLES = [
    CREATE_USERS_TABLE,
    CREATE_EXERCISES_TABLE,
    CREATE_WORKOUTS_TABLE,
    CREATE_SETS_TABLE,
    CREATE_WORKOUT_TEMPLATES_TABLE,
    CREATE_TEMPLATE_EXERCISES_TABLE
]