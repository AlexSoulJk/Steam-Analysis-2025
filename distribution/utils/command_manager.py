from typing import Dict, Any

from distribution.calculation import calculate_for_task
from distribution.games import collect_create_peaks, create_peaks_fill_database, create_games_for_strategy, \
    games_update_strategy, games_create_add_info_json, games_create_games_json, games_create_fill_database, \
    games_create_add_info_fill_database
from distribution.user import user_create_strategy, user_update_strategy, \
    user_create_to_json, user_games_create_to_json, \
    user_create_fill_database, user_create_games_fill_database
from distribution.google_load import google_load
from distribution.utils.command_schemas import BaseConfigCommandSchema, VisualizeConfig, \
    GoogleLoadConfig, CalculateConfig
from distribution.pathmanager import pm
from distribution.visualization import visualization_handler

ROUTE_MAP: Dict[str, Any] = {
    "create_strategy": {
        "Player": create_strategy_player,
        "Game": create_games_for_strategy
    },
    "update_strategy": {
        "Player": update_strategy_player,
        "Game": games_update_strategy
    },
    "collect_data": {
        "Player": {
            0: user_games_create_to_json,
            1: games_create_add_info_json,
        },
        "Game": {
            0: games_create_games_json,
            1: games_create_add_info_json
        }
    },
    "fill_analys_db_peeks": create_peaks_fill_database,
    "collect_data_peeks": collect_create_peaks,
    "fill_analys_db": {
        "Player": {
            0: user_create_fill_database,
            1: user_create_games_fill_database,
        },
        "Game": {
            0: games_create_fill_database,
            1: games_create_add_info_fill_database
        }
    },
    "calculate": calculate_for_task,
    "google_load": google_load,
    "visualize": visualization_handler,
}

PM_DIRECT_MAP = {
    "create_strategy": {"path_to_data": pm.path_to_strategy},
    "update_strategy": {"path_to_data": pm.path_to_strategy},

    "collect_data": {
        "path_to_save": pm.path_to_data,
    },
    "collect_data_peeks": {
        "path_to_save": pm.path_to_peak_pages,
    },

    "fill_analys_db": {"path_to_load":
                           pm.path_to_data},

    "fill_analys_db_peeks": {"path_to_load":
                                 pm.path_to_peak_pages},

    "calculate": {"path_to_save": pm.path_to_data},
    "google_load": {
        "credentials_path": pm.credentials_path
    },

    "visualize": {
        "path_to_save": pm.path_to_save,
        "path_to_data": pm.path_to_data
    }
}


def pm_manager_manipulation(config_model: BaseConfigCommandSchema):
    command = config_model.command

    if command not in PM_DIRECT_MAP:
        return

    mapping = PM_DIRECT_MAP[command]
    values = config_model.dict()

    for config_field, pm_field in mapping.items():
        if config_field in values:
            mapping[config_field] = values[config_field]  # Меняем значение в словаре!


def set_qwery_args_for_level_one(func, config_model: BaseConfigCommandSchema):
    command = config_model.command
    if command == "calculate":
        config_model: CalculateConfig = config_model
        info = func(task=config_model.task, graphs=config_model.graph)
    elif command == "visualize":
        config_model: VisualizeConfig = config_model
        info = func(tasks=config_model.task, graphs=config_model.graph)
    elif command == "google_load":
        config_model: GoogleLoadConfig = config_model
        info = func(spreadsheet_url=config_model.spreadsheet_url,
                    tasks=config_model.task,
                    graphs=config_model.graph)
    elif command in ["fill_analys_db_peeks", "collect_data_peeks"]:
        info = func()
    else:
        info = f"What, how you alive? with wrong command {command}"
    return info


def set_qwery_args_for_level_two(func, config_model: BaseConfigCommandSchema):
    return func()


def set_qwery_args_for_level_third(func, config_model: BaseConfigCommandSchema):
    return func()


def get_result(config_model: BaseConfigCommandSchema):
    command = config_model.command

    level_one = ROUTE_MAP[command]
    pm_manager_manipulation(config_model)

    if isinstance(level_one, Dict):
        level_two = level_one[config_model.subject]
        if isinstance(level_two, Dict):
            level_third = level_two[config_model.stage]
            info = set_qwery_args_for_level_third(level_third, config_model)
        else:
            info = set_qwery_args_for_level_two(level_two, config_model)
    else:
        info = set_qwery_args_for_level_one(level_one, config_model)

    return info
