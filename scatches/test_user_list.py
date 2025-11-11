from examples.steamapi.utils import load_api_key
from steam_analysis import PlayerRepository
from steam_analysis.core.dependencies.basehttp import RequestsWithDelayClient
from steam_analysis.core.services.player_analysis_provider import ProviderForPlayerAnalysis
from steam_analysis.core.services.player_list_creator import PlayerListCreator
from steam_analysis.resourcemanager.manager import resource_manager
from steam_analysis.resourcemanager.resources.codes import ResourceCodes
from steam_analysis.resourcemanager.resources.user_list import UserList


def main_friends_list():
    api_key = load_api_key()
    pr = PlayerRepository(RequestsWithDelayClient(delay=0.5), api_key)
    print(pr.get_friends("76561198287722531"))
    pass


def check_fill_user_list():
    api_key = load_api_key()
    pr = PlayerRepository(RequestsWithDelayClient(delay=0.5), api_key)
    pf = ProviderForPlayerAnalysis(pr)
    player_list_resource: UserList = resource_manager.get_resource(ResourceCodes.USER_LIST)
    req = pf.get_players_for_create(core_steam_id=player_list_resource.get_last_unfilled_user()["steam_id"],
                                    depth=3)


def check_player_list_creator():
    api_key = load_api_key()
    plc = PlayerListCreator(api_key)
    plc.fill_current_list()


def main():
    player_list_resource: UserList = resource_manager.get_resource(ResourceCodes.USER_LIST)
    print(player_list_resource.get_last_unfilled_user())


if __name__ == "__main__":
    # main_friends_list()
    # main()
    # check_fill_user_list()
    check_player_list_creator()
    # print(101//100)
