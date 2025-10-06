from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, Text,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from .base import BaseModel


class Achievement(BaseModel):
    """Достижения игры"""
    __tablename__ = "achievements"

    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    icon_url = Column(String(500))
    icon_gray_url = Column(String(500))
    achieved = Column(Boolean, default=False)
    unlock_time = Column(DateTime)
    global_achievement_rate = Column(Float)  # Процент игроков, получивших достижение

    game = relationship("Game", back_populates="achievements")

    __table_args__ = (
        UniqueConstraint('game_id', 'name', name='uq_achievement_game_name'),
        Index('idx_achievements_game', 'game_id'),
        Index('idx_achievements_name', 'name'),
    )

    # ???

    api_name = Column(String(255), nullable=False)  # Technical name from API
    hidden = Column(Boolean, default=False)  # Hidden achievement

    # Связи
    user_achievements = relationship("UserAchievement", back_populates="achievement", cascade="all, delete-orphan")


class AchievementHistory(BaseModel):
    """История изменения статистики достижений"""
    __tablename__ = "achievement_history"

    achievement_id = Column(Integer, ForeignKey('achievements.id', ondelete='CASCADE'), nullable=False)
    global_achievement_rate = Column(Float, nullable=False)

    achievement = relationship("Achievement")

    __table_args__ = (
        Index('idx_achievement_history_achievement', 'achievement_id'),
        Index('idx_achievement_history_date', 'created_at'),
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

    # Связи
    user = relationship("User", back_populates="achievements")
    game = relationship("Game")
    achievement = relationship("Achievement", back_populates="user_achievements")

    __table_args__ = (
        UniqueConstraint('user_id', 'game_id', 'achievement_id', name='uq_user_game_achievement'),
        Index('idx_user_achievements_user', 'user_id'),
        Index('idx_user_achievements_game', 'game_id'),
    )