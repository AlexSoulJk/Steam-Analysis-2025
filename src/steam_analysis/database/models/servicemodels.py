from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, Text, JSON,
    ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from .analysisbase import AnalysisBaseModel


class AnalysisChunk(AnalysisBaseModel):
    """Информация о чанке обработки"""
    __tablename__ = "analysis_chunks"

    status = Column(String(50), default="pending")  # pending / in_progress / success / failed

    processed_by = Column(String(100), nullable=True)
    response_time = Column(Float)

    error_log = Column(Text)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)

    completed = Column(Boolean, default=False)  # можно оставить для обратной совместимости

    games = relationship(
        "GameDataAnalysis",
        back_populates="chunk",
        cascade="all, delete-orphan",
        lazy="dynamic"  # ← это позволит делать запросы типа chunk.games.filter_by(...)
    )

    # region app_id props
    @property
    def start_app_id(self):
        """Виртуальное свойство для start_app_id"""
        first_game = self.games.order_by(GameDataAnalysis.app_id.asc()).first()
        return first_game.app_id if first_game else None

    @property
    def end_app_id(self):
        """Виртуальное свойство для end_app_id"""
        last_game = self.games.order_by(GameDataAnalysis.app_id.desc()).first()
        return last_game.app_id if last_game else None

    @property
    def app_ids(self):
        """Виртуальное свойство для app_ids"""
        return [game.app_id for game in self.games.order_by(GameDataAnalysis.app_id.asc())]

    # endregion

    # region status props
    @property
    def successful_games(self):
        """Список успешно обработанных игр"""
        return self.games.filter(GameDataAnalysis.status == "success").all()

    @property
    def failed_games(self):
        """Список неудачно обработанных игр"""
        return self.games.filter(GameDataAnalysis.status == "failed").all()

    @property
    def pending_games(self):
        """Список игр в ожидании обработки"""
        return self.games.filter(GameDataAnalysis.status == "pending").all()

    @property
    def in_progress_games(self):
        return self.games.filter(GameDataAnalysis.status == "in_progress").all()

    @property
    def partial_success_games(self):
        return self.games.filter(GameDataAnalysis.status == "partial_success ").all()

    # endregion

    # region counts props
    @property
    def null_count(self):
        """Количество игр с null_state. В стиме о них информации нет"""
        return self.games.filter(GameDataAnalysis.status == "null_state").count()

    @property
    def partial_count(self):
        """Количество игр с null_state. В стиме о них информации нет"""
        return self.games.filter(GameDataAnalysis.status == "partial").count()

    @property
    def not_null_count(self):
        """Количество игр с processed=True"""
        return self.success_count + self.partial_count

    @property
    def success_count(self):
        """Количество успешно обработанных игр"""
        return self.games.filter(GameDataAnalysis.status == "success").count()

    @property
    def failed_count(self):
        """Количество неудачно обработанных игр"""
        return self.games.filter(GameDataAnalysis.status == "failed").count()

    # endregion

    # region Support methods
    def add_processing_time(self, additional_time: float):
        """Добавить время обработки к аккумулятору"""
        self.response_time += additional_time

    def update_chunk_error_log(self):
        """Обновить error_log чанка на основе ошибок игр"""
        game_errors = [g.error_log for g in self.games if g.error_log]
        all_errors = [self.error_log] + game_errors if self.error_log else game_errors
        self.error_log = "\n---\n".join(filter(None, all_errors))

    # endregion

    __table_args__ = (
        Index('idx_analysis_chunk_status', 'status'),
        Index('idx_analysis_chunk_processed_by', 'processed_by'),
        CheckConstraint('started_at IS NULL OR finished_at IS NULL OR started_at <= finished_at',
                        name='check_timeline_order'),
    )


class GameDataAnalysis(AnalysisBaseModel):
    """Результаты анализа конкретной игры внутри чанка"""
    __tablename__ = "game_data_analysis"

    chunk_id = Column(Integer, ForeignKey("analysis_chunks.id", ondelete="CASCADE"))

    app_id = Column(Integer, nullable=False, index=True)

    status = Column(String(50), default="pending")  # success / failed / partial
    error_log = Column(Text, nullable=True)  # ошибка, если не удалось обработать игру
    chunk = relationship("AnalysisChunk", back_populates="games")
    created_at = Column(DateTime)

    __table_args__ = (
        Index('idx_game_data_chunk', 'chunk_id'),
        Index('idx_game_data_app', 'app_id'),
        Index('idx_game_data_status', 'status'),
    )
