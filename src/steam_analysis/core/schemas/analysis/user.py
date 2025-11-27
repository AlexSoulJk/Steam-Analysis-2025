from typing import List, Optional
from pydantic import Field
from datetime import datetime

from steam_analysis.core.schemas import PlayerShortInfo
from steam_analysis.core.schemas.base import BaseSchema


class UserAnalysisBase(BaseSchema):
    """Базовые поля юзера"""
    steam_id: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=255)


class UserAnalysisFromJson(UserAnalysisBase):
    created_at: datetime

    @classmethod
    def from_json_resource(cls, json_data: PlayerShortInfo, created_at: datetime) -> "UserAnalysisFromJson":
        """Создать схему из JSON модели"""
        return cls(
            steam_id=json_data.steam_id,
            name=json_data.persona_name,
            created_at=created_at,
        )

    pass


class UserAnalysisCreate(UserAnalysisBase):
    """Создание юзера (обязательно указываем chunk_id)"""
    chunk_id: int = Field(..., ge=1)
    created_at: datetime

    @classmethod
    def from_json_model(cls, json_data: UserAnalysisFromJson, chunk_id: int) -> "UserAnalysisCreate":
        """Создать схему из JSON модели"""
        return cls(
            steam_id=json_data.steam_id,
            name=json_data.name,
            chunk_id=chunk_id,
            created_at=json_data.created_at
        )


class UserAnalysisResponse(BaseSchema):
    id: int = Field(..., ge=1)
    steam_id: int
    status: str = Field(..., pattern="^(pending|in_progress|success|failed|partial|null_state)$")


class UserAnalysisUpdate(BaseSchema):
    """Обновление юзера (только изменяемые поля)"""
    id: int = Field(..., ge=1)
    status: str = Field(..., pattern="^(pending|in_progress|success|failed|particle|null_state)$")
    error_log: Optional[str] = None
    # processed: Optional[bool] = None

    @classmethod
    def from_response_schema(cls, response: UserAnalysisResponse,
                             status: str,
                             error_log: str):
        return cls(id=response.id,
                   status=status,
                   error_log=error_log)


class UserAnalysisChunkCreate(BaseSchema):
    """Создание чанка (БЕЗ списка юзеров)"""
    processed_by: Optional[str] = None
    chunk_size: int = Field(25, ge=1, le=100)
    # user_ids: Optional[List[int]] = None


class UserAnalysisChunkForResponse(BaseSchema):
    id: int = Field(..., ge=1)
    status: str = Field(..., pattern="^(pending|in_progress|success|failed|particle_success)$")
    users: List[UserAnalysisResponse]

    @property
    def get_chunk_steam_ids(self) -> List[int]:
        return list(map(lambda x: x.steam_id, self.users))


class UserAnalysisChunkUpdate(BaseSchema):
    """Обновление чанка"""
    id: int = Field(..., ge=1)
    status: str = Field(..., pattern="^(pending|in_progress|success|failed|particle_success|null_state)$")
    response_time: Optional[float] = None
    error_log: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    @classmethod
    def from_response_schema(cls, response: UserAnalysisChunkForResponse,
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


class UserAnalysisChunkForRequest(BaseSchema):
    chunk_users: List[UserAnalysisUpdate]
    chunk: UserAnalysisChunkUpdate


class UserAnalysisChunkWithUsers(UserAnalysisChunkUpdate):
    """Чанк со списком юзеров (только для чтения)"""
    users: List[UserAnalysisBase] = []
