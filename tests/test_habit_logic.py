import datetime as dt
import unittest

import pandas as pd

from py.habit_logic import (
    best_streak,
    completed_habits_for_date,
    current_streak,
    daily_progress,
    habit_period_progress,
    is_habit_due,
    skipped_habits_for_date,
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

    def test_numeric_default_goal_applies_before_daily_override(self):
        tracking = pd.DataFrame(
            columns=["HABIT_NAME", "DATE", "COUNT_COMPLETED", "DAILY_GOAL"]
        )
        self.assertEqual(
            daily_progress(
                tracking,
                "Pages",
                dt.date(2026, 11, 13),
                default_goal=100,
            ),
            (0.0, 100),
        )

    def test_weekly_goal_is_due_only_on_selected_weekdays(self):
        self.assertTrue(
            is_habit_due(
                "WEEKLY", "0,1,2,3,4", dt.date(2026, 11, 16)
            )
        )
        self.assertFalse(
            is_habit_due(
                "WEEKLY", "0,1,2,3,4", dt.date(2026, 11, 21)
            )
        )

    def test_weekly_progress_excludes_skipped_scheduled_day(self):
        tracking = pd.DataFrame(
            [
                ("Shower", "11/16/2026", 1),
                ("Shower", "11/17/2026", 1),
            ],
            columns=["HABIT_NAME", "DATE", "COUNT_COMPLETED"],
        )
        completed, target, label = habit_period_progress(
            tracking,
            "Shower",
            dt.date(2026, 11, 18),
            "WEEKLY",
            "0,1,2,3,4",
            skipped_dates={dt.date(2026, 11, 17)},
        )
        self.assertEqual((completed, target, label), (1, 4, "this week"))

    def test_monthly_progress_counts_completed_dates_within_month(self):
        tracking = pd.DataFrame(
            [
                ("Laundry", "11/02/2026", 1),
                ("Laundry", "11/03/2026", 1),
                ("Laundry", "10/31/2026", 1),
            ],
            columns=["HABIT_NAME", "DATE", "COUNT_COMPLETED"],
        )
        self.assertEqual(
            habit_period_progress(
                tracking,
                "Laundry",
                dt.date(2026, 11, 16),
                "MONTHLY",
                period_target=5,
            ),
            (2, 5, "this month"),
        )

    def test_skip_removes_date_from_completed_and_preserves_daily_streak(self):
        skipped_date = dt.date(2026, 11, 11)
        skip_days = pd.DataFrame(
            [("Read", "11/11/2026")],
            columns=["HABIT_NAME", "DATE"],
        )
        completed = completed_habits_for_date(
            self.tracking,
            skipped_date,
            skipped_habits_for_date(skip_days, skipped_date),
        )
        self.assertEqual(completed, set())
        self.assertEqual(
            current_streak(
                self.tracking,
                "Read",
                dt.date(2026, 11, 12),
                {skipped_date},
            ),
            2,
        )
        self.assertEqual(
            best_streak(self.tracking, "Read", {skipped_date}),
            2,
        )


if __name__ == "__main__":
    unittest.main()
