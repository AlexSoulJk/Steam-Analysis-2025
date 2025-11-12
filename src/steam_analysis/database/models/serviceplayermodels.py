from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, Text,
    ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from .analysisbase import AnalysisBaseModel


class AnalysisUserChunk(AnalysisBaseModel):
    """Информация о чанке обработки"""
    __tablename__ = "analysis_user_chunks"

    status = Column(String(50), default="pending")  # pending / in_progress / success / failed

    processed_by = Column(String(100), nullable=True)
    response_time = Column(Float)

    error_log = Column(Text)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)

    completed = Column(Boolean, default=False)

    users = relationship(
        "UserDataAnalysis",
        back_populates="chunk",
        cascade="all, delete-orphan",
        lazy="select"
    )

    @property
    def start_steam_id(self):
        """Виртуальное свойство для start_steam_id"""
        first_user = self.users.order_by(UserDataAnalysis.steam_id.asc()).first()
        return first_user.steam_id if first_user else None

    @property
    def end_steam_id(self):
        """Виртуальное свойство для end_steam_id"""
        last_user = self.users.order_by(UserDataAnalysis.steam_id.desc()).first()
        return last_user.steam_id if last_user else None

    @property
    def steam_ids(self):
        """Виртуальное свойство для steam_ids"""
        return [user.steam_id for user in self.users.order_by(UserDataAnalysis.steam_id.asc())]

    # endregion

    # region status props
    @property
    def successful_user(self):
        """Список успешно обработанных игр"""
        return self.users.filter(UserDataAnalysis.status == "success").all()

    @property
    def failed_users(self):
        """Список неудачно обработанных игр"""
        return self.users.filter(UserDataAnalysis.status == "failed").all()

    @property
    def pending_users(self):
        """Список игр в ожидании обработки"""
        return self.users.filter(UserDataAnalysis.status == "pending").all()

    @property
    def in_progress_users(self):
        return self.users.filter(UserDataAnalysis.status == "in_progress").all()

    @property
    def partial_success_users(self):
        return self.users.filter(UserDataAnalysis.status == "partial_success ").all()

    # endregion

    # region counts props
    @property
    def null_count(self):
        """Количество игр с null_state. В стиме о них информации нет"""
        return self.users.filter(UserDataAnalysis.status == "null_state").count()

    @property
    def partial_count(self):
        return self.users.filter(UserDataAnalysis.status == "partial").count()

    @property
    def not_null_count(self):
        return self.success_count + self.partial_count

    @property
    def success_count(self):
        return self.users.filter(UserDataAnalysis.status == "success").count()

    @property
    def failed_count(self):
        return self.users.filter(UserDataAnalysis.status == "failed").count()

    # endregion

    # region Support methods
    def add_processing_time(self, additional_time: float):
        """Добавить время обработки к аккумулятору"""
        self.response_time += additional_time

    def update_chunk_error_log(self):
        """Обновить error_log чанка на основе ошибок юзеров"""
        user_errors = [g.error_log for g in self.users if g.error_log]
        all_errors = [self.error_log] + user_errors if self.error_log else user_errors
        self.error_log = "\n---\n".join(filter(None, all_errors))

    # endregion

    __table_args__ = (
        Index('idx_analysis_user_chunk_status', 'status'),
        Index('idx_analysis_user_chunk_processed_by', 'processed_by'),
        CheckConstraint('started_at IS NULL OR finished_at IS NULL OR started_at <= finished_at',
                        name='check_timeline_order'),
    )


class UserDataAnalysis(AnalysisBaseModel):
    """Результаты анализа конкретного юзера внутри чанка"""
    __tablename__ = "user_data_analysis"

    chunk_id = Column(Integer, ForeignKey("analysis_user_chunks.id", ondelete="CASCADE"))

    steam_id = Column(Integer, nullable=False, index=True, unique=True)

    status = Column(String(50), default="pending")  # success / failed / partial
    error_log = Column(Text, nullable=True)
    chunk = relationship("AnalysisUserChunk", back_populates="users")
    name = Column(String(150))
    created_at = Column(DateTime)

    __table_args__ = (
        Index('idx_user_data_chunk', 'chunk_id'),
        Index('idx_user_data_app', 'steam_id'),
        Index('idx_user_data_status', 'status'),
    )
