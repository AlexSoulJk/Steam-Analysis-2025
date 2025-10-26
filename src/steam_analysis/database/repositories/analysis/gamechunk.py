from typing import Optional, List, Dict

from sqlalchemy import select
from sqlalchemy.orm import joinedload, Session

from steam_analysis.core.schemas.analysis.game import GameAnalysisChunkCreate, GameAnalysisChunkUpdate, \
    GameAnalysisCreate
from ..base.baseanalisis import BaseAnalysisRepository
from ...models.servicemodels import AnalysisChunk


class GameChunkRepository(BaseAnalysisRepository[AnalysisChunk, GameAnalysisChunkCreate, GameAnalysisChunkUpdate]):
    """Репозиторий для работы с играми"""

    def __init__(self):
        super().__init__(model=AnalysisChunk)

    def _get_next_chunk_by_status_and_name(self, status: str, processor_name: str, session: Session):
        obj: AnalysisChunk = session.query(AnalysisChunk).filter(AnalysisChunk.status == status and
                                                                 AnalysisChunk.processed_by == processor_name).order_by(
            AnalysisChunk.id).first()
        obj.status = "in_progress"
        return obj

    def get_next_pending_chunk_by_name(self, processor_name: str, session: Session) -> Optional[AnalysisChunk]:
        return self._get_next_chunk_by_status_and_name(status="pending",
                                                       processor_name=processor_name,
                                                       session=session)

    def get_next_faild_chunk_by_name(self, processor_name: str, session: Session) -> Optional[AnalysisChunk]:
        return self._get_next_chunk_by_status_and_name(status="faild",
                                                       processor_name=processor_name,
                                                       session=session)

    def get_next_particle_chunk_by_name(self, processor_name: str, session: Session) -> Optional[AnalysisChunk]:
        return self._get_next_chunk_by_status_and_name(status="particle_success",
                                                       processor_name=processor_name,
                                                       session=session)
