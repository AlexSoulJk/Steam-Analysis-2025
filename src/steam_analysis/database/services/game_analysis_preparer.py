from typing import List

from steam_analysis.core.schemas.analysis.game import GameAnalysisChunkCreate, GameAnalysisFromJson, GameAnalysisCreate
from steam_analysis.database.models.servicemodels import AnalysisChunk
from steam_analysis.database.repositories.analysis.gamechunk import GameChunkRepository
from steam_analysis.database.repositories.analysis.gamedata import GameAnalysisRepository


class GamePreparer:

    def __init__(self):
        self.game_model_repo = GameAnalysisRepository()
        self.chunk_repo = GameChunkRepository()

    def create_chuncks(self, chuncks: List[GameAnalysisChunkCreate],
                       games: List[List[GameAnalysisFromJson]], session):

        if len(chuncks) != len(games):
            raise Exception("Amount of chunks for create doesn't match with with amount fo games splited by chuncks")

        chunk_without_games = self.chunk_repo.create_bulk(objects_in=chuncks,
                                                          session=session)
        created_chunk_id = list(map(lambda x: x.id, chunk_without_games))
        self.game_model_repo.create_bulk(objects_in=list(map(GameAnalysisCreate.from_json_model,
                                                             zip(games, created_chunk_id))))

        pass
