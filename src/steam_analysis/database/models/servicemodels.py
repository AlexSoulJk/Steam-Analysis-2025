from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from .analysisbase import AnalysisBaseModel



class AnalysisChunk(AnalysisBaseModel):
    """Информация о чанке обработки (например, загрузке игр)"""
    __tablename__ = "analysis_chunks"

    start_app_id = Column(Integer, nullable=False)
    end_app_id = Column(Integer, nullable=False)
    response_time = Column(Float)  # сек
    null_count = Column(Integer, default=0)
    not_null_count = Column(Integer, default=0)
    processed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    error_log = Column(Text)
    completed = Column(Boolean, default=False)

    game_data = relationship("GameDataAnalysis", back_populates="chunk", cascade="all, delete-orphan")


class GameDataAnalysis(AnalysisBaseModel):
    """Результаты анализа конкретной игры внутри чанка"""
    __tablename__ = "game_data_analysis"

    chunk_id = Column(Integer, ForeignKey("analysis_chunks.id", ondelete="CASCADE"), nullable=False)
    game_id = Column(Integer, nullable=True)
    version = Column(Integer, default=1)
    stats = Column(JSON, nullable=True)
    achievements = Column(JSON, nullable=True)

    chunk = relationship("AnalysisChunk", back_populates="game_data")
