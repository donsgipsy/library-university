from model import Bookmark

class BookmarkRepository:
    def __init__(self, connection):
        self.connection = connection

    def add(self, user_id, material_id):
        cursor = self.connection.cursor()

        cursor.execute(
            """
            INSERT INTO bookmarks (user_id, material_id)
            VALUES (?, ?)
            """,
            (user_id, material_id)
        )

        self.connection.commit()


    def get_user_id(self, user_id):
        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT id, user_id, material_id
            FROM bookmarks
            WHERE user_id = ?
            """,
            (user_id,)
        )

        rows = cursor.fetchall()

        return [
            Bookmark(id, user_id, material_id)
            for id, user_id, material_id in rows
        ]


    def exists(self, user_id, material_id):
        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT EXISTS(
                SELECT 1 FROM bookmarks
                WHERE user_id = ? AND material_id = ?
            )
            """,
            (user_id, material_id)
        )

        return cursor.fetchone()[0] == 1

    def remove(self, user_id, material_id):
        cursor = self.connection.cursor()

        cursor.execute(
            """
            DELETE FROM bookmarks
            WHERE user_id = ? AND material_id = ?
            """,
            (user_id, material_id)
        )

        self.connection.commit()

        return cursor.rowcount > 0
