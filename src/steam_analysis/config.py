import os

project_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

db_path = f"{project_path}/resources_data/db/steam_analysis.db"
test_data_path = f"{project_path}/test_data"

analysis_db_path = f"{project_path}/resources_data/db-analysis/db_analytics.db"