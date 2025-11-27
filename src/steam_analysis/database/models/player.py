from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, Text,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from .base import BaseModel


class User(BaseModel):
    """Модель пользователя/игрока"""
    __tablename__ = "users"

    steam_id = Column(String(17), unique=True, nullable=False, index=True)
    persona_name = Column(String(255))
    profile_url = Column(String(500))
    time_created = Column(DateTime)
    last_logoff = Column(DateTime)
    community_visibility_state = Column(Integer)
    steam_level = Column(Integer, default=0)

    loccountrycode = Column(String(500), nullable=True)
    locstatecode = Column(String(500), nullable=True)
    loccityid = Column(String(500), nullable=True)

    game_ownership = relationship("UserGameOwnership", back_populates="user", cascade="all, delete-orphan")
    playtime = relationship("UserPlaytime", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    logoff_history = relationship("UserLogoffHistory", back_populates="user", cascade="all, delete-orphan")
    friends = relationship(
        "Friend",
        foreign_keys="Friend.user_id",  # ⬅️ ЯВНО указываем какой foreign key использовать
        back_populates="user",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_user_steam_id', 'steam_id'),
    )


class UserPlaytime(BaseModel):
    """Время игры пользователей"""
    __tablename__ = "user_playtime"

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    playtime_forever = Column(Integer)  # общее время в минутах
    playtime_2weeks = Column(Integer)  # время за 2 недели в минутах
    last_played = Column(DateTime)

    user = relationship("User", back_populates="playtime")
    game = relationship("Game")

    __table_args__ = (
        UniqueConstraint('user_id', 'game_id', name='uq_user_playtime'),
        Index('idx_playtime_user', 'user_id'),
        Index('idx_playtime_game', 'game_id'),
        Index('idx_playtime_last_played', 'last_played'),
    )


class Friend(BaseModel):
    """Друзья пользователя"""
    __tablename__ = "friends"

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    friend_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = Column(String(20), default='valid')

    user = relationship("User", foreign_keys=[user_id], back_populates="friends")
    friend = relationship("User", foreign_keys=[friend_id])

    __table_args__ = (
        UniqueConstraint('user_id', 'friend_id', name='uq_friends_pair'),
        Index('idx_friends_user', 'user_id'),
        Index('idx_friends_friend', 'friend_id'),
    )
