from steam_analysis.core.schemas.analysis.friends import FriendsByGames
from steam_analysis.database.facade import get_db
from steam_analysis.database.repositories import PlayerRepository


class FriendsProcessor:

    def __init__(self):
        self.users = PlayerRepository()

    def get_friends_by_games(self):
        with get_db() as session:
            vertex, orts = self.users.get_friends_by(
                # session=session,
                # with_geo=True,
                # min_count=5,
                # top_n=game_limit,
                # count_expr_factory=distinct_user_count,
                # result_schema=CountryGameStat
            )
            return FriendsByGames(orts=orts,
                                  users=vertex)