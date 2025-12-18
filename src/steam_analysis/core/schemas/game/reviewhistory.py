# schemas/review_history.py
from pydantic import BaseModel, ConfigDict, Field, field_validator, computed_field
from typing import Optional, List, Dict, Any
from datetime import datetime, date


class ReviewHistoryBase(BaseModel):
    """Базовая схема истории отзывов"""
    game_id: int = Field(..., ge=1, description="ID игры")
    review_score: float = Field(..., ge=0.0, le=1.0, description="Оценка отзывов (0.0-1.0)")
    review_count: int = Field(default=0, ge=0, description="Общее количество отзывов")
    positive_reviews: int = Field(default=0, ge=0, description="Количество положительных отзывов")
    negative_reviews: int = Field(default=0, ge=0, description="Количество отрицательных отзывов")


class ReviewHistoryCreate(ReviewHistoryBase):
    """Схема для создания записи истории отзывов"""
    pass


class ReviewHistoryUpdate(BaseModel):
    """Схема для обновления записи истории отзывов"""
    review_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    review_count: Optional[int] = Field(None, ge=0)
    positive_reviews: Optional[int] = Field(None, ge=0)
    negative_reviews: Optional[int] = Field(None, ge=0)


class ReviewTrend(BaseModel):
    """Схема тренда отзывов"""
    trend: str  # 'improving', 'declining', 'stable', 'no_data'
    first_record: Dict[str, Any]
    last_record: Dict[str, Any]
    changes: Dict[str, Any]
    period_days: int


class GameReviewTrend(BaseModel):
    """Схема тренда отзывов для игры"""
    game_id: int
    first_score: float
    last_score: float
    improvement: Optional[float] = None
    decline: Optional[float] = None
    improvement_percent: Optional[float] = None
    decline_percent: Optional[float] = None
    first_total: int
    last_total: int
    review_growth: int



class DailyReviewSummary(BaseModel):
    """Схема дневной сводки по отзывам"""
    date: date
    total_entries: int
    total_reviews: int
    avg_score: float
    total_positive: int
    total_negative: int
    positive_ratio: float



class ReviewHistoryStats(BaseModel):
    """Статистика по истории отзывов"""
    total_records: int
    games_tracked: int
    avg_review_score: float
    total_reviews_tracked: int
    date_range: Dict[str, datetime]
    recent_activity: Dict[str, int]  # Записи за последние 7 дней

