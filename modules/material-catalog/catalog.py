import json
import re
from datetime import date
from pathlib import Path

DEFAULT_DATA_FILE = Path(__file__).with_name("materials.json")
PUBLISHED = "published"
DRAFT = "draft"
ALLOWED_STATUSES = (PUBLISHED, DRAFT)
REQUIRED_FIELDS = ("id", "title", "author", "published_at",
                   "category", "description", "content", "status")
NON_EMPTY_TEXT_FIELDS = ("title", "author", "category")
TEXT_FIELDS = ("description", "content")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class CatalogError(Exception):
    """Базовая ошибка каталога."""


class DataFileError(CatalogError):
    """Файл данных отсутствует, повреждён или содержит некорректные значения."""


class ValidationError(CatalogError):
    """Некорректные параметры запроса."""


class MaterialNotFound(CatalogError):
    """Материал не найден или не опубликован."""


def _parse_iso_date(value):
    """Строго ГГГГ-ММ-ДД -> date. При ошибке — ValueError."""
    text = str(value).strip()
    if not _DATE_RE.match(text):
        raise ValueError(text)
    return date.fromisoformat(text)


def parse_date(value, field_name="дата"):
    """Преобразует строку ГГГГ-ММ-ДД в date. None и '' -> None."""
    if value is None or str(value).strip() == "":
        return None
    try:
        return _parse_iso_date(value)
    except ValueError:
        raise ValidationError(
            f"Некорректная {field_name}: '{value}'. Ожидается формат ГГГГ-ММ-ДД."
        ) from None


def _validate_material(item, index):
    """Проверяет структуру, типы и значения полей одного материала."""
    if not isinstance(item, dict):
        raise DataFileError(f"Элемент №{index} должен быть объектом.")
    missing = [k for k in REQUIRED_FIELDS if k not in item]
    if missing:
        raise DataFileError(
            f"У материала №{index} нет полей: {', '.join(missing)}")

    label = f"У материала №{index}"
    if not isinstance(item["id"], int) or isinstance(item["id"], bool):
        raise DataFileError(f"{label}: id должен быть целым числом.")
    for field in NON_EMPTY_TEXT_FIELDS:
        if not isinstance(item[field], str) or not item[field].strip():
            raise DataFileError(f"{label}: поле '{field}' должно быть непустой строкой.")
    for field in TEXT_FIELDS:
        if not isinstance(item[field], str):
            raise DataFileError(f"{label}: поле '{field}' должно быть строкой.")
    if not isinstance(item["published_at"], str):
        raise DataFileError(f"{label}: дата публикации должна быть строкой ГГГГ-ММ-ДД.")
    try:
        _parse_iso_date(item["published_at"])
    except ValueError:
        raise DataFileError(
            f"{label}: некорректная дата публикации '{item['published_at']}'."
        ) from None
    if item["status"] not in ALLOWED_STATUSES:
        raise DataFileError(
            f"{label}: статус должен быть одним из {ALLOWED_STATUSES}.")


def load_materials(path=DEFAULT_DATA_FILE):
    """Читает все материалы из JSON-файла и проверяет их структуру и значения."""
    try:
        with open(path, encoding="utf-8") as f:
            items = json.load(f)
    except FileNotFoundError:
        raise DataFileError(f"Файл данных не найден: {path}") from None
    except json.JSONDecodeError as e:
        raise DataFileError(f"Файл данных повреждён: {e}") from None

    if not isinstance(items, list):
        raise DataFileError("Файл данных должен содержать список материалов.")
    seen_ids = set()
    for index, item in enumerate(items, start=1):
        _validate_material(item, index)
        if item["id"] in seen_ids:
            raise DataFileError(f"Повторяющийся id материала: {item['id']}.")
        seen_ids.add(item["id"])
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
    if isinstance(material_id, bool):
        raise ValidationError("Идентификатор должен быть целым числом.")
    try:
        material_id = int(material_id)
    except (TypeError, ValueError):
        raise ValidationError("Идентификатор должен быть целым числом.") from None
    for m in get_published(load_materials(path)):
        if m["id"] == material_id:
            return dict(m)
    raise MaterialNotFound(f"Материал с id={material_id} не найден.")


def get_material_summary(material_id, path=DEFAULT_DATA_FILE):
    """Название, автор и описание материала по ID.

    Предназначена для других модулей, например для списка закладок:
    возвращает {'id', 'title', 'author', 'description'}.
    """
    m = get_material(material_id, path)
    return {k: m[k] for k in ("id", "title", "author", "description")}


def get_categories(path=DEFAULT_DATA_FILE):
    """Список категорий опубликованных материалов (для подсказки в меню)."""
    return sorted({m["category"] for m in get_published(load_materials(path))})
