from utils import load_api_key
from steam_analysis.app.application import AppMediator


def add_part_fill_games():
    api_key = load_api_key()
    app = AppMediator(steam_api_key=api_key,
                      processor_name="AlexSoulJK")
    app.loads_add_data_game_from_jsons()


if __name__ == "__main__":
    add_part_fill_games()
