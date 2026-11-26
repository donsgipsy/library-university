import argparse
import sys

try:  # запуск как пакета: python -m modules.material_catalog.main
    from . import catalog
    from .catalog import CatalogError
except ImportError:  # запуск как скрипта: python main.py
    import catalog
    from catalog import CatalogError


def print_list(items):
    if not items:
        print("Ничего не найдено.")
        return
    for m in items:
        print(f"[{m['id']}] {m['title']}")
        print(f"    Автор: {m['author']} | Дата: {m['published_at']} | Категория: {m['category']}")
        print(f"    {m['description']}")
    print(f"Найдено: {len(items)}")


def print_material(m):
    print("=" * 60)
    print(m["title"])
    print(f"Автор: {m['author']} | Дата: {m['published_at']} | Категория: {m['category']}")
    print("-" * 60)
    print(m["description"])
    print()
    print(m["content"])
    print("=" * 60)


def run_cli(args):
    try:
        if args.command == "list":
            print_list(catalog.get_catalog(args.query, args.category, args.author,
                                           args.date_from, args.date_to))
        else:
            print_material(catalog.get_material(args.id))
        return 0
    except CatalogError as e:
        print(f"Ошибка: {e}")
        return 1


def run_interactive():
    menu = ("\n1 - Все материалы\n2 - Поиск по ключевым словам\n"
            "3 - Фильтры (категория, автор, даты)\n4 - Просмотр материала по id\n0 - Выход")
    while True:
        print(menu)
        choice = input("Выберите пункт: ").strip()
        try:
            if choice == "1":
                print_list(catalog.get_catalog())
            elif choice == "2":
                print_list(catalog.get_catalog(query=input("Ключевые слова: ")))
            elif choice == "3":
                print("Категории:", ", ".join(catalog.get_categories()))
                print_list(catalog.get_catalog(
                    query=input("Ключевые слова (Enter - пропустить): "),
                    category=input("Категория (Enter - пропустить): "),
                    author=input("Автор (Enter - пропустить): "),
                    date_from=input("Дата с, ГГГГ-ММ-ДД (Enter - пропустить): "),
                    date_to=input("Дата по, ГГГГ-ММ-ДД (Enter - пропустить): ")))
            elif choice == "4":
                print_material(catalog.get_material(input("Введите id: ")))
            elif choice == "0":
                return 0
            else:
                print("Неизвестный пункт меню.")
        except CatalogError as e:
            print(f"Ошибка: {e}")


def main():
    if len(sys.argv) == 1:
        return run_interactive()
    parser = argparse.ArgumentParser(description="Каталог материалов")
    sub = parser.add_subparsers(dest="command", required=True)
    p_list = sub.add_parser("list", help="список материалов")
    p_list.add_argument("--query")
    p_list.add_argument("--category")
    p_list.add_argument("--author")
    p_list.add_argument("--from", dest="date_from")
    p_list.add_argument("--to", dest="date_to")
    p_show = sub.add_parser("show", help="полный материал")
    p_show.add_argument("id")
    return run_cli(parser.parse_args())


if __name__ == "__main__":
    sys.exit(main())
