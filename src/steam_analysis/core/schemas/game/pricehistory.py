from datetime import datetime

from pydantic import Field

from steam_analysis.core.schemas.base import BaseSchema, IDMixin


class PriceHistoryBase(BaseSchema):
    """Базовые поля цены (очень часто меняются)"""
    currency: str = Field("USD", min_length=3, max_length=3)
    price_final: int = Field(0, ge=0)
    discount_percent: int = Field(0, ge=0, le=100)
    initial: int = Field(0)


class PriceHistoryCreate(PriceHistoryBase):
    """DTO для создания записи цены"""
    game_id: int = Field(..., ge=1)


class PriceHistoryResponse(PriceHistoryBase, IDMixin):
    """DTO для чтения цены"""
    recorded_at: datetime
