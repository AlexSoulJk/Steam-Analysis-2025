from typing import List, Optional
from pydantic import Field, validator
from datetime import datetime

from steam_analysis.core.schemas import GameShortInfo
from steam_analysis.core.schemas.base import BaseSchema


class GameAnalysisBase(BaseSchema):
    """Базовые поля игры"""
    app_id: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=255)


class GameAnalysisFromJson(GameAnalysisBase):
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


class GameAnalysisResponse(BaseSchema):
    id: int = Field(..., ge=1)
    app_id: int
    status: str = Field(..., pattern="^(pending|in_progress|success|failed|particle|null_state)$")


class GameAnalysisUpdate(BaseSchema):
    """Обновление игры (только меняемые поля)"""
    id: int = Field(..., ge=1)
    status: str = Field(..., pattern="^(pending|in_progress|success|failed|particle|null_state)$")
    error_log: Optional[str] = None
    # processed: Optional[bool] = None

    @classmethod
    def from_response_schema(cls, response: GameAnalysisResponse,
                             status: str,
                             error_log: str):
        return cls(id=response.id,
                   status=status,
                   error_log=error_log)


class GameAnalysisChunkCreate(BaseSchema):
    """Создание чанка (БЕЗ списка игр)"""
    processed_by: Optional[str] = None
    # games создаются отдельно!


class GameAnalysisChunkForResponse(BaseSchema):
    id: int = Field(..., ge=1)
    status: str = Field(..., pattern="^(pending|in_progress|success|failed|particle_success)$") # TODO: Возможно тут можно сделать логику того, что валиадация по стейтам защищается и проверяется на уровне схемы
    games: List[GameAnalysisResponse]

    @property
    def get_chunk_app_ids(self) -> List[int]:
        return list(map(lambda x: x.app_id, self.games))


class GameAnalysisChunkUpdate(BaseSchema):
    """Обновление чанка"""
    id: int = Field(..., ge=1)
    status: str = Field(..., pattern="^(pending|in_progress|success|failed|particle_success|null_state)$")
    response_time: Optional[float] = None
    error_log: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    @classmethod
    def from_response_schema(cls, response: GameAnalysisChunkForResponse,
                             response_time: float,
                             error_log: str,
                             started_at: datetime,
                             finished_at: datetime,
                             status: str):
        return cls(id=response.id,
                   status=status,
                   response_time=response_time,
                   error_log=error_log,
                   started_at=started_at,
                   finished_at=finished_at)


class GameAnalysisChunkForRequest(BaseSchema):
    chunk_games: List[GameAnalysisUpdate]
    chunk: GameAnalysisChunkUpdate


# ДОПОЛНИТЕЛЬНО: схема для ответа с играми
class GameAnalysisChunkWithGames(GameAnalysisChunkUpdate):
    """Чанк со списком игр (только для чтения)"""
    games: List[GameAnalysisBase] = []
