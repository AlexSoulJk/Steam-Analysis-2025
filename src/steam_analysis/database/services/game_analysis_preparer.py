from typing import List, Optional

from sqlalchemy.orm import Session

from steam_analysis.core.schemas.analysis.game import GameAnalysisChunkCreate, GameAnalysisFromJson, GameAnalysisCreate, \
    GameAnalysisChunkForRequest
from steam_analysis.database.models.servicemodels import AnalysisChunk, GameDataAnalysis
from steam_analysis.database.repositories.analysis.gamechunk import GameChunkRepository
from steam_analysis.database.repositories.analysis.gamedata import GameAnalysisRepository


class GamePreparer:

    def __init__(self):
        self.game_model_repo = GameAnalysisRepository()
        self.chunk_repo = GameChunkRepository()

    def _prepare_game_list_for_create(self, created_chunks: List[AnalysisChunk],
                                      games: List[List[GameAnalysisFromJson]]) -> List[GameAnalysisCreate]:
        res = []
        for created_chunk, game_in_chunk in zip(created_chunks, games):
            res.extend(list(map(lambda x: GameAnalysisCreate.from_json_model(json_data=x,
                                                                             chunk_id=created_chunk.id),
                                game_in_chunk)))
        return res

    def create_chuncks(self, chuncks: List[GameAnalysisChunkCreate],
                       games: List[List[GameAnalysisFromJson]], session: Session):

        if len(chuncks) != len(games):
            raise Exception("Amount of chunks for create doesn't match with with amount fo games splited by chuncks")

        chunk_without_games = self.chunk_repo.create_bulk(objects_in=chuncks,
                                                          session=session)

        prepared_games = self._prepare_game_list_for_create(chunk_without_games,
                                                            games)

        self.game_model_repo.create_bulk(objects_in=prepared_games,
                                         session=session)
        session.commit()

        pass

    def get_last_uploaded_game(self, session: Session) -> Optional[GameDataAnalysis]:
        return self.game_model_repo.get_last_uploaded_game(session)

    def mark_game_chunk_complete(self, chunk: GameAnalysisChunkForRequest, session):
        self.chunk_repo.update_by_id(chunk.chunk.id, obj_in=chunk.chunk,
                                     session=session, no_commit=True)
        for game in chunk.chunk_games:
            self.game_model_repo.update_by_id(game.id, obj_in=game,
                                              session=session, no_commit=True)
        session.commit()
        pass
