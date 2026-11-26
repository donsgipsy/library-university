from services import MaterialPublicationService
from validators import ValidationError
def print_material(material):
    print(f'id материала: {material.id}')
    print(f'название: {material.title}')
    print(f"содержание материала: {material.content[:60]}{'...' if len(material.content) > 60 else ''}")
    print(f"описание материала: {material.description or '-'}")
    print(f'категория материала: {material.category}')
    print(f"файлы материала: {', '.join(material.files) if material.files else '-'}")
    print(f'статус: {material.status}')
    print(f'материал создан: {material.created_at}')
    print(f"материал опубликован: {material.published_at or '-'}")
def run():
    print('модуль публикации материалов')
    service = MaterialPublicationService()
    print('создание черновика')
    title = input('введите название материала: ')
    content = input('введите содержание материала: ')
    description = input('введите описание материала (нажмите enter для пропуска): ')
    category = input('введите категорию материала: ')
    files_input = input('введите пути к файлам через запятую (enter для пропуска): ')
    files = [f.strip() for f in files_input.split(',') if f.strip()] if files_input else []
    try:
        material = service.save_draft(title, content, description, category, files)
        print(f'\nчерновик сохранен, id: {material.id}')
        print_material(material)
    except ValidationError as e:
        print(f"{e}")
        return
    print('публикация материала')
    choice = input('опубликовать материал? (y/n): ').strip().lower()
    if choice == 'y':
        try:
            published = service.publish_material(material.id)
            print(f'материал опубликован')
            print_material(published)
        except ValidationError as e:
            print(f"\n{e}")
    else:
        print('материал остался в черновиках')
if __name__ == '__main__':
    run()