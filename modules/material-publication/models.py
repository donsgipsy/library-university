from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional 
@dataclass
class Material: 
    id: int
    title: str
    content: str 
    description: str 
    category: str 
    files: List[str] = field(default_factory = list)
    status: str = 'draft'
    created_at: str = field(default_factory =lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S") )
    published_at: Optional[str] = None
    def to_dict(self)-> dict: 
        return {
            'id': self.id, 
            'title': self.title, 
            'content': self.content, 
            'description': self.description, 
            'category': self.category, 
            'files': self.files, 
            'status': self.status, 
            'created_at': self.created_at, 
            'published_at': self.published_at,
        }