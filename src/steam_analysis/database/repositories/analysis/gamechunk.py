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


    # def create_bulk(self, objects_in: List[GameAnalysisChunkCreate],
    #                 session: Session) -> List[AnalysisChunk]:
    #     """
    #     Массовое создание объектов
    #
    #     Args:
    #         objects_in: Список Pydantic схем
    #         session: Session
    #     Returns:
    #         Список созданных объектов
    #     """

