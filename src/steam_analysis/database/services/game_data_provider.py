from sqlalchemy.orm import Session

from steam_analysis.core.schemas.analysis.game import GameAnalysisChunkUpdate
from steam_analysis.database.repositories.analysis.gamechunk import GameChunkRepository
from steam_analysis.database.repositories.analysis.gamedata import GameAnalysisRepository


class GameAnalysisProvider:

    def __init__(self):
        self.game_model_repo = GameAnalysisRepository()
        self.chunk_repo = GameChunkRepository()

    def get_next_pending_chunk_by_processor_name(self, processor_name: str, session: Session):
        return self.chunk_repo.get_next_pending_chunk_by_name(processor_name, session)

    def mark_as_in_particle(self, chunk: GameAnalysisChunkUpdate, session: Session):
        pass

    def mark_as_success(self, chunk: GameAnalysisChunkUpdate, session: Session):
        pass

    def get_next_retry_chunk_by_processor_name(self, processor_name: str, session: Session):
        return self.chunk_repo.get_next_faild_chunk_by_name(processor_name, session)