import datetime as dt
import unittest
from unittest.mock import patch

from py.habits import create_habit


class HabitCreationTests(unittest.TestCase):
    @patch("py.habits.get_db_connection", return_value="test-connection")
    @patch("py.habits.sqlitecloud.connect")
    def test_create_weekly_habit_saves_selected_weekdays(
        self, connect, get_connection
    ):
        connection = connect.return_value.__enter__.return_value

        create_habit(
            "person@example.com",
            "Shower",
            "",
            dt.date(2026, 11, 16),
            "BINARY",
            3,
            frequency="WEEKLY",
            scheduled_days=[0, 1, 2, 3, 4],
        )

        parameters = connection.execute.call_args.kwargs["parameters"]
        self.assertEqual(parameters[-3:], ("WEEKLY", "0,1,2,3,4", None))
        get_connection.assert_called_once_with()

    @patch("py.habits.sqlitecloud.connect")
    def test_weekly_habit_requires_at_least_one_day(self, connect):
        with self.assertRaisesRegex(ValueError, "at least one"):
            create_habit(
                "person@example.com",
                "Shower",
                "",
                dt.date(2026, 11, 16),
                "BINARY",
                3,
                frequency="WEEKLY",
                scheduled_days=[],
            )
        connect.assert_not_called()

    @patch("py.habits.get_db_connection", return_value="test-connection")
    @patch("py.habits.sqlitecloud.connect")
    def test_create_monthly_habit_saves_completion_target(
        self, connect, get_connection
    ):
        connection = connect.return_value.__enter__.return_value

        create_habit(
            "person@example.com",
            "Laundry",
            "",
            dt.date(2026, 11, 16),
            "BINARY",
            2,
            frequency="MONTHLY",
            period_target=4,
        )

        parameters = connection.execute.call_args.kwargs["parameters"]
        self.assertEqual(parameters[-3:], ("MONTHLY", None, 4))
        get_connection.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
