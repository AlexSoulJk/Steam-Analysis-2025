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
    release_date = Column(DateTime)
    coming_soon = Column(Boolean, default=False)
    controller_support = Column(String(50))
    is_free = Column(Boolean, default=False)

    game_type = relationship("GameType")
    metrics = relationship("GameMetrics", back_populates="game", uselist=False, cascade="all, delete-orphan")
    genres = relationship("GameGenre", back_populates="game", cascade="all, delete-orphan")
    categories = relationship("GameCategory", back_populates="game", cascade="all, delete-orphan")
    platforms = relationship("GamePlatform", back_populates="game", cascade="all, delete-orphan")

    reviews = relationship("Review", back_populates="game", cascade="all, delete-orphan")
    news = relationship("News", back_populates="game", cascade="all, delete-orphan")
    achievements = relationship("Achievement", back_populates="game", cascade="all, delete-orphan")
    developers = relationship("GameDeveloper", back_populates="game", cascade="all, delete-orphan")
    publishers = relationship("GamePublisher", back_populates="game", cascade="all, delete-orphan")

    users_owned = relationship("UserGameOwnership", back_populates="game", cascade="all, delete-orphan")
    user_achievements = relationship("UserAchievement", back_populates="game", cascade="all, delete-orphan")

    review_history = relationship("ReviewHistory", back_populates="game", cascade="all, delete-orphan")
    prices = relationship("PriceHistory", back_populates="game", cascade="all, delete-orphan")
    player_counts = relationship("PlayerCountHistory", back_populates="game", cascade="all, delete-orphan")

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


class GameMetrics(BaseModel):
    """Метрики игры (отдельно от основной информации)"""
    __tablename__ = "game_metrics"

    game_id = Column(Integer, ForeignKey('games.id'), unique=True, nullable=False)
    recommendations_count = Column(Integer, default=0)
    metacritic_score = Column(Integer)
    review_score = Column(Float)  # 0.0-1.0
    review_count = Column(Integer, default=0)
    peak_players_all_time = Column(Integer, default=0)

    game = relationship("Game", back_populates="metrics")

    __table_args__ = (
        Index('idx_metrics_review_score', 'review_score'),
        Index('idx_metrics_players', 'peak_players_all_time'),
    )


class Genre(DictionaryModel):
    """Справочник жанров"""
    __tablename__ = "genres"

    steam_id = Column(String(50), unique=True, index=True, nullable=False) #???????????

    games = relationship("GameGenre", back_populates="genre", cascade="all, delete-orphan")


class Category(DictionaryModel):
    """Справочник категорий"""
    __tablename__ = "categories"

    steam_id = Column(String(50), unique=True, index=True, nullable=False)  # ???????????

    games = relationship("GameCategory", back_populates="category", cascade="all, delete-orphan")


class Platform(DictionaryModel):
    __tablename__ = "platforms"

    steam_id = Column(String(50), unique=True, index=True, nullable=True)  # ???????????

    games = relationship("GamePlatform", back_populates="platform", cascade="all, delete-orphan")


class GameType(DictionaryModel):
    __tablename__ = "game_types"
    games = relationship("Game", back_populates="game_type")  # Связь с Game, а не GameCategory


class GameGenre(BaseModel):
    """Связь многие-ко-многим: Игры - Жанры"""
    __tablename__ = "game_genres"

    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    genre_id = Column(Integer, ForeignKey('genres.id', ondelete='CASCADE'), nullable=False)

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

    game = relationship("Game", back_populates="platforms")
    platform = relationship("Platform", back_populates="games")

    __table_args__ = (
        UniqueConstraint('game_id', 'platform_id', name='uq_game_platform'),
        Index('idx_game_platform_game', 'game_id'),
        Index('idx_game_platform_platform', 'platform_id'),
    )


class News(BaseModel):
    """Новости игры"""
    __tablename__ = "news"

    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    gid = Column(String(100), unique=True, nullable=False)
    title = Column(String(500))
    url = Column(String(500))
    is_external_url = Column(Boolean, default=False)
    author = Column(String(255))
    contents = Column(Text)
    feedlabel = Column(String(255))
    date = Column(Integer)  # timestamp
    feedname = Column(String(255))
    feed_type = Column(Integer)

    game = relationship("Game", back_populates="news")

    __table_args__ = (
        Index('idx_news_game', 'game_id'),
        Index('idx_news_date', 'date'),
    )


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

    api_name = Column(String(255), nullable=False)  # Technical name from API
    hidden = Column(Boolean, default=False)  # Hidden achievement

    user_achievements = relationship("UserAchievement", back_populates="achievement", cascade="all, delete-orphan")
    game = relationship("Game", back_populates="achievements")
    history = relationship("AchievementHistory", back_populates="achievement", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('game_id', 'name', name='uq_achievement_game_name'),
        Index('idx_achievements_game', 'game_id'),
        Index('idx_achievements_name', 'name'),
    )
