from typing import Dict, List

from steam_analysis import PlayerRepository
from steam_analysis.core.schemas.player.service import PlayerAnalysisForJson


class ProviderForPlayerAnalysis:

    def __init__(self, player_repos: PlayerRepository):
        self.player_repos = player_repos

    def _collect_friends_recursive(self, core_steam_id: str,
                                   depth: int,
                                   visited_dict: dict):

        user = visited_dict.get(core_steam_id, None)
        if user is None:
            visited_dict[core_steam_id] = "unfilled"
        else:
            return

        if depth <= 0:
            return

        try:
            friends = self.player_repos.get_friends(core_steam_id)
            friend_ids = [friend.get('steamid') for friend in friends if friend.get('steamid')]

            for friend_id in friend_ids:
                self._collect_friends_recursive(friend_id, depth - 1, visited_dict)

            visited_dict[core_steam_id] = "filled"
        except Exception as e:
            print(f"Error getting friends for {core_steam_id}: {e}")
            visited_dict[core_steam_id] = "close_f_list"



    def _convert_to_save_model(self, visited_dict: dict, batch_size: int = 100) -> List[PlayerAnalysisForJson]:

        user_friends_filled = list(filter(lambda x: x[1] in ["filled", "close_f_list"], visited_dict.items()))
        user_friends_unfilled = list(filter(lambda x: x[1] == "unfilled", visited_dict.items()))
        res = list(map(lambda x: PlayerAnalysisForJson.create_without_friends(steam_id=x[0]),
                       user_friends_unfilled))

        size = len(user_friends_filled)
        num_batches = (size + batch_size - 1) // batch_size  # Это ключевая строка!

        butches = [user_friends_filled[i * batch_size:(i + 1) * batch_size] for i in range(num_batches)]


        for butch in butches:
            players = self.player_repos.get_by_ids(list(map(lambda x: x[0], butch)))
            players = list(map(lambda x: PlayerAnalysisForJson(persona_name=x["personaname"],
                                                               status="filled",
                                                               steam_id=x["steamid"]), players))
            res.extend(players)

        return res

    def get_players_for_create(self, core_steam_id: str, depth: int) -> List[PlayerAnalysisForJson]:

        if depth <= 0:
            return []

        visited_dict: Dict[str] = {core_steam_id: None}

        self._collect_friends_recursive(core_steam_id, depth, visited_dict)

        return self._convert_to_save_model(visited_dict)
