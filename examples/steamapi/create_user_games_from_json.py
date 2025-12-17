from utils import load_api_key
from steam_analysis.app.application import AppMediator


def add_part_fill_users_games():
    api_key = load_api_key()
    app = AppMediator(steam_api_key=api_key,
                      processor_name="Lo-Lap")
    app.loads_users_games_from_jsons(folder="user_games")


if __name__ == "__main__":
    add_part_fill_users_games()
