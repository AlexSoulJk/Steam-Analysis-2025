# schemas/dictionary.py
from typing import Optional

from pydantic import Field

from steam_analysis.core.schemas.base import SteamEntityMixin, BaseSchema


class CategoryBase(SteamEntityMixin):
    """Базовая схема категории"""
    pass


class CategoryCreate(CategoryBase):
    """Схема для создания категории"""
    pass # Steam API использует 'id'


class CategoryUpdate(BaseSchema):
    """Схема для обновления категории"""
    description: Optional[str] = Field(None, max_length=1000)


class CategoryResponse(CategoryBase):
    """Схема ответа для категории"""
    pass


class GenreBase(SteamEntityMixin):
    pass


class GenreCreate(GenreBase):
    pass


class GenreUpdate(BaseSchema):
    description: Optional[str] = None


class GenreResponse(GenreBase):
    pass


class PlatformBase(BaseSchema):
    description: Optional[str] = Field(None, max_length=1000)
    pass


class PlatformCreate(PlatformBase):
    pass

class PlatformUpdate(BaseSchema):
    pass
class PlatformResponse(PlatformBase):
    pass
