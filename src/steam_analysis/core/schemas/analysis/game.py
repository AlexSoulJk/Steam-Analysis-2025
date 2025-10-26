from typing import List, Optional
from pydantic import Field, validator
from datetime import datetime

from steam_analysis.core.schemas import GameShortInfo
from steam_analysis.core.schemas.base import BaseSchema


class GameAnalysisBase(BaseSchema):
    """Базовые поля игры"""
    app_id: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=255)


class GameAnalysisFromJson(BaseSchema):
    created_at: datetime

    @classmethod
    def from_json_resource(cls, json_data: GameShortInfo, created_at: datetime) -> "GameAnalysisFromJson":
        """Создать схему из JSON модели"""
        return cls(
            app_id=json_data.app_id,
            name=json_data.name,
            created_at=created_at,
        )

    pass


class GameAnalysisCreate(GameAnalysisBase):
    """Создание игры (обязательно указываем chunk_id)"""
    chunk_id: int = Field(..., ge=1)
    created_at: datetime
    @classmethod
    def from_json_model(cls, json_data: GameAnalysisFromJson, chunk_id: int) -> "GameAnalysisCreate":
        """Создать схему из JSON модели"""
        return cls(
            app_id=json_data.app_id,
            name=json_data.name,
            chunk_id=chunk_id,
            created_at=json_data.created_at
        )



class GameAnalysisUpdate(BaseSchema):
    """Обновление игры (только меняемые поля)"""
    id: int = Field(..., ge=1)
    status: str = Field(..., pattern="^(pending|in_progress|success|failed|partial|null_state)$")
    error_log: Optional[str] = None
    processed: Optional[bool] = None
    response_time: Optional[float] = None


class GameAnalysisChunkCreate(BaseSchema):
    """Создание чанка (БЕЗ списка игр)"""
    processed_by: Optional[str] = None
    # games создаются отдельно!


class GameAnalysisChunkUpdate(BaseSchema):
    """Обновление чанка"""
    id: int = Field(..., ge=1)
    status: str = Field(..., pattern="^(pending|in_progress|success|failed|partial_success)$")
    response_time: Optional[float] = None
    error_log: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


# ДОПОЛНИТЕЛЬНО: схема для ответа с играми
class GameAnalysisChunkWithGames(GameAnalysisChunkUpdate):
    """Чанк со списком игр (только для чтения)"""
    games: List[GameAnalysisBase] = []
