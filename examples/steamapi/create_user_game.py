import datetime
from time import sleep

from utils import load_api_key
from steam_analysis.app.application import AppMediator


def main():
    api_key = load_api_key()
    app = AppMediator(steam_api_key=api_key,
                      processor_name="AlexSoulJK")
    # app.create_user()
    app.create_user_game()


if __name__ == "__main__":
    main()