from typing import List

from .pathmanager import pm
from steam_analysis.analysis.finalapplication import Application
from steam_analysis.config import examples_statistics_images_path
from steam_analysis.loader_test_data import LoaderTestData


def task_3(app: Application, graphs):
    GRAPHS_HENDLERS = {0: app.calculate_geo_games, 1: app.calculate_geo_categories}
    for graph in graphs:
        GRAPHS_HENDLERS[graph]()


def task_4(app: Application, graphs, spreadsheet_url):
    GRAPHS_HENDLERS = {0: app.load_geo_games, 1: app.calculate_geo_categories}
    for graph in graphs:
        loader_geo_game = LoaderTestData("")
        GRAPHS_HENDLERS[graph](loader_geo_game, spreadsheet_url)


def task_5(app: Application, graphs, spreadsheet_url):
    GRAPHS_HENDLERS = {0: app.load_friends_graphs_by_games}
    for graph in graphs:
        loader_friends_game = LoaderTestData("")
        GRAPHS_HENDLERS[graph](loader_friends_game, spreadsheet_url)


def google_load(task: int, graphs: List[int], spreadsheet_url: str):
    app = Application(examples_statistics_images_path)
    TASKS = {4: task_4, 5: task_5}

    return TASKS[task](app, graphs, spreadsheet_url)

spreadsheet_url_ = "https://docs.google.com/spreadsheets/d/1w-ojS7k00hRTdEKqRa8fF-fOkBAQ0dPxMASBMVlJgLs/edit?usp=sharing"
pm._path_to_google_token = r"C:\Users\Hp\PycharmProjects\Steam-Analysis-2025\google_token.json"
spreadsheet_foled = "1CTi4qxH6TXQbnOwGHz7TbDZOteeXliQ3"
# google_load(4, [0], spreadsheet_url)
# google_load(5, [0], spreadsheet_foled)