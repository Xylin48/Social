"""Regression tests for notification navigation and terminal announcements."""
import contextlib
import io
import unittest
from unittest.mock import patch
import notifi


class FakeAPI:
    token = "test-session"

    def __init__(self):
        self.calls = []
        self.summary = {"unread": 6, "unseen_posts": 5, "latest_post_author": "Alex"}

    def request(self, path, method="GET", payload=None):
        self.calls.append((path, method))
        if path == "/notifications/summary":
            return self.summary
        if path == "/notifications":
            return {"notifications": [
                {"id": 7, "kind": "post", "actor": "Alex", "post_id": 42, "read_at": None},
                {"id": 8, "kind": "profile", "actor": "Jordan", "post_id": None, "read_at": None},
            ]}
        if path == "/posts/42":
            return {"id": 42, "username": "Alex", "body": "hello",
                    "created_at": "now", "like_count": 0, "repost_count": 0}
        return {"status": "okay"}


class NotificationsTest(unittest.TestCase):
    def setUp(self):
        notifi._last_announcement.clear()

    def test_five_posts_announced_once(self):
        api = FakeAPI()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            notifi.announce(api)
            notifi.announce(api)
        self.assertEqual(output.getvalue().count("Check your Shelf"), 1)

    def test_announcement_changes_for_new_session(self):
        first = FakeAPI()
        second = FakeAPI()
        second.token = "other-session"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            notifi.announce(first)
            notifi.announce(second)
        self.assertEqual(output.getvalue().count("Check your Shelf"), 2)

    def test_post_notification_opens_original_post(self):
        api = FakeAPI()
        with patch("builtins.input", side_effect=["1", "back"]), contextlib.redirect_stdout(io.StringIO()):
            notifi.open_notifications(api)
        self.assertIn(("/notifications/7/read", "POST"), api.calls)
        self.assertIn(("/posts/42", "GET"), api.calls)

    def test_profile_notification_opens_profile(self):
        api = FakeAPI()
        with patch("builtins.input", side_effect=["2", "back"]), patch.object(notifi, "profile") as profile:
            with contextlib.redirect_stdout(io.StringIO()):
                notifi.open_notifications(api)
        profile.assert_called_once_with(api, "Jordan")


if __name__ == "__main__":
    unittest.main()
