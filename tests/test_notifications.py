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

    def test_three_posts_announced_individually(self):
        api = FakeAPI()
        api.summary = {"unread": 3, "unseen_posts": 3,
                       "recent_post_authors": ["Jordan", "Alex", "Sam"]}
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            notifi.announce(api)
        text = output.getvalue()
        self.assertEqual(text.count("[Notification]"), 3)
        self.assertIn("Sam made a post.", text)
        self.assertNotIn("Check your Shelf", text)

    def test_zero_posts_still_announces_other_notifications(self):
        api = FakeAPI()
        api.summary = {"unread": 2, "unseen_posts": 0,
                       "recent_post_authors": []}
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            notifi.announce(api)
        self.assertIn("2 unread notifications", output.getvalue())

    def test_post_notification_opens_original_post(self):
        api = FakeAPI()
        with patch("builtins.input", side_effect=["1", "back"]), contextlib.redirect_stdout(io.StringIO()):
            notifi.open_notifications(api)
        self.assertIn(("/notifications/7/read", "POST"), api.calls)
        self.assertIn(("/posts/42", "GET"), api.calls)

    def test_missing_post_does_not_mark_notification_read(self):
        api = FakeAPI()
        original = api.request

        def request(path, method="GET", payload=None):
            if path == "/posts/42":
                raise ValueError("Post not found")
            return original(path, method, payload)

        api.request = request
        output = io.StringIO()
        with patch("builtins.input", side_effect=["1", "back"]), contextlib.redirect_stdout(output):
            notifi.open_notifications(api)
        self.assertIn("Unable to open notification", output.getvalue())
        self.assertNotIn(("/notifications/7/read", "POST"), api.calls)

    def test_unread_notifications_are_not_mixed_into_shelf(self):
        from shelf import open_shelf
        api = FakeAPI()
        original = api.request

        def request(path, method="GET", payload=None):
            if path.startswith("/shelf"):
                return {"posts": [], "next_before": None}
            return original(path, method, payload)

        api.request = request
        with patch("builtins.input", side_effect=["back"]), contextlib.redirect_stdout(io.StringIO()):
            open_shelf(api)
        self.assertNotIn(("/notifications", "GET"), api.calls)

    def test_profile_notification_opens_profile(self):
        api = FakeAPI()
        with patch("builtins.input", side_effect=["2", "back"]), patch.object(notifi, "profile") as profile:
            with contextlib.redirect_stdout(io.StringIO()):
                notifi.open_notifications(api)
        profile.assert_called_once_with(api, "Jordan")


if __name__ == "__main__":
    unittest.main()
