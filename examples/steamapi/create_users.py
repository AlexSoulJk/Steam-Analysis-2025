import datetime
from time import sleep

from utils import load_api_key, load_api_keys
from steam_analysis.app.application import AppMediator


def main():
    api_key = load_api_key()

    app = AppMediator(steam_api_key=api_key,
                      processor_name="Lo-Lap")
    # sleep(180)
    for i in range(2000):
        # app.create_user()
        app.add_user_to_json(filename="users")

    # app.create_user_game()


if __name__ == "__main__":
    main()
