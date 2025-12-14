from pathlib import Path
import json
from deps import validation, validate_json_strategy, get_app_mediator
from pathmanager import pm
from pydantic import ValidationError
from utils.diconteiner import conteiner
from steam_analysis.app.application import AppMediator
from steam_analysis.loader_test_data import LoaderTestData
from steam_analysis.saver_test_data import SaveTestData
from steam_analysis.core.schemas.player.player import ListPlayerShortInfo


def user_create_strategy(api_key: str, processor_name: str):
    path_strategy_json = pm.path_to_strategy_user

    with open(path_strategy_json, 'r', encoding='utf-8') as file:
        data = json.load(file)

    try:
        user_data = ListPlayerShortInfo.model_validate_json(data)

        app = get_app_mediator(api_key, processor_name)
        app.fill_analysis_user_from_json(user_data)

    except ValidationError as e:
        print(f"❌ Ошибки валидации:")
        for error in e.errors():
            print(f"  Поле: {error['loc']}, Ошибка: {error['msg']}")


def user_update_strategy(api_key: str, processor_name: str):
    path_strategy_json = pm.path_to_strategy_update_user

    with open(path_strategy_json, 'r', encoding='utf-8') as file:
        data = json.load(file)

    try:
        user_data = ListPlayerShortInfo.model_validate_json(data)

        app = get_app_mediator(api_key, processor_name)
        app.update_analysis_game_from_json(user_data)

    except ValidationError as e:
        print(f"❌ Ошибки валидации:")
        for error in e.errors():
            print(f"  Поле: {error['loc']}, Ошибка: {error['msg']}")


def user_create_to_json(api_key, processor_name):
    app = get_app_mediator(api_key, processor_name)
    saver = SaveTestData(pm.path_to_data / pm.folder_to_users)
    app.add_user_to_json(saver=saver)


def user_create_fill_database():
    app = AppMediator()
    path_save_data = pm.path_to_data
    folder_users = pm.folder_to_users
    default_loader = LoaderTestData(dir_to_load=path_save_data)
    app.loads_users_from_jsons(loader=default_loader, folder=folder_users)


def user_games_create_to_json(api_key, processor_name):
    app = get_app_mediator(api_key, processor_name)
    saver = SaveTestData(pm.path_to_data / pm.folder_to_users_games)
    app.add_user_games_to_json(saver=saver)


def user_create_games_fill_database():
    app = AppMediator()
    path_save_data = pm.path_to_data
    folder_users_games = pm.folder_to_users_games
    default_loader = LoaderTestData(dir_to_load=path_save_data)
    app.loads_users_games_from_jsons(loader=default_loader, folder=folder_users_games)
