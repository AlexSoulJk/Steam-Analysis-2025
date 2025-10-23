import datetime
from typing import List, Dict, Any, Optional
from ..repositories.game_repository import GameRepository
from ..schemas import GameCreate
from ..schemas.game.service import GameDataAnalysisCreate, TypeAnalysesSchema, FillGameAnalysisChunk, FillTypeSchemaChunk
from ...resourcemanager.manager import resource_manager
from ...resourcemanager.resources.codes import ResourceCodes


class GameService:
    def __init__(self, game_repo: GameRepository):
        self.game_repo = game_repo
        self.resource_manager = resource_manager

    def get_game_analysis(self, app_id: int) -> Optional[Dict[str, Any]]:
        """Полный анализ игры"""
        game_data = self.game_repo.get_by_id(app_id)
        if not game_data:
            return None

        reviews = self.game_repo.get_reviews(app_id, limit=50)
        schema = self.game_repo.get_schema(app_id)

        # Анализ отзывов
        positive_reviews = [r for r in reviews if r.get('voted_up')]
        review_score = len(positive_reviews) / len(reviews) if reviews else 0

        return {
            'game_info': game_data,
            'review_analysis': {
                'total_reviews': len(reviews),
                'positive_rate': review_score,
                'average_playtime': self._calculate_avg_playtime(reviews)
            },
            'achievements_count': len(schema.get('availableGameStats', {}).get('achievements', [])) if schema else 0
        }

    def get_game_analysis_list(self, app_id: int, chunk_size: int) -> FillGameAnalysisChunk:
        app_id_list = resource_manager.get_resource(ResourceCodes.GAME_LIST).get_app_id_list(app_id, chunk_size)

        start_time = datetime.datetime.now()
        data_chunk = list(map(self.game_repo.get_by_id, app_id_list))
        elapsed_time = datetime.datetime.now() - start_time

        return FillGameAnalysisChunk(start_app_id=app_id_list[0],
                                     end_app_id=app_id_list[-1],
                                     response_time=elapsed_time,
                                     data_chunk=data_chunk)

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
            if news != None or achiev_persentage != None or number_of_players != None or reviews != None:
                success_count += 1

            data = TypeAnalysesSchema(
                news = news,
                achiev_persentage = achiev_persentage,
                number_of_players = number_of_players,
                reviews = reviews
            )
            data_chunck[app_id] = data
            
        response_time = datetime.datetime.now() - start_time

        return FillTypeSchemaChunk(
            app_ids = app_ids,
            start_time = start_time,
            data_chunck = data_chunck,
            response_time = response_time,
            success_count = success_count
        )



    @staticmethod
    def get_first_app_id():
        return resource_manager.get_resource(ResourceCodes.GAME_LIST).get_first_app_id()

    def collect_categories(self, coll_info):

        dump_categories = self.resource_manager.get_resource_data(ResourceCodes.GAME_CATEGORIES)

        if not dump_categories: dump_categories = {}
        offset, size = coll_info
        g_list = self.game_repo.get_game_list(offset, size)

        for game_info in g_list:

            t = self.game_repo.get_by_id(game_info.app_id)

            if not t: continue

            for category in t.categories:
                dump_categories[str(category["id"])] = category["description"]

        self.resource_manager.update_resource(ResourceCodes.GAME_CATEGORIES, dump_categories)

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
