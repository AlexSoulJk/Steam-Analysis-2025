from typing import Optional, List, Dict

from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload, Session, selectinload

from steam_analysis.core.schemas.analysis.game import GameAnalysisChunkCreate, GameAnalysisChunkUpdate, \
    GameAnalysisCreate
from ..base.baseanalisis import BaseAnalysisRepository
from ...models.servicemodels import AnalysisChunk


class GameChunkRepository(BaseAnalysisRepository[AnalysisChunk, GameAnalysisChunkCreate, GameAnalysisChunkUpdate]):
    """Репозиторий для работы с играми"""

    def __init__(self):
        super().__init__(model=AnalysisChunk) # ыыыыыы

    def get_chunks_by_ids(self, chunk_ids: List[int], session: Session, batch_size=500):
        if not chunk_ids:
            return {}

        result_dict = {}

        # Обрабатываем батчи
        for i in range(0, len(chunk_ids), batch_size):
            batch = chunk_ids[i:i + batch_size]
            query = select(self.model).where(self.model.id.in_(batch))
            result = session.execute(query)
            existing_games = result.scalars().all()

            result_dict.update({chunk.id: chunk for chunk in existing_games})

        return result_dict



    def _get_next_chunk_by_status_and_name(self, status: str, processor_name: str, session: Session) -> Optional[
        AnalysisChunk]:
        obj = session.query(AnalysisChunk) \
            .filter(
            and_(
                AnalysisChunk.status == status,
                AnalysisChunk.processed_by == processor_name
            )
        ) \
            .order_by(AnalysisChunk.id) \
            .with_for_update().options(selectinload(AnalysisChunk.games)).first()
        return obj

    def mark_as_in_progress(self, chunk: AnalysisChunk,
                            session: Session) -> AnalysisChunk:
        chunk.status = "in_progress"
        session.flush([chunk])
        return chunk

    def update_status_after_processing(self, chunk: GameAnalysisChunkUpdate,
                                       session: Session) -> AnalysisChunk:
        chunk_model = self.update_by_id(chunk.id, chunk, session=session)
        return chunk_model

    def get_next_pending_chunk_by_name(self, processor_name: str, session: Session) -> Optional[AnalysisChunk]:
        # TODO: Add exceptions for some cases
        obj = self._get_next_chunk_by_status_and_name(status="pending",
                                                      processor_name=processor_name,
                                                      session=session)
        if obj:
            self.mark_as_in_progress(obj, session)

        return obj

    def get_next_faild_chunk_by_name(self, processor_name: str, session: Session) -> Optional[AnalysisChunk]:
        obj = self._get_next_chunk_by_status_and_name(status="failed",
                                                      processor_name=processor_name,
                                                      session=session)
        if obj:
            self.mark_as_in_progress(obj, session)

        return obj

    def get_next_particle_chunk_by_name(self, processor_name: str, session: Session) -> Optional[AnalysisChunk]:
        obj = self._get_next_chunk_by_status_and_name(status="particle_success",
                                                      processor_name=processor_name,
                                                      session=session)
        if obj:
            self.mark_as_in_progress(obj, session)

        return obj
