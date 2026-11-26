import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import catalog  # noqa: E402
from catalog import (  # noqa: E402
    DataFileError, MaterialNotFound, ValidationError,
)


def make_item(**overrides):
    item = {"id": 1, "title": "Заголовок", "author": "Автор", "published_at": "2026-01-01",
            "category": "Тест", "description": "Описание", "content": "Текст",
            "status": "published"}
    item.update(overrides)
    return item


class TempDataMixin:
    """Создаёт временный JSON-файл с данными для теста."""

    def write_data(self, data, raw=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "materials.json"
        path.write_text(raw if raw is not None else json.dumps(data, ensure_ascii=False),
                        encoding="utf-8")
        return path


class CatalogListTests(unittest.TestCase):
    def test_only_published_materials_are_listed(self):
        ids = [m["id"] for m in catalog.get_catalog()]
        self.assertEqual(sorted(ids), [1, 2, 3, 4, 5])
        self.assertNotIn(6, ids)  # черновик

    def test_sorted_newest_first(self):
        dates = [m["published_at"] for m in catalog.get_catalog()]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_list_item_has_required_fields_without_content(self):
        item = catalog.get_catalog()[0]
        self.assertEqual(set(item), {"id", "title", "author", "published_at",
                                     "category", "description"})


class SearchTests(unittest.TestCase):
    def test_single_keyword(self):
        titles = [m["title"] for m in catalog.get_catalog(query="sql")]
        self.assertEqual(titles, ["Основы SQL для начинающих"])

    def test_case_insensitive(self):
        self.assertEqual(catalog.get_catalog(query="PYTHON"), catalog.get_catalog(query="python"))

    def test_all_words_must_match(self):
        self.assertEqual(len(catalog.get_catalog(query="данных python")), 1)
        self.assertEqual(catalog.get_catalog(query="sql python"), [])

    def test_searches_in_content(self):
        self.assertEqual([m["id"] for m in catalog.get_catalog(query="нормальной формы")], [5])

    def test_empty_or_none_query_returns_all(self):
        self.assertEqual(len(catalog.get_catalog(query="")), 5)
        self.assertEqual(len(catalog.get_catalog(query=None)), 5)
        self.assertEqual(len(catalog.get_catalog(query="   ")), 5)

    def test_no_match_returns_empty_list(self):
        self.assertEqual(catalog.get_catalog(query="несуществующееслово"), [])

    def test_draft_is_not_found_by_search(self):
        self.assertEqual(catalog.get_catalog(query="Машинное обучение"), [])


class FilterTests(unittest.TestCase):
    def test_by_category(self):
        self.assertEqual(sorted(m["id"] for m in catalog.get_catalog(category="Аналитика")), [1, 4])

    def test_category_is_case_insensitive(self):
        self.assertEqual(len(catalog.get_catalog(category="аналитика")), 2)

    def test_by_author_partial(self):
        self.assertEqual(sorted(m["id"] for m in catalog.get_catalog(author="иванов")), [2, 3])

    def test_date_range_inclusive_boundaries(self):
        result = catalog.get_catalog(date_from="2026-10-20", date_to="2026-10-20")
        self.assertEqual([m["id"] for m in result], [4])

    def test_only_date_from(self):
        self.assertEqual([m["id"] for m in catalog.get_catalog(date_from="2026-10-20")], [5, 4])

    def test_only_date_to(self):
        self.assertEqual([m["id"] for m in catalog.get_catalog(date_to="2026-09-01")], [1])

    def test_combined_filters_and_search(self):
        result = catalog.get_catalog(query="данных", category="Аналитика", author="Филимонова",
                                     date_from="2026-09-01", date_to="2026-10-31")
        self.assertEqual(sorted(m["id"] for m in result), [1, 4])

    def test_empty_strings_are_ignored(self):
        self.assertEqual(len(catalog.get_catalog(category="", author="", date_from="", date_to="")), 5)

    def test_unknown_category_returns_empty(self):
        self.assertEqual(catalog.get_catalog(category="Нет такой"), [])

    def test_wrong_date_format(self):
        for bad in ("2026-13-01", "01.01.2026", "2026-1-1", "abc", "20261020"):
            with self.subTest(value=bad):
                with self.assertRaises(ValidationError):
                    catalog.get_catalog(date_from=bad)

    def test_date_from_after_date_to(self):
        with self.assertRaises(ValidationError):
            catalog.get_catalog(date_from="2026-12-01", date_to="2026-01-01")


class GetMaterialTests(unittest.TestCase):
    def test_full_material(self):
        m = catalog.get_material(3)
        self.assertEqual(m["title"], "Python: работа с файлами")
        self.assertIn("content", m)

    def test_id_as_string(self):
        self.assertEqual(catalog.get_material("3")["id"], 3)

    def test_not_found(self):
        with self.assertRaises(MaterialNotFound):
            catalog.get_material(999)

    def test_draft_is_not_available(self):
        with self.assertRaises(MaterialNotFound):
            catalog.get_material(6)

    def test_invalid_id(self):
        for bad in ("abc", None, "", "1.5", True):
            with self.subTest(value=bad):
                with self.assertRaises(ValidationError):
                    catalog.get_material(bad)

    def test_returned_dict_is_a_copy(self):
        m = catalog.get_material(1)
        m["title"] = "Изменено"
        self.assertNotEqual(catalog.get_material(1)["title"], "Изменено")


class SummaryAndCategoriesTests(unittest.TestCase):
    def test_summary_for_bookmarks(self):
        s = catalog.get_material_summary(2)
        self.assertEqual(set(s), {"id", "title", "author", "description"})
        self.assertEqual(s["author"], "Иванов Пётр")

    def test_summary_not_found(self):
        with self.assertRaises(MaterialNotFound):
            catalog.get_material_summary(999)

    def test_categories_only_from_published(self):
        self.assertEqual(catalog.get_categories(),
                         ["Аналитика", "Базы данных", "Программирование"])


class DataValidationTests(TempDataMixin, unittest.TestCase):
    def test_valid_file_is_loaded(self):
        path = self.write_data([make_item()])
        self.assertEqual(len(catalog.get_catalog(path=path)), 1)

    def test_empty_list_is_valid(self):
        path = self.write_data([])
        self.assertEqual(catalog.get_catalog(path=path), [])

    def test_missing_file(self):
        with self.assertRaises(DataFileError):
            catalog.load_materials(Path("нет_такого_файла.json"))

    def test_broken_json(self):
        path = self.write_data(None, raw="{ не json")
        with self.assertRaises(DataFileError):
            catalog.load_materials(path)

    def test_not_a_list(self):
        path = self.write_data({"id": 1})
        with self.assertRaises(DataFileError):
            catalog.load_materials(path)

    def test_item_is_not_an_object(self):
        path = self.write_data(["строка"])
        with self.assertRaises(DataFileError):
            catalog.load_materials(path)

    def test_missing_field(self):
        item = make_item()
        del item["author"]
        with self.assertRaises(DataFileError):
            catalog.load_materials(self.write_data([item]))

    def test_invalid_field_values(self):
        cases = {
            "id строкой": {"id": "1"},
            "id логический": {"id": True},
            "пустое название": {"title": "   "},
            "название не строка": {"title": 5},
            "пустой автор": {"author": ""},
            "пустая категория": {"category": ""},
            "описание не строка": {"description": None},
            "дата неверного формата": {"published_at": "01.01.2026"},
            "несуществующая дата": {"published_at": "2026-02-30"},
            "дата не строка": {"published_at": 20260101},
            "неизвестный статус": {"status": "archived"},
        }
        for name, override in cases.items():
            with self.subTest(case=name):
                path = self.write_data([make_item(**override)])
                with self.assertRaises(DataFileError):
                    catalog.load_materials(path)

    def test_duplicate_ids(self):
        path = self.write_data([make_item(id=1), make_item(id=1, title="Другой")])
        with self.assertRaises(DataFileError):
            catalog.load_materials(path)

    def test_error_is_raised_from_public_functions(self):
        path = self.write_data([make_item(status="archived")])
        with self.assertRaises(DataFileError):
            catalog.get_catalog(path=path)
        with self.assertRaises(DataFileError):
            catalog.get_material(1, path=path)


if __name__ == "__main__":
    unittest.main()
