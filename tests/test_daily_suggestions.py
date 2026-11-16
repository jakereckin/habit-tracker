import unittest
from types import SimpleNamespace
from unittest.mock import patch

from py.daily_suggestions import (
    MODEL,
    DailySuggestionError,
    generate_daily_suggestions,
)


class DailySuggestionTests(unittest.TestCase):
    @patch("py.daily_suggestions.genai.Client")
    def test_generates_suggestions_with_the_daily_context(self, client_class):
        client = client_class.return_value
        client.models.generate_content.return_value = SimpleNamespace(
            text="- Take a short walk."
        )
        habits = [{"habit": "Walk", "status": "not complete"}]

        result = generate_daily_suggestions("test-key", habits)

        self.assertEqual(result, "- Take a short walk.")
        client_class.assert_called_once_with(api_key="test-key")
        client.models.generate_content.assert_called_once()
        call = client.models.generate_content.call_args.kwargs
        self.assertEqual(call["model"], MODEL)
        self.assertIn(str(habits), call["contents"])
        self.assertIn(
            "do not suggest a habit marked skipped or not scheduled",
            call["contents"],
        )

    @patch("py.daily_suggestions.genai.Client")
    def test_rejects_an_empty_model_response(self, client_class):
        client_class.return_value.models.generate_content.return_value = (
            SimpleNamespace(text=" ")
        )

        with self.assertRaisesRegex(DailySuggestionError, "returned no suggestions"):
            generate_daily_suggestions("test-key", [])


if __name__ == "__main__":
    unittest.main()
