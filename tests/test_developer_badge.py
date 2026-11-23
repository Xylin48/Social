"""Developer identity must be consistent, server-owned and visible throughout Social."""
import io
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://unused:unused@localhost/unused")
from server import is_developer, decorate_identity
from posts import display, identity


class DeveloperBadgeTests(unittest.TestCase):
    def test_server_configuration_is_case_insensitive(self):
        with patch.dict(os.environ, {"SOCIAL_DEV_USERS": "Xylin48, OtherDev"}):
            self.assertTrue(is_developer("xylin48"))
            self.assertTrue(is_developer("OTHERDEV"))
            self.assertFalse(is_developer("randomuser"))
            self.assertFalse(is_developer(None))

    def test_client_supplied_flag_cannot_grant_badge(self):
        with patch.dict(os.environ, {"SOCIAL_DEV_USERS": "Xylin48"}):
            self.assertFalse(decorate_identity({"username": "other", "is_dev": True})["is_dev"])
            self.assertTrue(decorate_identity({"username": "Xylin48", "is_dev": False})["is_dev"])

    def test_post_and_repost_badges(self):
        post = {"id": 1, "username": "Xylin48", "is_dev": True,
                "created_at": "2026-11-22", "body": "hello",
                "reposted_by": "OtherDev", "reposted_by_is_dev": True}
        with redirect_stdout(io.StringIO()) as output:
            display([post])
        self.assertIn("@Xylin48 [dev]", output.getvalue())
        self.assertIn("OtherDev [dev] reposted", output.getvalue())

    def test_regular_accounts_have_no_badge(self):
        self.assertEqual(identity("regular"), "regular")
        self.assertEqual(identity("regular", False), "regular")
        self.assertEqual(identity("Xylin48", True), "Xylin48 [dev]")


if __name__ == "__main__":
    unittest.main()
