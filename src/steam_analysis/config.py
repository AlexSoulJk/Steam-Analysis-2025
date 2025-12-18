import os

project_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

db_path = f"{project_path}/resources_data/db/steam_analysis.db"
test_data_path = f"{project_path}/test_data"
test_data_add_game_path = f"{project_path}/test_data/add_info_games"
test_game_path = f"{project_path}/test_data/games"
test_data_add_user = f"{project_path}/test_data/users"
test_add_user_games = f"{project_path}/test_data/user_games"

analysis_db_path = f"{project_path}/resources_data/db-analysis/db_analytics.db"
examples_statistics_images_path = f"{project_path}/examples/statistics samples/images"