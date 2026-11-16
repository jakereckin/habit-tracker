import datetime as dt
import unittest

import pandas as pd

from py.habit_logic import (
    best_streak,
    completed_habits_for_date,
    current_streak,
    daily_progress,
)


class HabitLogicTests(unittest.TestCase):
    def setUp(self):
        self.tracking = pd.DataFrame(
            [
                ("Read", "11/10/2026", 1),
                ("Read", "11/11/2026", 1),
                ("Read", "11/12/2026", 1),
                ("Walk", "11/12/2026", 1),
                ("Read", "11/13/2026", 0),
            ],
            columns=["HABIT_NAME", "DATE", "COUNT_COMPLETED"],
        )

    def test_completed_habits_for_date_ignores_zero_count(self):
        completed = completed_habits_for_date(
            self.tracking, dt.date(2026, 11, 13)
        )
        self.assertEqual(completed, set())

    def test_current_streak_includes_today_and_previous_days(self):
        streak = current_streak(
            self.tracking, "Read", dt.date(2026, 11, 12)
        )
        self.assertEqual(streak, 3)

    def test_current_streak_allows_today_to_be_incomplete(self):
        streak = current_streak(
            self.tracking, "Read", dt.date(2026, 11, 13)
        )
        self.assertEqual(streak, 3)

    def test_best_streak_is_longest_consecutive_run(self):
        self.assertEqual(best_streak(self.tracking, "Read"), 3)

    def test_numeric_habit_requires_reaching_daily_goal(self):
        tracking = pd.DataFrame(
            [
                ("Pages", "11/12/2026", 25, 100, "NUMERIC"),
                ("Pages", "11/13/2026", 100, 100, "NUMERIC"),
            ],
            columns=[
                "HABIT_NAME",
                "DATE",
                "COUNT_COMPLETED",
                "DAILY_GOAL",
                "GOAL_TYPE",
            ],
        )
        self.assertEqual(
            completed_habits_for_date(tracking, dt.date(2026, 11, 12)),
            set(),
        )
        self.assertEqual(
            completed_habits_for_date(
                tracking, dt.date(2026, 11, 13)
            ),
            {"Pages"},
        )
        self.assertEqual(
            current_streak(tracking, "Pages", dt.date(2026, 11, 13)),
            1,
        )
        self.assertEqual(
            daily_progress(tracking, "Pages", dt.date(2026, 11, 12)),
            (25.0, 100.0),
        )


if __name__ == "__main__":
    unittest.main()
