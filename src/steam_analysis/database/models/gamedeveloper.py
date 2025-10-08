from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, Text,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from .base import BaseModel


class GameDeveloper(BaseModel):
    """Связь многие-ко-многим: Игры - Разработчики"""
    __tablename__ = "game_developers"

    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    developer_id = Column(Integer, ForeignKey('developers.id', ondelete='CASCADE'), nullable=False)

    game = relationship("Game")
    developer = relationship("Developer", back_populates="games")

    __table_args__ = (
        UniqueConstraint('game_id', 'developer_id', name='uq_game_developer'),
        Index('idx_game_developer_game', 'game_id'),
        Index('idx_game_developer_dev', 'developer_id'),
    )


class GamePublisher(BaseModel):
    """Связь многие-ко-многим: Игры - Издатели"""
    __tablename__ = "game_publishers"

    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    publisher_id = Column(Integer, ForeignKey('publishers.id', ondelete='CASCADE'), nullable=False)

    game = relationship("Game")
    publisher = relationship("Publisher", back_populates="games")

    __table_args__ = (
        UniqueConstraint('game_id', 'publisher_id', name='uq_game_publisher'),
        Index('idx_game_publisher_game', 'game_id'),
        Index('idx_game_publisher_pub', 'publisher_id'),
    )