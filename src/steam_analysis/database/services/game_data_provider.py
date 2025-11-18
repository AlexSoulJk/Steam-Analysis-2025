from sqlalchemy.orm import Session

from steam_analysis.core.schemas.analysis.game import GameAnalysisChunkUpdate
from steam_analysis.database.repositories.analysis.gamechunk import GameChunkRepository
from steam_analysis.database.repositories.analysis.gamedata import GameAnalysisRepository


class GameAnalysisProvider:

    def __init__(self):
        self.game_model_repo = GameAnalysisRepository()
        self.chunk_repo = GameChunkRepository()

    def get_next_pending_chunk_by_processor_name(self, processor_name: str, session: Session):

        chunk = self.chunk_repo.get_next_pending_chunk_by_name(processor_name, session)

        if chunk is None:
            raise Exception(f"Chunk storage for {processor_name} is empty. Please fill analysis-db")

        chunk.games = self.game_model_repo.mark_list_as_in_progress(chunk.games, session)
        session.commit()
        session.refresh(chunk)
        return chunk

    def get_next_part_chunk_by_processor_name(self, processor_name: str, session: Session):
        chunk = self.chunk_repo.get_next_particle_chunk_by_name(processor_name, session)

        if chunk is None:
            raise Exception(f"Chunk storage for {processor_name} is empty. Please fill analysis-db")

        chunk.games = self.game_model_repo.mark_list_as_in_progress(chunk.partial_success_games, session)
        session.commit()
        session.refresh(chunk)
        return chunk

    def mark_as_in_particle(self, chunk: GameAnalysisChunkUpdate, session: Session):
        pass

    def mark_as_success(self, chunk: GameAnalysisChunkUpdate, session: Session):
        pass

    def get_next_retry_chunk_by_processor_name(self, processor_name: str, session: Session):
        return self.chunk_repo.get_next_faild_chunk_by_name(processor_name, session)