from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, Text,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship, validates
from .base import BaseModel, DictionaryModel


class Game(BaseModel):
    """Основная модель игры"""
    __tablename__ = "games"

    app_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    type_id = Column(Integer, ForeignKey('game_types.id'), nullable=False)
    is_free = Column(Boolean, default=False)
    release_date = Column(DateTime)
    coming_soon = Column(Boolean, default=False)
    controller_support = Column(String(50))

    # Связи
    game_type = relationship("GameType")
    metrics = relationship("GameMetrics", back_populates="game", uselist=False, cascade="all, delete-orphan")
    genres = relationship("GameGenre", back_populates="game", cascade="all, delete-orphan")
    categories = relationship("GameCategory", back_populates="game", cascade="all, delete-orphan")
    platforms = relationship("GamePlatform", back_populates="game", cascade="all, delete-orphan")
    prices = relationship("PriceHistory", back_populates="game", cascade="all, delete-orphan")

    # Индексы
    __table_args__ = (
        Index('idx_games_app_id', 'app_id'),
        Index('idx_games_name', 'name'),
        Index('idx_games_release_date', 'release_date'),
        Index('idx_games_free', 'is_free'),
        Index('idx_games_coming_soon', 'coming_soon'),
        Index('idx_games_type', 'type_id'),
    )

    @validates('release_date')
    def validate_release_date(self, key, date):
        """Валидация даты релиза"""
        if date and date.year < 1990:  # Steam появился в 2003, но на всякий случай
            raise ValueError("Release date seems too early for Steam")
        return date

class Genre(DictionaryModel):
    """Справочник жанров"""
    __tablename__ = "genres"

    # Связи
    games = relationship("GameGenre", back_populates="genre", cascade="all, delete-orphan")


class Category(DictionaryModel):
    """Справочник категорий"""
    __tablename__ = "categories"

    # Связи
    games = relationship("GameCategory", back_populates="category", cascade="all, delete-orphan")


class Platform(DictionaryModel):
    """Справочник платформ"""
    __tablename__ = "platforms"

    games = relationship("GameCategory", back_populates="platform", cascade="all, delete-orphan")


class GameType(DictionaryModel):
    """Справочник типов игр"""
    __tablename__ = "game_types"

    games = relationship("GameCategory", back_populates="category", cascade="all, delete-orphan")


class GameGenre(BaseModel):
    """Связь многие-ко-многим: Игры - Жанры"""
    __tablename__ = "game_genres"

    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    genre_id = Column(Integer, ForeignKey('genres.id', ondelete='CASCADE'), nullable=False)

    # Связи
    game = relationship("Game", back_populates="genres")
    genre = relationship("Genre", back_populates="games")

    __table_args__ = (
        UniqueConstraint('game_id', 'genre_id', name='uq_game_genre'),
        Index('idx_game_genre_game', 'game_id'),
        Index('idx_game_genre_genre', 'genre_id'),
    )


class GameCategory(BaseModel):
    """Связь многие-ко-многим: Игры - Категории"""
    __tablename__ = "game_categories"

    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)

    # Связи
    game = relationship("Game", back_populates="categories")
    category = relationship("Category", back_populates="games")

    __table_args__ = (
        UniqueConstraint('game_id', 'category_id', name='uq_game_category'),
        Index('idx_game_category_game', 'game_id'),
        Index('idx_game_category_category', 'category_id'),
    )


class GamePlatform(BaseModel):
    """Связь многие-ко-многим: Игры - Платформы"""
    __tablename__ = "game_platforms"

    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    platform_id = Column(Integer, ForeignKey('platforms.id', ondelete='CASCADE'), nullable=False)
    supported = Column(Boolean, default=True)

    # Связи
    game = relationship("Game", back_populates="platforms")
    platform = relationship("Platform", back_populates="games")

    __table_args__ = (
        UniqueConstraint('game_id', 'platform_id', name='uq_game_platform'),
        Index('idx_game_platform_game', 'game_id'),
        Index('idx_game_platform_platform', 'platform_id'),
    )


class PriceHistory(BaseModel):
    """История цен игр"""
    __tablename__ = "price_history"

    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    currency = Column(String(3), default='USD', nullable=False)
    price_final = Column(Integer)  # в центах
    discount_percent = Column(Integer, default=0)
    recorded_at = Column(DateTime, nullable=False)

    # Связи
    game = relationship("Game", back_populates="prices")

    __table_args__ = (
        Index('idx_price_history_game', 'game_id'),
        Index('idx_price_history_date', 'recorded_at'),
        Index('idx_price_history_currency', 'currency'),
    )

    @validates('price_final')
    def validate_price(self, key, price):
        """Валидация цены"""
        if price is not None and price < 0:
            raise ValueError("Price cannot be negative")
        return price


class PlayerCountHistory(BaseModel):
    """История онлайна игроков"""
    __tablename__ = "player_count_history"

    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    player_count = Column(Integer, nullable=False)
    recorded_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index('idx_player_history_game', 'game_id'),
        Index('idx_player_history_date', 'recorded_at'),
    )

    @validates('player_count')
    def validate_player_count(self, key, count):
        """Валидация количества игроков"""
        if count < 0:
            raise ValueError("Player count cannot be negative")
        return count