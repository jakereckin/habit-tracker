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
                DEFAULT_DAILY_GOAL REAL,
                GOAL_FREQUENCY TEXT,
                SCHEDULED_DAYS TEXT,
                PERIOD_TARGET INTEGER
            );
            CREATE TABLE daily_tracking (
                EMAIL TEXT,
                HABIT_NAME TEXT,
                DATE TEXT,
                TIME TEXT,
                COUNT_COMPLETED REAL,
                DAILY_GOAL REAL
            );
            CREATE TABLE habit_skip_days (
                EMAIL TEXT,
                HABIT_NAME TEXT,
                DATE TEXT,
                PRIMARY KEY (EMAIL, HABIT_NAME, DATE)
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
            "WEEKLY",
            "0,1,2,3,4",
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
        self.assertEqual(habits[0][8:], ("WEEKLY", "0,1,2,3,4", None))

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
            """
            INSERT INTO habit_list (
                EMAIL, HABIT_NAME, HABIT_DESCRIPTION, START_DATE, ACTIVE,
                GOAL_TYPE, DIFFICULTY, DEFAULT_DAILY_GOAL,
                GOAL_FREQUENCY, SCHEDULED_DAYS, PERIOD_TARGET
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "person@example.com",
                "Drink water",
                "",
                "11/13/2026",
                "Y",
                "NUMERIC",
                3,
                100,
                "DAILY",
                None,
                None,
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

    def test_skip_day_is_scoped_and_can_be_undone(self):
        parameters = (
            "person@example.com",
            "Shower",
            "11/16/2026",
            "person@example.com",
            "Shower",
            "11/16/2026",
        )
        self.connection.execute(sql.insert_skip_day(), parameters)
        self.connection.execute(sql.insert_skip_day(), parameters)
        skipped = self.connection.execute(
            sql.get_skip_days(), ("person@example.com",)
        ).fetchall()
        self.assertEqual(skipped, [("person@example.com", "Shower", "11/16/2026")])

        self.connection.execute(
            sql.remove_skip_day(),
            ("person@example.com", "Shower", "11/16/2026"),
        )
        skipped = self.connection.execute(
            sql.get_skip_days(), ("person@example.com",)
        ).fetchall()
        self.assertEqual(skipped, [])

    def test_weekly_cadence_update_replaces_days_and_clears_month_target(self):
        self.connection.execute(
            """
            INSERT INTO habit_list (
                EMAIL, HABIT_NAME, GOAL_FREQUENCY, SCHEDULED_DAYS,
                PERIOD_TARGET
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                "person@example.com",
                "Shower",
                "MONTHLY",
                None,
                10,
            ),
        )
        self.connection.execute(
            sql.update_habit_cadence(),
            (
                "WEEKLY",
                "0,1,2,3,4",
                None,
                "person@example.com",
                "Shower",
            ),
        )
        cadence = self.connection.execute(
            """
            SELECT GOAL_FREQUENCY, SCHEDULED_DAYS, PERIOD_TARGET
              FROM habit_list
             WHERE HABIT_NAME = 'Shower'
            """
        ).fetchone()
        self.assertEqual(cadence, ("WEEKLY", "0,1,2,3,4", None))
