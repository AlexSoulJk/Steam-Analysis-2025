import datetime
from typing import List, Dict, Any, Optional
from ..repositories.game_repository import GameRepository, logger
from ..schemas import GameCreate
from ..schemas.analysis.game import GameAnalysisChunkForResponse, GameAnalysisChunkForRequest, GameAnalysisChunkUpdate
from ..schemas.game.service import TypeAnalysesSchema, FillGameAnalysisChunk, \
    FillTypeSchemaChunk, FillSchemaChunk, FillAddSchemaChunk
from ...resourcemanager.manager import resource_manager
from ...resourcemanager.resources.codes import ResourceCodes


class GameService:
    def __init__(self, game_repo: GameRepository):
        self.game_repo = game_repo
        self.resource_manager = resource_manager

    def get_game_analysis_list(self, chunk: GameAnalysisChunkForResponse) -> FillGameAnalysisChunk:
        start_time = datetime.datetime.now()

        # data_chunk = []
        # for game in chunk.games:
        #     tmp_request = self.game_repo.get_by_schema(game)
        #     data_chunk.append(tmp_request)

        data_chunk = list(map(self.game_repo.get_by_schema, chunk.games))

        finished_at = datetime.datetime.now()
        response_time = finished_at - start_time
        requested_games = list(map(lambda x: x[1], data_chunk))
        chunk_error_log = "\n".join(list(map(lambda x: x.error_log, requested_games)))

        chunk_request_part = GameAnalysisChunkUpdate.from_response_schema(response=chunk,
                                                                          response_time=response_time.total_seconds(),
                                                                          started_at=start_time,
                                                                          finished_at=finished_at,
                                                                          error_log=chunk_error_log,
                                                                          status="particle_success")

        return FillGameAnalysisChunk(data_for_analysis_db=GameAnalysisChunkForRequest(chunk=chunk_request_part,
                                                                                      chunk_games=requested_games),
                                     data_chunk=list(map(lambda x: x[0], data_chunk)))

    def get_add_game_info(self, chunk: GameAnalysisChunkForResponse) -> FillAddSchemaChunk:
        logger.info(
            f"\nℹ️ Starting processing chunk games with id = {chunk.id}")

        start_time = datetime.datetime.now()
        # data_chunk = []
        # for game in chunk.games:
        #     tmp_request = self.game_repo.get_by_schema(game)
        #     data_chunk.append(tmp_request)

        data_chunk = list(map(self.game_repo.get_add_info, chunk.games))

        finished_at = datetime.datetime.now()
        response_time = finished_at - start_time
        requested_games = list(map(lambda x: x[1], data_chunk))
        chunk_error_log = "\n".join(list(map(lambda x: x.error_log, requested_games)))

        chunk_request_part = GameAnalysisChunkUpdate.from_response_schema(response=chunk,
                                                                          response_time=response_time.total_seconds(),
                                                                          started_at=start_time,
                                                                          finished_at=finished_at,
                                                                          error_log=chunk_error_log,
                                                                          status="success")

        return FillAddSchemaChunk(data_for_analysis_db=GameAnalysisChunkForRequest(chunk=chunk_request_part,
                                                                                chunk_games=requested_games),
                                  data_chunk=list(map(lambda x: x[0], data_chunk)))

    def get_game_timed_data(self, app_ids: list[int]) -> FillTypeSchemaChunk:
        start_time = datetime.datetime.now()
        data_chunck = {}
        success_count = 0

        for app_id in app_ids:
            news = self.game_repo.get_news(app_id)
            achiev_persentage = self.game_repo.get_achiev_persentage(app_id)
            # global_stats = self.game_repo.get_global_stats(app_id, ..)
            number_of_players = self.game_repo.get_number_of_players(app_id)
            reviews = self.game_repo.get_reviews(app_id, limit=50)
            if news is not None or achiev_persentage is not None or number_of_players is not None or reviews is not None:
                success_count += 1

            data = TypeAnalysesSchema(
                news=news,
                achiev_persentage=achiev_persentage,
                number_of_players=number_of_players,
                reviews=reviews
            )
            data_chunck[app_id] = data

        response_time = datetime.datetime.now() - start_time

        return FillTypeSchemaChunk(
            app_ids=app_ids,
            start_time=start_time,
            data_chunck=data_chunck,
            response_time=response_time,
            success_count=success_count
        )

    @staticmethod
    def get_first_app_id():
        return resource_manager.get_resource(ResourceCodes.GAME_LIST).get_first_app_id()

    # def collect_categories(self, coll_info):
    #
    #     dump_categories = self.resource_manager.get_resource_data(ResourceCodes.GAME_CATEGORIES)
    #
    #     if not dump_categories: dump_categories = {}
    #     offset, size = coll_info
    #     g_list = self.game_repo.get_game_list(offset, size)
    #
    #     for game_info in g_list:
    #
    #         t = self.game_repo.get_by_id(game_info.app_id)
    #
    #         if not t: continue
    #
    #         for category in t.categories:
    #             dump_categories[str(category["id"])] = category["description"]
    #
    #     self.resource_manager.update_resource(ResourceCodes.GAME_CATEGORIES, dump_categories)

    def get_all_app_ids(self) -> list[int]:
        """Возвращает все app_id из GameList ресурса"""
        game_list_resource = self.resource_manager.get_resource(ResourceCodes.GAME_LIST)
        if not game_list_resource or not game_list_resource.data:
            return []
        return [item['appid'] for item in game_list_resource.data]

    def get_game_list(self,
                      offset: int = 0,
                      size: int = 100):
        return self.game_repo.get_game_list(offset, size)

    def _calculate_avg_playtime(self, reviews: List[Dict[str, Any]]) -> float:
        playtimes = [r.get('author', {}).get('playtime_forever', 0) for r in reviews]
        valid_playtimes = [p for p in playtimes if p > 0]
        return sum(valid_playtimes) / len(valid_playtimes) if valid_playtimes else 0
