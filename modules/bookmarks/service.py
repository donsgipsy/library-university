
from repository import BookmarkRepository


class BookmarksService:
    def __init__(self, repository: BookmarkRepository):
        self.repository = repository

    def add_bookmark(self, user_id, material_id):
        if not isinstance(user_id, int) or isinstance(user_id, bool):
            raise ValueError("ID пользователя должен быть целым числом")

        if user_id <= 0:
            raise ValueError("ID пользователя должен быть положительным")

        if not isinstance(material_id, int) or isinstance(material_id, bool):
            raise ValueError("ID материала должен быть целым числом")

        if material_id <= 0:
            raise ValueError("ID материала должен быть положительным")

        if self.repository.exists(user_id, material_id):
            raise ValueError("Закладка уже существует")

        self.repository.add(user_id, material_id)

    def get_user_bookmarks(self, user_id):
        if not isinstance(user_id, int) or isinstance(user_id, bool):
            raise ValueError("ID пользователя должен быть целым числом")

        if user_id <= 0:
            raise ValueError("ID пользователя должен быть положительным")

        return self.repository.get_user_id(user_id)

    def remove_bookmark(self, user_id, material_id):
        if not isinstance(user_id, int) or isinstance(user_id, bool):
            raise ValueError("ID пользователя должен быть целым числом")

        if user_id <= 0:
            raise ValueError("ID пользователя должен быть положительным")

        if not isinstance(material_id, int) or isinstance(material_id, bool):
            raise ValueError("ID материала должен быть целым числом")

        if material_id <= 0:
            raise ValueError("ID материала должен быть положительным")

        if not self.repository.remove(user_id, material_id):
            raise ValueError("Закладка не найдена")
