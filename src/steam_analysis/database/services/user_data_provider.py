from sqlalchemy.orm import Session

from steam_analysis.core.schemas.analysis.user import UserAnalysisChunkUpdate
from steam_analysis.database.repositories.analysis.userchunk import UserChunkRepository
from steam_analysis.database.repositories.analysis.userdata import UserAnalysisRepository


class UserAnalysisProvider:

    def __init__(self):
        self.user_model_repo = UserAnalysisRepository()
        self.chunk_repo = UserChunkRepository()

    def get_next_pending_chunk_by_processor_name(self, processor_name: str, session: Session):

        chunk = self.chunk_repo.get_next_pending_chunk_by_name(processor_name, session)

        if chunk is None:
            raise Exception(f"Chunk storage for {processor_name} is empty. Please fill analysis-db")

        chunk.users = self.user_model_repo.mark_list_as_in_progress(chunk.users, session)
        return chunk

    def get_next_part_chunk_by_processor_name(self, processor_name: str, session: Session):
        chunk = self.chunk_repo.get_next_particle_chunk_by_name(processor_name, session)

        if chunk is None:
            raise Exception(f"Chunk storage for {processor_name} is empty. Please fill analysis-db")

        self.user_model_repo.mark_list_as_in_progress(chunk.users, session)

        session.refresh(chunk)
        return chunk

    def mark_as_in_particle(self, chunk: UserAnalysisChunkUpdate, session: Session):
        pass

    def mark_as_success(self, chunk: UserAnalysisChunkUpdate, session: Session):
        pass

    def get_next_retry_chunk_by_processor_name(self, processor_name: str, session: Session):
        return self.chunk_repo.get_next_faild_chunk_by_name(processor_name, session)