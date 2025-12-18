from examples.steamapi.utils import load_api_key
from steam_analysis.app.application import AppMediator


def main():
    api_key = load_api_key()
    app = AppMediator(steam_api_key=api_key)

    for i in range(10000):
        app.fill_analysis_game()

if __name__ == "__main__":
    main()