import json
from datetime import date
from pathlib import Path

DEFAULT_DATA_FILE = Path(__file__).with_name("materials.json")
PUBLISHED = "published"
REQUIRED_FIELDS = ("id", "title", "author", "published_at",
                   "category", "description", "content", "status")


class CatalogError(Exception):
    """Базовая ошибка каталога."""


class DataFileError(CatalogError):
    """Файл данных отсутствует или повреждён."""


class ValidationError(CatalogError):
    """Некорректные параметры запроса."""


class MaterialNotFound(CatalogError):
    """Материал не найден или не опубликован."""


def parse_date(value, field_name="дата"):
    """Преобразует строку ГГГГ-ММ-ДД в date. None и '' -> None."""
    if value is None or str(value).strip() == "":
        return None
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError:
        raise ValidationError(
            f"Некорректная {field_name}: '{value}'. Ожидается формат ГГГГ-ММ-ДД."
        ) from None


def load_materials(path=DEFAULT_DATA_FILE):
    """Читает все материалы из JSON-файла и проверяет их структуру."""
    try:
        with open(path, encoding="utf-8") as f:
            items = json.load(f)
    except FileNotFoundError:
        raise DataFileError(f"Файл данных не найден: {path}") from None
    except json.JSONDecodeError as e:
        raise DataFileError(f"Файл данных повреждён: {e}") from None

    if not isinstance(items, list):
        raise DataFileError("Файл данных должен содержать список материалов.")
    for item in items:
        missing = [k for k in REQUIRED_FIELDS if k not in item]
        if missing:
            raise DataFileError(
                f"У материала {item.get('id', '?')} нет полей: {', '.join(missing)}"
            )
    return items


def get_published(materials):
    """Возвращает только опубликованные материалы."""
    return [m for m in materials if m["status"] == PUBLISHED]


def to_list_item(material):
    """Краткое представление для списка (без полного текста)."""
    return {k: material[k] for k in
            ("id", "title", "author", "published_at", "category", "description")}


def search_materials(query, materials):
    """Поиск по ключевым словам (без учёта регистра).

    Материал подходит, если КАЖДОЕ слово запроса встречается в названии,
    описании, авторе или тексте.
    """
    words = (query or "").lower().split()
    if not words:
        return list(materials)
    result = []
    for m in materials:
        haystack = " ".join(
            (m["title"], m["description"], m["author"], m["content"])
        ).lower()
        if all(w in haystack for w in words):
            result.append(m)
    return result


def filter_materials(materials, category=None, author=None,
                     date_from=None, date_to=None):
    """Фильтрация по категории, автору и диапазону дат (границы включены)."""
    d_from = parse_date(date_from, "дата начала")
    d_to = parse_date(date_to, "дата окончания")
    if d_from and d_to and d_from > d_to:
        raise ValidationError("Дата начала не может быть позже даты окончания.")

    category = (category or "").strip().lower()
    author = (author or "").strip().lower()
    result = []
    for m in materials:
        if category and m["category"].lower() != category:
            continue
        if author and author not in m["author"].lower():
            continue
        published = date.fromisoformat(m["published_at"])
        if d_from and published < d_from:
            continue
        if d_to and published > d_to:
            continue
        result.append(m)
    return result


def get_catalog(query=None, category=None, author=None,
                date_from=None, date_to=None, path=DEFAULT_DATA_FILE):
    """Главная функция: список опубликованных материалов с поиском и фильтрами.

    Сначала фильтры, затем поиск; новые материалы идут первыми.
    """
    materials = get_published(load_materials(path))
    materials = filter_materials(materials, category, author, date_from, date_to)
    materials = search_materials(query, materials)
    materials.sort(key=lambda m: m["published_at"], reverse=True)
    return [to_list_item(m) for m in materials]


def get_material(material_id, path=DEFAULT_DATA_FILE):
    """Полный материал по идентификатору."""
    try:
        material_id = int(material_id)
    except (TypeError, ValueError):
        raise ValidationError("Идентификатор должен быть целым числом.") from None
    for m in get_published(load_materials(path)):
        if m["id"] == material_id:
            return dict(m)
    raise MaterialNotFound(f"Материал с id={material_id} не найден.")


def get_categories(path=DEFAULT_DATA_FILE):
    """Список категорий опубликованных материалов (для подсказки в меню)."""
    return sorted({m["category"] for m in get_published(load_materials(path))})
