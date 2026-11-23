"""Tests for the network-facing rooms without a live server."""
import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from api import SocialAPI
from accounts import profile
from book import open_book
from social import living_room


class FakeAPI:
    def __init__(self):
        self.calls = []
        self.token = "test-token"

    def request(self, path, method="GET", payload=None):
        self.calls.append((path, method, payload))
        if path.startswith("/feed") or path.startswith("/shelf"):
            return {"posts": [], "next_before": None}
        if path == "/me/following":
            return {"users": ["Alice"]}
        if path.startswith("/users/") and not path.endswith("/follow"):
            username = path.split("/")[2]
            return {"username": username, "bio": "Hello", "description": "My page",
                    "status": "", "followers": 2, "following_count": 4,
                    "is_self": username == "test"}
        if path.startswith("/users?"):
            return {"users": []}
        return {"status": "okay"}


class NetworkRoomsTests(unittest.TestCase):
    def test_default_api_uses_hosted_endpoint(self):
        self.assertEqual(SocialAPI().base_url, "https://social.xylin48.site")

    def test_book_uses_remote_feed(self):
        api = FakeAPI()
        with patch("builtins.input", side_effect=["back"]), redirect_stdout(io.StringIO()):
            open_book(api)
        self.assertEqual(api.calls[0][0], "/feed")

    def test_living_room_routes_to_book(self):
        api = FakeAPI()
        with patch("builtins.input", side_effect=["book", "back", "logout"]), redirect_stdout(io.StringIO()):
            living_room(api, "Alice")
        self.assertEqual(api.calls[0][0], "/feed")
        self.assertEqual(api.calls[-1][0], "/logout")

    def test_shelf_uses_remote_feed(self):
        from shelf import open_shelf
        api = FakeAPI()
        with patch("builtins.input", side_effect=["following", "back"]), redirect_stdout(io.StringIO()):
            open_shelf(api)
        self.assertEqual(api.calls[0][0], "/shelf")
        self.assertEqual(api.calls[1][0], "/me/following")

    def test_follow_and_unfollow_route_to_server(self):
        api = FakeAPI()
        with patch("builtins.input", side_effect=["follow Alice", "unfollow Alice", "logout"]), redirect_stdout(io.StringIO()):
            living_room(api, "test")
        self.assertEqual(api.calls[0][:2], ("/users/Alice/follow", "POST"))
        self.assertEqual(api.calls[1][:2], ("/users/Alice/follow", "DELETE"))

    def test_profile_numbered_follow_and_named_unfollow(self):
        api = FakeAPI()
        with patch("builtins.input", side_effect=["1", "unfollow", "3"]), redirect_stdout(io.StringIO()) as output:
            profile(api, "Alice")
        self.assertIn("Welcome to Alice's profile", output.getvalue())
        self.assertIn("[1. follow] [2. unfollow] [3. back]", output.getvalue())
        self.assertEqual([call[:2] for call in api.calls if call[0].endswith("/follow")],
                         [("/users/Alice/follow", "POST"), ("/users/Alice/follow", "DELETE")])

    def test_own_profile_edit_and_back(self):
        api = FakeAPI()
        with patch("builtins.input", side_effect=["edit", "5", "back"]), redirect_stdout(io.StringIO()) as output:
            profile(api, "test")
        self.assertIn("[1. edit] [2. posts] [3. back]", output.getvalue())
        self.assertIn("ACCOUNT SETTINGS", output.getvalue())

    def test_numbered_book_navigation(self):
        api = FakeAPI()
        with patch("builtins.input", side_effect=["1", "4"]), redirect_stdout(io.StringIO()):
            open_book(api)
        self.assertEqual([c[0] for c in api.calls], ["/feed", "/feed"])

    def test_numbered_shelf_navigation(self):
        from shelf import open_shelf
        api = FakeAPI()
        with patch("builtins.input", side_effect=["3", "4"]), redirect_stdout(io.StringIO()):
            open_shelf(api)
        self.assertEqual([c[0] for c in api.calls], ["/shelf", "/me/following"])

    def test_numbered_living_room_navigation(self):
        api = FakeAPI()
        with patch("builtins.input", side_effect=["1", "4", "7"]), redirect_stdout(io.StringIO()):
            living_room(api, "test")
        self.assertEqual(api.calls[0][0], "/feed")
        self.assertEqual(api.calls[-1][0], "/logout")

    def test_post_is_sent_to_server(self):
        api = FakeAPI()
        with patch("builtins.input", side_effect=["post Hello world", "logout"]), redirect_stdout(io.StringIO()):
            living_room(api, "Alice")
        self.assertEqual(api.calls[0], ("/posts", "POST", {"body": "Hello world"}))


if __name__ == "__main__":
    unittest.main()
