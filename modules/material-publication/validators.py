import os 
class ValidationError(Exception): 
    pass 
class MaterialValidator: 
    allowed_extensions = {'pdf', 'docx', 'pptx', 'xlsx', 'png', 'jpg', 'zip'}
    max_file_size = 50*1024*1024 
    @staticmethod 
    def validate_fields(title: str, content: str, category: str)-> None: 
        if not title or not title.strip(): 
            raise ValidationError('ошибка: заполните название материала')
        if not content or not content.strip(): 
            raise ValidationError('ошибка: заполните содержание материала')
        if not category or not category.strip(): 
            raise ValidationError('ошибка: заполните категорию материала')
    @classmethod 
    def validate_files(cls, file_paths: list[str])-> None: 
        if not file_paths: 
            return 
        for file_path in file_paths: 
            if not os.path.exists(file_path): 
                raise ValidationError(f'ошибка: файл {file_path} не найден:(')
            ext= file_path.rsplit('.', 1)[-1].lower()
            if ext not in cls.allowed_extensions: 
                raise ValidationError(
                    f'ошибка: недопустимый формат файла {ext}'
                    f'допустимые форматы: {','.join(sorted(cls.allowed_extensions))}'
                )
            size = os.path.getsize(file_path)
            if size> cls.max_file_size: 
                raise ValidationError(
                    f'ошибка: неподходящий размер файла {size} '
                    f'файл должен весить не более 50 мб'
                    f'текущий размер {size/1024/1024} мб'
                )
                


