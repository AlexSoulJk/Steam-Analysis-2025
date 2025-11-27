from steam_analysis import PlayerRepository
from steam_analysis.core.dependencies.basehttp import RequestsWithDelayClient
from steam_analysis.core.services.player_analysis_provider import ProviderForPlayerAnalysis
from steam_analysis.resourcemanager.resources.user_list import UserList


class PlayerListCreator:

    def __init__(self, api_key: str):
        self.player_analysis_provider = ProviderForPlayerAnalysis(
            PlayerRepository(RequestsWithDelayClient(delay=0.5), api_key))

    def fill_current_list(self, player_list_resource: UserList):
        # TODO: Can be optimized
        last_unfilled = player_list_resource.get_last_unfilled_user()
        req = self.player_analysis_provider.get_players_for_create(core_steam_id=last_unfilled["steam_id"],
                                                                   depth=2)
        player_list_resource.update_list(req)
