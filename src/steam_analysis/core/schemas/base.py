# schemas/base.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class BaseSchema(BaseModel):
    """Базовая схема с общими настройками"""
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class TimestampMixin(BaseSchema):
    """Миксин для временных меток"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class IDMixin(BaseSchema):
    """Миксин для ID"""
    id: Optional[int] = Field(None, description="ID записи")

class SteamEntityMixin(BaseSchema):
    """Миксин для Steam сущностей"""
    steam_id: int = Field(..., description="ID в Steam API", alias="id")
    description: Optional[str] = Field(None, max_length=1000)
