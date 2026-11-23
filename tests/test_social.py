import tempfile
import unittest
from pathlib import Path
from legacy.social import connect, register, authenticate, create_post, feed


class SocialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.temp.name) / 'social.db')

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_accounts(self):
        register(self.db, 'Alice', 'password123')
        self.assertEqual(authenticate(self.db, 'alice', 'password123'), 'Alice')
        self.assertIsNone(authenticate(self.db, 'Alice', 'wrongpassword'))
        with self.assertRaises(ValueError):
            register(self.db, 'ALICE', 'password123')

    def test_posts_persist(self):
        register(self.db, 'Alice', 'password123')
        create_post(self.db, 'Alice', 'Hello, Social!')
        self.assertEqual(feed(self.db)[0][2], 'Hello, Social!')
        with self.assertRaises(ValueError):
            create_post(self.db, 'Alice', '')


if __name__ == '__main__':
    unittest.main()
