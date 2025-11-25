from typing import Optional, List, Dict

from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload, Session, selectinload

from steam_analysis.core.schemas.analysis.user import UserAnalysisChunkCreate, UserAnalysisChunkUpdate, \
    UserAnalysisCreate
from ..base.baseanalisis import BaseAnalysisRepository
from ...models.serviceplayermodels import AnalysisUserChunk

class UserChunkRepository(BaseAnalysisRepository[AnalysisUserChunk, UserAnalysisChunkCreate, UserAnalysisChunkUpdate]):
    """Репозиторий для работы с юзерами"""

    def __init__(self):
        super().__init__(model=AnalysisUserChunk)

    def _get_next_chunk_by_status_and_name(self, status: str, processor_name: str, session: Session) -> Optional[
        AnalysisUserChunk]:
        obj = session.query(AnalysisUserChunk) \
            .filter(
            and_(
                AnalysisUserChunk.status == status,
                AnalysisUserChunk.processed_by == processor_name
            )
        ) \
            .order_by(AnalysisUserChunk.id) \
            .with_for_update().options(selectinload(AnalysisUserChunk.users)).first()
        return obj

    def mark_as_in_progress(self, chunk: AnalysisUserChunk,
                            session: Session) -> AnalysisUserChunk:
        chunk.status = "in_progress"
        session.flush([chunk])
        return chunk

    def update_status_after_processing(self, chunk: UserAnalysisChunkUpdate,
                                       session: Session) -> AnalysisUserChunk:
        chunk_model = self.update_by_id(chunk.id, chunk, session=session)
        return chunk_model

    def get_next_pending_chunk_by_name(self, processor_name: str, session: Session) -> Optional[AnalysisUserChunk]:
        obj = self._get_next_chunk_by_status_and_name(status="pending",
                                                      processor_name=processor_name,
                                                      session=session)
        if obj:
            self.mark_as_in_progress(obj, session)

        return obj

    def get_next_faild_chunk_by_name(self, processor_name: str, session: Session) -> Optional[AnalysisUserChunk]:
        obj = self._get_next_chunk_by_status_and_name(status="failed",
                                                      processor_name=processor_name,
                                                      session=session)
        if obj:
            self.mark_as_in_progress(obj, session)

        return obj

    def get_next_particle_chunk_by_name(self, processor_name: str, session: Session) -> Optional[AnalysisUserChunk]:
        obj = self._get_next_chunk_by_status_and_name(status="particle_success",
                                                      processor_name=processor_name,
                                                      session=session)
        if obj:
            self.mark_as_in_progress(obj, session)

        return obj

    def create_user_bulk(self, objects_in: List[UserAnalysisChunkCreate], session: Session, no_commit=False) -> List[
        AnalysisUserChunk]:
        """
        Массовое создание объектов AnalysisUserChunk, исключая поле chunk_size
        которого нет в модели БД

        Args:
            objects_in: Список Pydantic схем UserAnalysisChunkCreate
            session: Сессия БД
            no_commit: Не коммитить транзакцию

        Returns:
            Список созданных объектов AnalysisUserChunk
        """
        db_objects = []
        for obj_in in objects_in:
            obj_data = obj_in.model_dump(by_alias=True) if hasattr(obj_in, 'model_dump') else obj_in.dict()

            obj_data.pop('chunk_size', None)

            db_obj = self.model(**obj_data)
            db_objects.append(db_obj)

        session.add_all(db_objects)

        if not no_commit:
            session.commit()
            for db_obj in db_objects:
                session.refresh(db_obj)
        else:
            session.flush()

        return db_objects