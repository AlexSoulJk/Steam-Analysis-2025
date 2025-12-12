import datetime
from time import sleep

from utils import load_api_key
from steam_analysis.app.application import AppMediator


def main():
    api_key = load_api_key()
    app = AppMediator(steam_api_key=api_key,
                      processor_name="Lo-Lap")
    # app.create_user()
    for i in range(3):
        # app.create_game()
        app.add_game_to_json()

    # api_keys = load_api_keys()
    # apps = []
    # for api_key in api_keys:
    #     apps.append(AppMediator(steam_api_key=api_key,
    #                       processor_name="Ekaterina Lips"))
    # butch_per_3_minute = len(api_keys) * 4 + 1
    # sleep(300)
    # start_time = datetime.datetime.now()
    #
    # for i in range(1, 3600-1186):
    #     if (i % butch_per_3_minute) != 0:
    #         index = i % butch_per_3_minute
    #         app = apps[(index - 1) // 4]
    #         print(f"Chunk {i} {app.steam_api_key}")
    #         app.create_game()
    #     else:
    #         elapsed_time = (datetime.datetime.now() - start_time).seconds
    #         print(f"Now is {i} and we will sleep {300 - elapsed_time}")
    #         sleep(300 - elapsed_time)
    #         start_time = datetime.datetime.now()

if __name__ == "__main__":
    main()
    # butc = 13
    # for i in range(1, 100):
    #     if (i % butc) != 0:
    #         index = i % butc
    #         print(f"{(index - 1) // 4}")
    # start_time = datetime.datetime.now()
    # sleep(1)
    # elapsed_time = (datetime.datetime.now() - start_time).seconds
    # print(elapsed_time)