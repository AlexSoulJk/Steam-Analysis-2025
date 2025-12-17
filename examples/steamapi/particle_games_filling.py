from examples.steamapi.utils import load_api_key
from steam_analysis.app.application import AppMediator


def add_part_fill_games():
    api_key = load_api_key()
    app = AppMediator(steam_api_key=api_key,
                      processor_name="AlexSoulJK")
    for _ in range(10):
        # app.add_schema()
        app.add_schema_to_json(filename="games_add_info_chunk")


if __name__ == "__main__":
    add_part_fill_games()
