from utils import load_api_key
from steam_analysis.app.application import AppMediator


def test_part_fill_games():
    api_key = load_api_key()
    app = AppMediator(steam_api_key=api_key,
                      processor_name="AlexSoulJK")
    app.loads_data_from_jsons()


if __name__ == "__main__":
    test_part_fill_games()
