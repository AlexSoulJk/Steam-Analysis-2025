from steam_analysis.core.schemas.analysis.friends import FriendsByGames, OrtBase, NodeWithCount, NodeBase, NodeUser, \
    NodeGame
from steam_analysis.database.facade import get_db
from steam_analysis.database.repositories import PlayerRepository, PlayerGameOwnershipRepository


class FriendsProcessor:

    def __init__(self):
        self.users = PlayerRepository()
        self.game_owner_ships = PlayerGameOwnershipRepository()

    def _conver_to_response_for_games(self, info):
        vertexes = []
        for vertex in info["nodes"]:
            if vertex["type"] == "user":
                vertexes.append(NodeUser(type=vertex["subtype"],
                                         id=vertex["id"],
                                         name=vertex["label"],
                                         steam_id=vertex["steam_id"],
                                         url=vertex["url"]))
            else:
                vertexes.append(NodeGame(id=vertex["id"], count=vertex["owned_by_friends_count"],
                                         name=vertex["label"], type=vertex["type"],
                                         app_id=str(vertex["app_id"])))

        orts = list(map(lambda x: OrtBase(source=x["source"], target=x["target"]), info["edges"]))
        return orts, vertexes

    def get_friends_by_games(self, steam_id: str):
        with get_db() as session:

            target_user = self.users.get_by_steam_id(session=session, steam_id=steam_id)

            if target_user is None:
                raise Exception(f"Unknown user please choose another user for target, or update strategy and collect "
                                f"user with steam_id {steam_id}")

            game_owned = self.game_owner_ships.get_user_owned_games(session=session, user_id=target_user.id)

            if len(game_owned) == 0:
                print(f"WARNING User with steam_id {steam_id} haven't games in database. "
                      f"May be you should update strategy and collect users")
            else:
                game_owned = list(map(lambda owning: owning.game, game_owned))

            info = self.users.get_friends_game_graph(
                session=session,
                target_user_id_stmt=target_user,
                games=game_owned
            )
            orts, vertex = self._conver_to_response_for_games(info)
            return FriendsByGames(orts=orts,
                                  nodes=vertex)
