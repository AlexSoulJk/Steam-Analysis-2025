from enum import Enum
from typing import Optional

from steam_analysis.database.facade import get_db
from steam_analysis.database.repositories import GameRepository
from steam_analysis.database.repositories.game.type import TypeRepository
from steam_analysis.database.repositories.game.category import CategoryRepository

from steam_analysis.proccessors.schemas.games import GamesByTypes, GamesByCategories, GamesByCountCategoriesWithSubs, \
    GamesByGenres, GamesReleaseBySeason, GameFeatureVector, GamesClusteringData, TwoDHistogramData, EnhancedHistogramData


class SeasonMode(str, Enum):
    monthly = "monthly"
    quarter = "quarter"


LABELS = {

        "monthly": {
                1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
                5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
                9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
        },

        "quarter": {
                1: "Q1 (Янв-Мар)", 2: "Q2 (Апр-Июн)",
                3: "Q3 (Июл-Сен)", 4: "Q4 (Окт-Дек)"
        }
    }

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

    def get_games_by_genres(self) -> Optional[GamesByGenres]:
        ret = None
        with get_db() as session:
            genres = self.categories.get_multi(session=session)
            genres_dict = {genre.id: genre.description for genre in genres}
            ticks = list(map(lambda x: x.description, genres))
            values = self.game_repo.count_games_by_genres_for_type(session=session)
            values = {genres_dict[value[0]]: value[1] for value in values}
            ret = GamesByGenres(ticks=ticks,
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

    def get_games_release_by_season(self, code: SeasonMode = SeasonMode.monthly) -> Optional[GamesReleaseBySeason]:
        values = None

        with get_db() as session:
            values, ticks = self.game_repo.get_games_release_by_season(session=session,
                                                                        season_mode=code)
            values = {LABELS[code][int(value[0])]: value[1] for value in values.items()}
            ticks = list(map(lambda tick: LABELS[code][int(tick)], ticks))
        return GamesReleaseBySeason(values=values, ticks=ticks)


    # дальше по кластерзации

    def get_game_clustering_data(self) -> Optional[GamesClusteringData]:
        with get_db() as session:
            vals = self.game_repo.get_game_feature_vector(session=session) # в цикле затолкать в GamesClusteringData
        pass


    def get_2d_hist_data(self) -> Optional[TwoDHistogramData]:
        with get_db() as session:
            vals = self.game_repo.get_2d_hist_data(session=session) # в цикле затолкать в GamesClusteringData
        pass

