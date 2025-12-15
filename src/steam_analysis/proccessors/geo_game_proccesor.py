from typing import List

from sqlalchemy import func, distinct

from steam_analysis.core.schemas.analysis.geoshemas import CountryGameStat, ListCountryGameStat
from steam_analysis.database.facade import get_db
from steam_analysis.database.models import User
from steam_analysis.database.repositories import GameRepository, PlayerRepository
from steam_analysis.database.repositories.game.category import CategoryRepository
from steam_analysis.database.repositories.game.type import TypeRepository


def distinct_user_count():
    return func.count(distinct(User.id))

class GeoProccessor:

    def __init__(self):
        self.game_repo = GameRepository()
        self.game_type_repo = TypeRepository()
        self.categories = CategoryRepository()
        self.users = PlayerRepository()

    def get_games_by_geo(self, game_limit) -> ListCountryGameStat:
        with get_db() as session:
            stats = self.users.get_country_game_stats(
                session=session,
                with_geo=True,
                min_count=5,
                top_n=game_limit,
                count_expr_factory=distinct_user_count,
                result_schema=CountryGameStat
            )
            return ListCountryGameStat(data=stats)
