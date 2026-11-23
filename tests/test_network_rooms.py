"""Tests for the network-facing rooms without a live server."""
import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from api import SocialAPI
from book import open_book
from social import living_room


class FakeAPI:
    def __init__(self):
        self.calls = []
        self.token = "test-token"

    def request(self, path, method="GET", payload=None):
        self.calls.append((path, method, payload))
        if path.startswith("/feed"):
            return {"posts": [], "next_before": None}
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

    def test_post_is_sent_to_server(self):
        api = FakeAPI()
        with patch("builtins.input", side_effect=["post Hello world", "logout"]), redirect_stdout(io.StringIO()):
            living_room(api, "Alice")
        self.assertEqual(api.calls[0], ("/posts", "POST", {"body": "Hello world"}))


if __name__ == "__main__":
    unittest.main()
