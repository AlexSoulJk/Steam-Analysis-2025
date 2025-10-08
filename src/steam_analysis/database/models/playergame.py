from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, Text,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from .base import BaseModel


class UserGameOwnership(BaseModel):
    """Владение играми пользователями"""
    __tablename__ = "user_game_ownership"

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    owned = Column(Boolean, default=True)
    ownership_date = Column(DateTime)

    user = relationship("User", back_populates="game_ownership")
    game = relationship("Game")

    __table_args__ = (
        UniqueConstraint('user_id', 'game_id', name='uq_user_game_ownership'),
        Index('idx_ownership_user', 'user_id'),
        Index('idx_ownership_game', 'game_id'),
    )


class Review(BaseModel):
    """Отзыв пользователя на игру"""
    __tablename__ = "reviews"

    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    recommendation_id = Column(String(100), unique=True, nullable=False)
    steam_id = Column(String(20), nullable=False, index=True)

    language = Column(String(20))
    review = Column(Text)
    timestamp_created = Column(Integer)
    timestamp_updated = Column(Integer)
    voted_up = Column(Boolean)
    votes_up = Column(Integer, default=0)
    votes_funny = Column(Integer, default=0)
    weighted_vote_score = Column(Float)
    comment_count = Column(Integer, default=0)
    steam_purchase = Column(Boolean, default=False)
    received_for_free = Column(Boolean, default=False)
    written_during_early_access = Column(Boolean, default=False)
    primarily_steam_deck = Column(Boolean, default=False)

    game = relationship("Game", back_populates="reviews")
    user = relationship("User", back_populates="reviews")

    __table_args__ = (
        Index('idx_reviews_game', 'game_id'),
        Index('idx_reviews_user', 'user_id'),
        Index('idx_reviews_steam', 'steam_id'),
        Index('idx_reviews_created', 'timestamp_created'),
    )


class UserAchievement(BaseModel):
    """Достижения конкретного пользователя"""
    __tablename__ = "user_achievements"

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    achievement_id = Column(Integer, ForeignKey('achievements.id', ondelete='CASCADE'), nullable=False)

    achieved = Column(Boolean, default=False)
    unlock_timestamp = Column(Integer)  # Unix timestamp
    unlock_time = Column(DateTime)  # Converted datetime


    user = relationship("User", back_populates="achievements")
    game = relationship("Game")
    achievement = relationship("Achievement", back_populates="user_achievements")

    __table_args__ = (
        UniqueConstraint('user_id', 'game_id', 'achievement_id', name='uq_user_game_achievement'),
        Index('idx_user_achievements_user', 'user_id'),
        Index('idx_user_achievements_game', 'game_id'),
        Index('idx_user_achievements_unlock_time', 'unlock_time'),
    )
