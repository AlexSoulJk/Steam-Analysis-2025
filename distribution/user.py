from pathlib import Path
from deps import validation, validate_json_strategy, get_app_mediator
from pathmanager import pm
from pathmanager import DEFAULT_FILE_APP_IDS, DEFAULT_FILE_BATCHES_APP_IDS
from utils.diconteiner import conteiner
from steam_analysis.app.application import AppMediator
from steam_analysis.loader_test_data import LoaderTestData
from steam_analysis.saver_test_data import SaveTestData


def user_create_strategy():
    # json
    pass


def user_create_to_json(api_key, processor_name):
    app = get_app_mediator(api_key, processor_name)
    saver = SaveTestData(pm.folder_to_users)
    app.add_user_to_json(saver=saver)


def user_create_fill_database():
    pass


def create_user_games_to_json(api_key, processor_name):
    app = get_app_mediator(api_key, processor_name)
    saver = SaveTestData(pm.folder_to_users_games)
    app.add_user_games_to_json(saver=saver)


def user_create_games_fill_database():
    # json
    pass
