from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, Text,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from .base import BaseModel


class PlayerCountHistory(BaseModel):
    """История онлайна игроков (улучшенная)"""
    __tablename__ = "player_count_history"

    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    player_count = Column(Integer, nullable=False)
    # Дополнительные метрики
    twitch_viewers = Column(Integer)  # Количество зрителей на Twitch
    trend_24h = Column(Float)  # Изменение за 24 часа в %

    game = relationship("Game", back_populates="player_counts")

    __table_args__ = (
        Index('idx_player_history_game', 'game_id'),
        Index('idx_player_history_date', 'created_at'),
        Index('idx_player_history_game_date', 'game_id', 'created_at'),
    )


class PriceHistory(BaseModel):
    """История цен (улучшенная)"""
    __tablename__ = "price_history"

    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    currency = Column(String(3), default='USD', nullable=False)
    price_final = Column(Integer)  # в центах
    price_initial = Column(Integer)  # исходная цена в центах
    discount_percent = Column(Integer, default=0)
    # Дополнительные поля
    price_original = Column(Integer)  # цена до скидки
    purchase_available = Column(Boolean, default=True)
    package_id = Column(Integer)  # ID пакета, если применимо

    game = relationship("Game", back_populates="prices")

    __table_args__ = (
        Index('idx_price_history_game', 'game_id'),
        Index('idx_price_history_date', 'created_at'),
        Index('idx_price_history_currency', 'currency'),
        Index('idx_price_history_game_date', 'game_id', 'created_at'),
    )


class ReviewHistory(BaseModel):
    """История отзывов (временной ряд)"""
    __tablename__ = "review_history"

    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    review_score = Column(Float)  # 0.0-1.0
    review_count = Column(Integer, default=0)
    positive_reviews = Column(Integer, default=0)
    negative_reviews = Column(Integer, default=0)

    game = relationship("Game")

    __table_args__ = (
        Index('idx_review_history_game', 'game_id'),
        Index('idx_review_history_date', 'created_at'),
        Index('idx_review_history_game_date', 'game_id', 'created_at'),
    )