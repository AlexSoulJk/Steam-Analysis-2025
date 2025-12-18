from datetime import datetime
from typing import Optional

from pydantic import Field

from steam_analysis.core.schemas.base import BaseSchema, IDMixin


class GameMetricsBase(BaseSchema):
    """Базовые поля метрик (часто меняются)"""
    recommendations_count: int = Field(0, ge=0)
    metacritic_score: Optional[int] = Field(None, ge=0, le=100)
    review_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    review_count: int = Field(0, ge=0)
    peak_players_all_time: int = Field(0, ge=0)


class GameMetricsCreate(GameMetricsBase):
    """DTO для создания метрик"""
    game_id: int = Field(..., ge=1)


class GameMetricsUpdate(GameMetricsBase):
    """DTO для обновления метрик (все поля опциональны)"""
    recommendations_count: Optional[int] = None
    metacritic_score: Optional[int] = None
    review_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    review_count: Optional[int] = Field(0, ge=0)
    peak_players_all_time: Optional[int] = Field(0, ge=0)



class GameMetricsResponse(GameMetricsBase, IDMixin):
    """DTO для чтения метрик"""
    last_updated: datetime
