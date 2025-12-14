from pathlib import Path
import json
from deps import validation, validate_json_strategy, get_app_mediator
from pydantic import ValidationError
from pathmanager import pm
from pathmanager import DEFAULT_FILE_APP_IDS, DEFAULT_FILE_BATCHES_APP_IDS
from steam_analysis.app.application import AppMediator
from steam_analysis.loader_test_data import LoaderTestData
from steam_analysis.saver_test_data import SaveTestData
from steam_analysis.steamcharts.collect_app_id import SteamAppIdCollector
from steam_analysis.steamcharts.steamcharts import SteamChartsPipeline
from steam_analysis.steamcharts.steamcharts_repository import SteamChartsRepository
from steam_analysis.core.schemas.game.game import GameListFromJson


def create_games_for_strategy(api_key: str, processor_name: str):
    path_strategy_json = pm.path_to_strategy_game

    with open(path_strategy_json, 'r', encoding='utf-8') as file:
        data = json.load(file)

    try:
        games_data = GameListFromJson.model_validate_json(data)

        app = get_app_mediator(api_key, processor_name)
        app.fill_analysis_game_from_json(games_data)

    except ValidationError as e:
        print(f"❌ Ошибки валидации:")
        for error in e.errors():
            print(f"  Поле: {error['loc']}, Ошибка: {error['msg']}")


def games_update_strategy(api_key, processor_name):
    path_strategy_json = pm.path_to_strategy_update_game

    with open(path_strategy_json, 'r', encoding='utf-8') as file:
        data = json.load(file)

    try:
        games_data = GameListFromJson.model_validate_json(data)

        app = get_app_mediator(api_key, processor_name)
        app.update_analysis_game_from_json(games_data)

    except ValidationError as e:
        print(f"❌ Ошибки валидации:")
        for error in e.errors():
            print(f"  Поле: {error['loc']}, Ошибка: {error['msg']}")


def games_create_games_json(api_key, processor_name):
    # нужна валидация api_key
    app = get_app_mediator(api_key, processor_name)
    saver = SaveTestData(pm.path_to_data / pm.folder_to_games)
    app.add_game_to_json(saver=saver)


def games_create_fill_database():
    app = AppMediator()
    path_load_data = pm.path_to_load
    folder_games = pm.folder_to_games
    default_loader = LoaderTestData(dir_to_load=path_load_data)
    app.loads_games_from_jsons(loader=default_loader, folder=folder_games)


def get_app_ids():
    collector_app_ids = SteamAppIdCollector(output_file=DEFAULT_FILE_APP_IDS)
    collector_app_ids.collect_pages(start_page=1, end_page=517)
    collector_app_ids.print_stats()


def collect_create_peaks():
    app_ids = SteamAppIdCollector.read_app_ids_from_json(pm.file_peak_app_ids)
    games = SteamChartsPipeline.save_games_in_batches(all_games=app_ids,
                                                      base_filename=DEFAULT_FILE_BATCHES_APP_IDS)
    peak = SteamChartsPipeline(games=games)
    peak.processed_batches()


def create_peaks_fill_database():
    chart_repo = SteamChartsRepository()
    chart_repo.read_jsons(pm.path_to_peak_pages)
    chart_repo.add_files_to_db()


def games_create_add_info_json(api_key, processor_name):
    # нужна валидация api_key
    app = get_app_mediator(api_key, processor_name)
    saver = SaveTestData(pm.path_to_data / pm.folder_to_games_add_info)
    app.add_schema_to_json(saver=saver)


def games_create_add_info_fill_database():
    app = AppMediator()
    path_save_data = pm.path_to_load
    folder_games_add_info = pm.path_to_save_add_info
    default_loader = LoaderTestData(dir_to_load=path_save_data)
    app.loads_add_data_game_from_jsons(loader=default_loader, folder=folder_games_add_info)
