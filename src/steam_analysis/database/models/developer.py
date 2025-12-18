from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, Text,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from .base import BaseModel


class Developer(BaseModel):
    """Модель разработчика"""
    __tablename__ = "developers"

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    website = Column(String(500))

    games = relationship("GameDeveloper", back_populates="developer", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_developer_name', 'name'),
    )


class Publisher(BaseModel):
    """Модель издателя"""
    __tablename__ = "publishers"

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    website = Column(String(500))

    games = relationship("GamePublisher", back_populates="publisher", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_publisher_name', 'name'),
    )

