"""Validate malformed request bodies without connecting to PostgreSQL."""
import os
import unittest
from unittest.mock import patch

# The server validates DATABASE_URL during import; these tests never use it.
os.environ.setdefault("DATABASE_URL", "postgresql://unused:unused@localhost/unused")
from server import app


class InvalidPayloadTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_register_rejects_non_object(self):
        for payload in ([], "hello", 42, None):
            with self.subTest(payload=payload):
                response = self.client.post("/register", json=payload)
                self.assertEqual(response.status_code, 400)

    def test_login_rejects_non_object(self):
        for payload in ([], "hello", 42, None):
            with self.subTest(payload=payload):
                response = self.client.post("/login", json=payload)
                self.assertEqual(response.status_code, 400)

    def test_authenticated_routes_reject_non_object(self):
        # Replace the auth decorator's database lookup so the endpoint can
        # be tested without a live PostgreSQL service.
        with patch("server.connection") as connect:
            connect.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = {"username": "tester"}
            for path, method in (("/posts", "post"), ("/me", "patch"), ("/me/password", "post")):
                for payload in ([], "hello", 42, None):
                    with self.subTest(path=path, payload=payload):
                        response = getattr(self.client, method)(
                            path, json=payload, headers={"Authorization": "Bearer test-token"}
                        )
                        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
