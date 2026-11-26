from typing import Dict, List, Optional
from models import Material
from validators import MaterialValidator, ValidationError
class MaterialPublicationService:
    def __init__(self):
        self._materials: Dict[int, Material] = {}
        self._next_id: int = 1
    def save_draft(
        self,
        title: str,
        content: str,
        description: str,
        category: str,
        files: Optional[List[str]] = None,
    ) -> Material:
        MaterialValidator.validate_fields(title, content, category)
        MaterialValidator.validate_files(files or [])
        material = Material(
            id=self._next_id,
            title=title.strip(),
            content=content.strip(),
            description=description.strip() if description else '',
            category=category.strip(),
            status='draft'
        )
        self._materials[material.id] = material
        self._next_id += 1
        return material
    def publish_material(self, material_id: int) -> Material:
        if material_id not in self._materials:
            raise ValidationError(f'ошибка: материал с ID {material_id} не найден:(')
        material = self._materials[material_id]
        if material.status == 'published':
            raise ValidationError('ошибка: материал уже опубликован')
        from datetime import datetime
        material.status = 'published'
        material.published_at = datetime.now()
        return material
    def get_material(self, material_id: int) -> Optional[Material]:
        return self._materials.get(material_id)
    def get_all_materials(self) -> List[Material]:
        return list(self._materials.values())