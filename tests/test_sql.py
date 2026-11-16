import sqlite3
import unittest

from py import sql


class HabitSqlTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.executescript(
            """
            CREATE TABLE users (
                EMAIL TEXT PRIMARY KEY,
                PASSWORD TEXT NOT NULL
            );
            CREATE TABLE habit_list (
                EMAIL TEXT,
                HABIT_NAME TEXT,
                HABIT_DESCRIPTION TEXT,
                START_DATE TEXT,
                ACTIVE TEXT,
                GOAL_TYPE TEXT,
                DIFFICULTY INTEGER,
                DEFAULT_DAILY_GOAL REAL
            );
            CREATE TABLE daily_tracking (
                EMAIL TEXT,
                HABIT_NAME TEXT,
                DATE TEXT,
                TIME TEXT,
                COUNT_COMPLETED REAL,
                DAILY_GOAL REAL
            );
            """
        )

    def tearDown(self):
        self.connection.close()

    def test_user_provisioning_is_idempotent_and_clears_password(self):
        self.connection.execute(
            "INSERT INTO users (EMAIL, PASSWORD) VALUES (?, ?)",
            ("person@example.com", "legacy-password"),
        )
        self.connection.execute(sql.ensure_user(), ("person@example.com",) * 2)
        self.connection.execute(
            sql.clear_legacy_password(), ("person@example.com",)
        )
        users = self.connection.execute(
            "SELECT EMAIL, PASSWORD FROM users"
        ).fetchall()
        self.assertEqual(users, [("person@example.com", "")])

    def test_habit_and_tracking_queries_are_scoped_to_email(self):
        habit = (
            "person@example.com",
            "Read",
            "A few pages",
            "11/13/2026",
            "Y",
            "BINARY",
            3,
            None,
        )
        self.connection.execute(sql.insert_habits(), habit)
        self.connection.execute(
            sql.add_daily_habits(),
            (
                "person@example.com",
                "Read",
                "11/13/2026",
                "09:00",
                1,
                "person@example.com",
                "Read",
                "11/13/2026",
            ),
        )

        habits = self.connection.execute(
            sql.get_habits(), ("person@example.com",)
        ).fetchall()
        tracking = self.connection.execute(
            sql.get_tracking(), ("person@example.com",)
        ).fetchall()
        self.assertEqual(len(habits), 1)
        self.assertEqual(len(tracking), 1)

    def test_daily_check_in_insert_does_not_duplicate(self):
        parameters = (
            "person@example.com",
            "Read",
            "11/13/2026",
            "09:00",
            1,
            "person@example.com",
            "Read",
            "11/13/2026",
        )
        self.connection.execute(sql.add_daily_habits(), parameters)
        self.connection.execute(sql.add_daily_habits(), parameters)
        count = self.connection.execute(
            "SELECT COUNT(*) FROM daily_tracking"
        ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_numeric_goal_is_saved_and_progress_accumulates(self):
        self.connection.execute(
            "INSERT INTO habit_list VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "person@example.com",
                "Drink water",
                "",
                "11/13/2026",
                "Y",
                "NUMERIC",
                3,
                100,
            ),
        )
        self.connection.execute(
            sql.update_daily_goal(),
            (100, "person@example.com", "Drink water", "11/13/2026"),
        )
        self.connection.execute(
            sql.insert_daily_goal(),
            (
                "person@example.com",
                "Drink water",
                "11/13/2026",
                "09:00",
                100,
                "person@example.com",
                "Drink water",
                "11/13/2026",
            ),
        )

        for amount in (25, 10):
            self.connection.execute(
                sql.add_numeric_progress(),
                (
                    amount,
                    100,
                    "09:30",
                    "person@example.com",
                    "Drink water",
                    "11/13/2026",
                ),
            )
            self.connection.execute(
                sql.insert_numeric_progress(),
                (
                    "person@example.com",
                    "Drink water",
                    "11/13/2026",
                    "09:30",
                    amount,
                    100,
                    "person@example.com",
                    "Drink water",
                    "11/13/2026",
                ),
            )

        progress = self.connection.execute(
            """
            SELECT COUNT_COMPLETED, DAILY_GOAL
              FROM daily_tracking
             WHERE HABIT_NAME = 'Drink water'
            """
        ).fetchone()
        self.assertEqual(progress, (35.0, 100.0))
