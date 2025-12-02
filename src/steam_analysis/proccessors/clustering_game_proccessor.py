from typing import Optional

from steam_analysis.database.facade import get_db
from steam_analysis.database.repositories import GameRepository
from steam_analysis.database.repositories.game.type import TypeRepository
from steam_analysis.database.repositories.game.category import CategoryRepository

from steam_analysis.proccessors.schemas.games import GamesByTypes, GamesByCategories, GamesByCountCategoriesWithSubs


class ClusteringGameProcessor:  # ЭТО СЕРВИС: ПООБЩАЛСЯ С БАЗОЙ И СОБРАЛ ДАННЫЕ ДЛЯ КЛАСТЕРИЗАЦИИ И ОТДАЛ В ПРОВАЙДЕР (ФАСАД)

    def __init__(self):
        self.game_repo = GameRepository()
        self.game_type_repo = TypeRepository()
        self.categories = CategoryRepository()

    def get_games_by_types(self) -> Optional[GamesByTypes]:
        ret = None
        with get_db() as session:
            types = self.game_type_repo.get_multi(session=session)
            ticks = list(map(lambda x: x.description, types))
            values = {type.description: self.game_repo.count(session=session, filters={"type_id": type.id})
                      for type in types}
            ret = GamesByTypes(ticks=ticks,
                               values=values)
        return ret

    def get_games_by_categories(self) -> Optional[GamesByCategories]:
        ret = None
        with get_db() as session:
            categories = self.categories.get_multi(session=session)
            categories_dict = {category.id: category.description for category in categories}
            ticks = list(map(lambda x: x.description, categories))
            values = self.game_repo.count_games_by_categories_for_type(session=session)
            values = {categories_dict[value[0]]: value[1]for value in values}
            ret = GamesByCategories(ticks=ticks,
                                    values=values)
        return ret

    def get_games_by_categories_count(self) -> Optional[GamesByCountCategoriesWithSubs]:

        values = None

        with get_db() as session:
            values = self.game_repo.get_games_by_category_combinations_sql(session=session, max_category_count=15)

        return values

