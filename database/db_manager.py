import aiosqlite
from typing import List, Dict, Optional
from database.models import ALL_TABLES


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def init_db(self):
        """Инициализация базы данных"""
        async with aiosqlite.connect(self.db_path) as db:
            for table_query in ALL_TABLES:
                await db.execute(table_query)
            await db.commit()

    # ========== USERS ==========

    async def add_user(self, user_id: int, username: str = None, first_name: str = None):
        """Добавить пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
                (user_id, username, first_name)
            )
            await db.commit()

    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Получить пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    # ========== EXERCISES ==========

    async def add_exercise(self, user_id: int, name: str, category: str = None,
                           exercise_type: str = None) -> Optional[int]:
        """Добавить упражнение"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """INSERT INTO exercises (user_id, name, category, exercise_type) 
                       VALUES (?, ?, ?, ?)""",
                    (user_id, name, category, exercise_type)
                )
                await db.commit()
                return cursor.lastrowid
        except aiosqlite.IntegrityError:
            return None  # Упражнение уже существует

    async def get_user_exercises(self, user_id: int, category: str = None) -> List[Dict]:
        """Получить упражнения пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if category:
                query = "SELECT * FROM exercises WHERE user_id = ? AND category = ? ORDER BY name"
                params = (user_id, category)
            else:
                query = "SELECT * FROM exercises WHERE user_id = ? ORDER BY category, name"
                params = (user_id,)

            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_exercise_by_name(self, user_id: int, name: str) -> Optional[Dict]:
        """Получить упражнение по названию"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                    "SELECT * FROM exercises WHERE user_id = ? AND name = ?",
                    (user_id, name)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_exercise_by_id(self, exercise_id: int) -> Optional[Dict]:
        """Получить упражнение по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                    "SELECT * FROM exercises WHERE id = ?",
                    (exercise_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    # ========== WORKOUTS ==========

    async def create_workout(self, user_id: int, workout_name: str = None) -> int:
        """Создать новую тренировку"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO workouts (user_id, workout_name) VALUES (?, ?)",
                (user_id, workout_name)
            )
            await db.commit()
            return cursor.lastrowid

    async def finish_workout(self, workout_id: int, notes: str = None,
                             energy_level: int = None, sleep_quality: int = None):
        """Завершить тренировку"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE workouts 
                   SET end_time = CURRENT_TIMESTAMP, notes = ?, energy_level = ?, sleep_quality = ?
                   WHERE id = ?""",
                (notes, energy_level, sleep_quality, workout_id)
            )
            await db.commit()

    async def get_workout(self, workout_id: int) -> Optional[Dict]:
        """Получить тренировку"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM workouts WHERE id = ?", (workout_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_user_workouts(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Получить последние тренировки пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                    """SELECT * FROM workouts 
                       WHERE user_id = ? 
                       ORDER BY start_time DESC 
                       LIMIT ?""",
                    (user_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_active_workout(self, user_id: int) -> Optional[Dict]:
        """Получить активную тренировку (не завершенную)"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                    """SELECT * FROM workouts 
                       WHERE user_id = ? AND end_time IS NULL 
                       ORDER BY start_time DESC 
                       LIMIT 1""",
                    (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    # ========== SETS ==========

    async def add_set(self, workout_id: int, exercise_id: int, set_number: int,
                      weight: float, reps: int, rpe: int = None, notes: str = None) -> int:
        """Добавить подход"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO sets (workout_id, exercise_id, set_number, weight, reps, rpe, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (workout_id, exercise_id, set_number, weight, reps, rpe, notes)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_workout_sets(self, workout_id: int) -> List[Dict]:
        """Получить все подходы тренировки"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                    """SELECT s.*, e.name as exercise_name, e.category
                       FROM sets s
                       JOIN exercises e ON s.exercise_id = e.id
                       WHERE s.workout_id = ?
                       ORDER BY s.created_at""",
                    (workout_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_last_set(self, workout_id: int, exercise_id: int) -> Optional[Dict]:
        """Получить последний подход упражнения в тренировке"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                    """SELECT * FROM sets 
                       WHERE workout_id = ? AND exercise_id = ?
                       ORDER BY set_number DESC
                       LIMIT 1""",
                    (workout_id, exercise_id)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_exercise_history(self, user_id: int, exercise_id: int, limit: int = 10) -> List[Dict]:
        """Получить историю упражнения"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                    """SELECT s.*, w.start_time, w.workout_name
                       FROM sets s
                       JOIN workouts w ON s.workout_id = w.id
                       WHERE w.user_id = ? AND s.exercise_id = ?
                       ORDER BY w.start_time DESC, s.set_number
                       LIMIT ?""",
                    (user_id, exercise_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    # ========== TEMPLATES ==========

    async def create_template(self, user_id: int, template_name: str,
                              description: str = None) -> Optional[int]:
        """Создать шаблон тренировки"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "INSERT INTO workout_templates (user_id, template_name, description) VALUES (?, ?, ?)",
                    (user_id, template_name, description)
                )
                await db.commit()
                return cursor.lastrowid
        except aiosqlite.IntegrityError:
            return None

    async def add_exercise_to_template(self, template_id: int, exercise_id: int,
                                       order_number: int, target_sets: int = None,
                                       target_reps: str = None, notes: str = None):
        """Добавить упражнение в шаблон"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO template_exercises 
                   (template_id, exercise_id, order_number, target_sets, target_reps, notes)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (template_id, exercise_id, order_number, target_sets, target_reps, notes)
            )
            await db.commit()

    async def get_user_templates(self, user_id: int) -> List[Dict]:
        """Получить шаблоны пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                    "SELECT * FROM workout_templates WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_template_exercises(self, template_id: int) -> List[Dict]:
        """Получить упражнения шаблона"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                    """SELECT te.*, e.name as exercise_name, e.category
                       FROM template_exercises te
                       JOIN exercises e ON te.exercise_id = e.id
                       WHERE te.template_id = ?
                       ORDER BY te.order_number""",
                    (template_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def delete_template(self, template_id: int):
        """Удалить шаблон"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM template_exercises WHERE template_id = ?", (template_id,))
            await db.execute("DELETE FROM workout_templates WHERE id = ?", (template_id,))
            await db.commit()