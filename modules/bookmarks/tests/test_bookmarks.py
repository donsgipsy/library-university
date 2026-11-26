
import unittest
import sqlite3

from repository import BookmarkRepository
from service import BookmarksService


class TestBookmarksService(unittest.TestCase):

    def setUp(self):
        # Создаём временную базу в памяти
        self.connection = sqlite3.connect(":memory:")

        self.connection.execute("""
            CREATE TABLE bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                material_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, material_id)
            )
        """)

        self.repository = BookmarkRepository(self.connection)
        self.service = BookmarksService(self.repository)

    def tearDown(self):
        self.connection.close()

    def test_add_bookmark(self):
        self.service.add_bookmark(1, 10)

        bookmarks = self.service.get_user_bookmarks(1)

        self.assertEqual(len(bookmarks), 1)
        self.assertEqual(bookmarks[0].user_id, 1)
        self.assertEqual(bookmarks[0].material_id, 10)

    def test_add_duplicate_bookmark(self):
        self.service.add_bookmark(1, 10)

        with self.assertRaises(ValueError):
            self.service.add_bookmark(1, 10)

    def test_get_user_bookmarks(self):
        self.service.add_bookmark(1, 10)
        self.service.add_bookmark(1, 20)
        self.service.add_bookmark(2, 30)

        bookmarks = self.service.get_user_bookmarks(1)

        self.assertEqual(len(bookmarks), 2)

        material_ids = [bookmark.material_id for bookmark in bookmarks]

        self.assertEqual(material_ids, [10, 20])

    def test_get_empty_bookmarks(self):
        bookmarks = self.service.get_user_bookmarks(1)

        self.assertEqual(bookmarks, [])

    def test_remove_bookmark(self):
        self.service.add_bookmark(1, 10)

        self.service.remove_bookmark(1, 10)

        bookmarks = self.service.get_user_bookmarks(1)

        self.assertEqual(bookmarks, [])

    def test_remove_nonexistent_bookmark(self):
        with self.assertRaises(ValueError):
            self.service.remove_bookmark(1, 10)

    def test_invalid_user_id(self):
        with self.assertRaises(ValueError):
            self.service.add_bookmark(-1, 10)

        with self.assertRaises(ValueError):
            self.service.add_bookmark("1", 10)

        with self.assertRaises(ValueError):
            self.service.add_bookmark(True, 10)

    def test_invalid_material_id(self):
        with self.assertRaises(ValueError):
            self.service.add_bookmark(1, -10)

        with self.assertRaises(ValueError):
            self.service.add_bookmark(1, "10")

        with self.assertRaises(ValueError):
            self.service.add_bookmark(1, True)


if __name__ == "__main__":
    unittest.main()
