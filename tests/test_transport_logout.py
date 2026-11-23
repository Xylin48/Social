"""Regression coverage for API transport failures and local logout state."""
import io
import socket
import unittest
from unittest.mock import patch

from api import SocialAPI
from social import living_room


class TransportTests(unittest.TestCase):
    def test_socket_timeout_is_reported_as_value_error(self):
        api = SocialAPI("https://example.invalid")
        with patch("api.urlopen", side_effect=socket.timeout("timed out")):
            with self.assertRaisesRegex(ValueError, "Cannot connect to Social server: timed out"):
                api.request("/health")

    def test_connection_error_is_reported_as_value_error(self):
        api = SocialAPI("https://example.invalid")
        with patch("api.urlopen", side_effect=ConnectionError("connection reset")):
            with self.assertRaisesRegex(ValueError, "connection reset"):
                api.request("/health")


class LogoutTests(unittest.TestCase):
    def test_logout_clears_token_on_success(self):
        api = SocialAPI("https://example.invalid")
        api.token = "session-secret"
        with patch.object(api, "request", return_value={"status": "okay"}), \
             patch("builtins.input", return_value="logout"), \
             patch("sys.stdout", new_callable=io.StringIO):
            living_room(api, "tester")
        self.assertIsNone(api.token)

    def test_logout_clears_token_when_server_unavailable(self):
        api = SocialAPI("https://example.invalid")
        api.token = "session-secret"
        with patch.object(api, "request", side_effect=ValueError("offline")), \
             patch("builtins.input", return_value="logout"), \
             patch("sys.stdout", new_callable=io.StringIO):
            living_room(api, "tester")
        self.assertIsNone(api.token)


if __name__ == "__main__":
    unittest.main()
