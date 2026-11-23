"""Local-clock status behavior, independent of a live server."""
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from contextlib import redirect_stdout
import io
from status import visible_status
from settings import menu


class StatusTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 22, tzinfo=timezone.utc)

    def data(self, hours, infinite=False):
        return {"status": "Working on Social",
                "status_set_at": (self.now - timedelta(hours=hours)).isoformat(),
                "status_infinite": infinite}

    def test_visible_before_expiration(self):
        self.assertEqual(visible_status(self.data(47), self.now), "Working on Social")

    def test_hidden_at_48_hours(self):
        self.assertEqual(visible_status(self.data(48), self.now), "")

    def test_infinite_remains_visible(self):
        self.assertEqual(visible_status(self.data(500), self.now), "Working on Social")

    def test_invalid_timestamp_is_hidden(self):
        self.assertEqual(visible_status({"status": "Hi", "status_set_at": "bad"}), "")

    def test_settings_save_infinite(self):
        class FakeAPI:
            def __init__(self):
                self.calls = []
            def request(self, *args):
                self.calls.append(args)
        api = FakeAPI()
        with patch("builtins.input", side_effect=["2", "Working on Social", "2", "5"]), redirect_stdout(io.StringIO()):
            menu(api)
        self.assertEqual(api.calls, [("/me", "PATCH", {"status": "Working on Social", "status_infinite": True})])


if __name__ == "__main__":
    unittest.main()
