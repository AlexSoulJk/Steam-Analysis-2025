from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, Text,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from .base import BaseModel


class PlayerCountHistory(BaseModel):
    """История онлайна игроков"""
    __tablename__ = "player_count_history"

    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    player_count = Column(Integer, nullable=False)
    month =  Column(String(10))
    avg_players = Column(Float)
    percent_gain = Column(Float)
    gain = Column(Float)

    game = relationship("Game", back_populates="player_counts")

    __table_args__ = (
        Index('idx_player_history_game', 'game_id'),
        Index('idx_player_history_date', 'created_at'),
        Index('idx_player_history_game_date', 'game_id', 'created_at'),
    )


class PriceHistory(BaseModel):
    """История цен"""
    __tablename__ = "price_history"

    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    currency = Column(String(3), default='USD', nullable=False)
    price_final= Column(Integer)
    price_initial = Column(Integer)
    discount_percent = Column(Integer, default=0)

    game = relationship("Game", back_populates="prices")

    __table_args__ = (
        Index('idx_price_history_game', 'game_id'),
        Index('idx_price_history_date', 'created_at'),
        Index('idx_price_history_currency', 'currency'),
        Index('idx_price_history_game_date', 'game_id', 'created_at'),
    )


class ReviewHistory(BaseModel):
    """История отзывов"""
    __tablename__ = "review_history"

    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    review_score = Column(Float)  # 0.0-1.0
    review_count = Column(Integer, default=0)
    positive_reviews = Column(Integer, default=0)
    negative_reviews = Column(Integer, default=0)

    game = relationship("Game", back_populates="review_history")

    __table_args__ = (
        Index('idx_review_history_game', 'game_id'),
        Index('idx_review_history_date', 'created_at'),
        Index('idx_review_history_game_date', 'game_id', 'created_at'),
    )


class AchievementHistory(BaseModel):
    """История изменения статистики достижений"""
    __tablename__ = "achievement_history"

    achievement_id = Column(Integer, ForeignKey('achievements.id', ondelete='CASCADE'), nullable=False)
    global_achievement_rate = Column(Float, nullable=False)

    achievement = relationship("Achievement", back_populates="history")

    __table_args__ = (
        Index('idx_achievement_history_achievement', 'achievement_id'),
        Index('idx_achievement_history_date', 'created_at'),
    )


class ReviewDynamicData(BaseModel):
    """Динамические данные по конкретному отзыву"""
    __tablename__ = "review_dynamic_data"

    review_id = Column(Integer, ForeignKey('reviews.id', ondelete='CASCADE'), nullable=False)
    recommendation_id = Column(String(100), nullable=False, index=True)
    voted_up = Column(Boolean)
    votes_up = Column(Integer, default=0)
    votes_funny = Column(Integer, default=0)
    weighted_vote_score = Column(Float)
    comment_count = Column(Integer, default=0)

    review = relationship("Review", back_populates="dynamic_data")

    __table_args__ = (
        UniqueConstraint('review_id', 'recommendation_id', name='uq_review_dynamic'),
        Index('idx_review_dynamic_review', 'review_id'),
        Index('idx_review_dynamic_recommendation', 'recommendation_id'),
    )
