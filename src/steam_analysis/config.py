import os
from pathlib import Path

from distribution.pathmanager import DEFAULT_PATH_FOR_RES_DATA, PROJECT_PATH

db_path = DEFAULT_PATH_FOR_RES_DATA / Path("db/steam_analysis.db")
print(f"Path to main db {db_path}")
test_data_path = f"{PROJECT_PATH}/test_data"
test_data_add_game_path = f"{PROJECT_PATH}/test_data/add_info_games"
test_game_path = f"{PROJECT_PATH}/test_data/games"
test_data_add_user = f"{PROJECT_PATH}/test_data/users"
test_add_user_games = f"{PROJECT_PATH}/test_data/user_games"

analysis_db_path = DEFAULT_PATH_FOR_RES_DATA / Path("db-analysis/db_analytics.db")

examples_statistics_images_path = f"{PROJECT_PATH}/examples/statistics samples/images"