"""Network transport tests that never contact the public server."""
import io
import json
import socket
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from api import SocialAPI


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, size=-1):
        return self.payload


class TransportTests(unittest.TestCase):
    def test_authorization_and_payload(self):
        api = SocialAPI("https://example.test")
        api.token = "test-token"
        def fake_open(request, timeout):
            self.assertEqual(request.get_header("Authorization"), "Bearer test-token")
            self.assertEqual(request.get_method(), "POST")
            self.assertEqual(json.loads(request.data), {"body": "Hello"})
            return FakeResponse(b'{"status":"okay"}')
        with patch("api.urlopen", side_effect=fake_open):
            self.assertEqual(api.request("/posts", "POST", {"body": "Hello"}), {"status": "okay"})

    def test_invalid_json_is_recoverable(self):
        with patch("api.urlopen", return_value=FakeResponse(b"<html>error</html>")):
            with self.assertRaisesRegex(ValueError, "invalid response"):
                SocialAPI("https://example.test").request("/feed")

    def test_timeout_is_recoverable(self):
        with patch("api.urlopen", side_effect=socket.timeout("timed out")):
            with self.assertRaisesRegex(ValueError, "Cannot connect"):
                SocialAPI("https://example.test").request("/feed")

    def test_http_error_message(self):
        error = HTTPError("https://example.test/feed", 401, "Unauthorized", {},
                          io.BytesIO(b'{"error":"Unauthorized"}'))
        with patch("api.urlopen", side_effect=error):
            with self.assertRaisesRegex(ValueError, "Unauthorized"):
                SocialAPI("https://example.test").request("/feed")


if __name__ == "__main__":
    unittest.main()
