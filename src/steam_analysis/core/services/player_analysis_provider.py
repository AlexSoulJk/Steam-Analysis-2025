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
            user = ["unfilled", []]
        else:
            return

        try:
            friends = self.player_repos.get_friends(core_steam_id)
            friend_ids = [friend.get('steamid') for friend in friends if friend.get('steamid')]

            if depth <= 0:
                user[1] = friend_ids
                visited_dict[core_steam_id] = user
                return

            for friend_id in friend_ids:
                self._collect_friends_recursive(friend_id, depth - 1, visited_dict)

            user[0] = "filled"
            user[1] = friend_ids

        except Exception as e:
            print(f"Error getting friends for {core_steam_id}: {e}")
            user[0] = "close_f_list"
            user[1] = None

        visited_dict[core_steam_id] = user

    def _remark_post_process(self, visited_dict: dict):

        unfilled_users = list(filter(lambda x: x[1][0] == "unfilled", visited_dict.items()))
        all_ids = set(visited_dict.keys())
        # can_be_added = set()
        for unfilled_user in unfilled_users:
            friends_ids = unfilled_user[1][1]

            need_add = list(filter(lambda x: x not in all_ids, friends_ids))
            size_need_add = len(need_add)

            if size_need_add == 0:
                visited_dict[unfilled_user[0]][0] = "filled"
            # else:
            #     for need_add_id in need_add:
            #         visited_dict[need_add_id] = ["unfilled", []]

            # if size_need_add/len(friends_ids) < 0.15:
            #     for need_add_id in need_add:
            #         can_be_added.add(need_add_id)





    def _convert_to_save_model(self, visited_dict: dict, batch_size: int = 100) -> List[PlayerAnalysisForJson]:

        res = []
        visited_users = list(visited_dict.items())
        size = len(visited_users)
        num_batches = (size + batch_size - 1) // batch_size  # Это ключевая строка!

        butches = [visited_users[i * batch_size:(i + 1) * batch_size] for i in range(num_batches)]

        for butch in butches:
            players = self.player_repos.get_by_ids(list(map(lambda x: x[0], butch)))
            players = list(map(lambda x: PlayerAnalysisForJson(persona_name=x["personaname"],
                                                               status=visited_dict[x["steamid"]],
                                                               steam_id=x["steamid"]), players))
            res.extend(players)

        return res

    def get_players_for_create_small(self, steam_ids: list[str]):

        visited_dict: Dict[str] = {core_steam_id: "unfilled" for core_steam_id in steam_ids}

        for core_steam_id in steam_ids:
            self._collect_friends_recursive(core_steam_id, 1, visited_dict)

        return self._convert_to_save_model(visited_dict)

    def get_players_for_create(self, core_steam_id: str, depth: int) -> List[PlayerAnalysisForJson]:

        if depth <= 0:
            return []

        visited_dict: Dict[str] = {core_steam_id: None}

        self._collect_friends_recursive(core_steam_id, depth, visited_dict)
        self._remark_post_process(visited_dict)
        return self._convert_to_save_model({key: status for key, [status, friends] in visited_dict.items()})
