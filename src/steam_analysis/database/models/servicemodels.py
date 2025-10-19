from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, Text, JSON,
    ForeignKey, Index
)
from sqlalchemy.orm import relationship
from .analysisbase import AnalysisBaseModel



class AnalysisChunk(AnalysisBaseModel):
    """Информация о чанке обработки"""
    __tablename__ = "analysis_chunks"

    app_ids = Column(JSON, nullable=False)          # список app_id
    start_app_id = Column(Integer, nullable=True)
    end_app_id = Column(Integer, nullable=True)

    status = Column(String(50), default="pending")  # pending / in_progress / success / failed
    processed_by = Column(String(100), nullable=True)
    response_time = Column(Float)
    null_count = Column(Integer, default=0)
    not_null_count = Column(Integer, default=0)
    processed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    error_log = Column(Text)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    request_count = Column(Integer, default=0)

    completed = Column(Boolean, default=False)  # можно оставить для обратной совместимости

    game_data = relationship(
        "GameDataAnalysis",
        back_populates="chunk",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_analysis_chunk_status', 'status'),
        Index('idx_analysis_chunk_start', 'start_app_id'),
        Index('idx_analysis_chunk_end', 'end_app_id'),
    )



class GameDataAnalysis(AnalysisBaseModel):
    """Результаты анализа конкретной игры внутри чанка"""
    __tablename__ = "game_data_analysis"

    chunk_id = Column(Integer, ForeignKey("analysis_chunks.id", ondelete="CASCADE"), nullable=False)

    app_id = Column(Integer, nullable=False, index=True)
    version = Column(Integer, default=1)  # версия данных (для перезапуска анализа)

    status = Column(String(50), default="success")  # success / failed / partial
    response_time = Column(Float)                   # время ответа API по конкретной игре
    stats = Column(JSON, nullable=True)             # метрики/статистика (StatsCreate)
    achievements = Column(JSON, nullable=True)      # достижения (AchievCreate / AchievPercentCreate)
    genres = Column(JSON, nullable=True)            # жанры
    categories = Column(JSON, nullable=True)        # категории
    platforms = Column(JSON, nullable=True)         # платформы
    error_log = Column(Text, nullable=True)         # ошибка, если не удалось обработать игру

    chunk = relationship("AnalysisChunk", back_populates="game_data")

    __table_args__ = (
        Index('idx_game_data_chunk', 'chunk_id'),
        Index('idx_game_data_app', 'app_id'),
        Index('idx_game_data_status', 'status'),
    )
