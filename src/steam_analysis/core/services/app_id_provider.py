import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from typing import List, Optional, Union

from steam_analysis.database.models.servicemodels import AnalysisChunk, GameDataAnalysis


class AppIdProviderService:
    """
    Сервис управления чанками app_id для анализа и загрузки данных из Steam API.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_chunk(
        self,
        app_ids: List[int],
        processed_by: Optional[str] = None,
        start_app_id: Optional[int] = None,
        end_app_id: Optional[int] = None,
    ) -> AnalysisChunk:
        """
        Создает один чанк для указанного списка app_id.
        """
        chunk = AnalysisChunk(
            app_ids=app_ids,
            start_app_id=start_app_id or (min(app_ids) if app_ids else None),
            end_app_id=end_app_id or (max(app_ids) if app_ids else None),
            status="pending",
            processed_by=processed_by,
            created_at=datetime.datetime.utcnow(),
        )
        self.db.add(chunk)
        self.db.commit()
        self.db.refresh(chunk)
        return chunk

    def create_chunks_by_range(
        self,
        start_id: int,
        end_id: int,
        step: int = 100,
        processed_by: Optional[str] = None,
    ) -> List[AnalysisChunk]:
        """
        Создает чанки для диапазона app_id (например, 1000–9999) с заданным шагом.
        Пример:
            create_chunks_by_range(1000, 1200, step=50)
            → создаст чанки [1000–1049], [1050–1099], [1100–1149], [1150–1199]
        """
        chunks = []
        current = start_id

        while current <= end_id:
            batch_ids = list(range(current, min(current + step, end_id + 1)))
            chunk = self.create_chunk(batch_ids, processed_by=processed_by)
            chunks.append(chunk)
            current += step

        return chunks

    def create_chunks_from_list(
        self,
        app_id_list: List[int],
        chunk_size: int = 100,
        processed_by: Optional[str] = None,
    ) -> List[AnalysisChunk]:
        """
        Создает чанки из произвольного списка app_id (например, если ID идут не подряд).
        Пример:
            create_chunks_from_list([123, 999, 1500, 1510], chunk_size=2)
            → создаст чанки с app_ids: [123, 999], [1500, 1510]
        """
        chunks = []
        for i in range(0, len(app_id_list), chunk_size):
            subset = app_id_list[i:i + chunk_size]
            chunk = self.create_chunk(subset, processed_by=processed_by)
            chunks.append(chunk)
        return chunks

    def get_next_chunk(self, limit: int = 1) -> Optional[AnalysisChunk]:
        """
        Получить следующий чанк, который еще не обрабатывался.
        """
        chunk = (
            self.db.execute(
                select(AnalysisChunk)
                .where(AnalysisChunk.status == "pending")
                .order_by(AnalysisChunk.id.asc())
                .limit(limit)
            )
            .scalars()
            .first()
        )

        if chunk:
            chunk.status = "in_progress"
            chunk.started_at = datetime.datetime.utcnow()
            self.db.commit()
            self.db.refresh(chunk)

        return chunk

    def mark_chunk_completed(
        self,
        chunk_id: int,
        null_count: int = 0,
        not_null_count: int = 0,
        failed_count: int = 0,
        response_time: Optional[float] = None,
        processed_by: Optional[str] = None,
    ):
        """
        Пометить чанк как завершенный и обновить статистику.
        """
        stmt = (
            update(AnalysisChunk)
            .where(AnalysisChunk.id == chunk_id)
            .values(
                status="success",
                completed=True,
                finished_at=datetime.datetime.utcnow(),
                null_count=null_count,
                not_null_count=not_null_count,
                failed_count=failed_count,
                response_time=response_time,
                processed_by=processed_by,
            )
        )
        self.db.execute(stmt)
        self.db.commit()

    def mark_chunk_failed(self, chunk_id: int, error_log: str):
        """
        Пометить чанк как неудачный (ошибка выполнения).
        """
        stmt = (
            update(AnalysisChunk)
            .where(AnalysisChunk.id == chunk_id)
            .values(
                status="failed",
                finished_at=datetime.datetime.utcnow(),
                error_log=error_log,
                completed=True,
            )
        )
        self.db.execute(stmt)
        self.db.commit()

    def add_game_analysis(
        self,
        chunk_id: int,
        app_id: int,
        stats: Optional[dict] = None,
        achievements: Optional[dict] = None,
        response_time: Optional[float] = None,
        error: Optional[str] = None,
    ) -> GameDataAnalysis:
        """
        Добавить информацию об анализе конкретной игры в рамках чанка.
        """
        game_analysis = GameDataAnalysis(
            chunk_id=chunk_id,
            app_id=app_id,
            stats=stats,
            achievements=achievements,
            response_time=response_time,
            error_log=error,
            created_at=datetime.datetime.utcnow(),
        )
        self.db.add(game_analysis)
        self.db.commit()
        self.db.refresh(game_analysis)
        return game_analysis

