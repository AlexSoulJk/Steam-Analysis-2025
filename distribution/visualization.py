import os
from typing import List

from distribution.pathmanager import pm, DEFAULT_FOLDER_CLUSTERING, DEFAULT_FOLDER_FRIENDS_TASKS
from steam_analysis.analysis.finalapplication import Application
from steam_analysis.config import examples_statistics_images_path
from steam_analysis.saver_test_data import SaveTestData
from steam_analysis.loader_test_data import LoaderTestData


def task_1(app: Application, graphs):
    # Тут лоадинг
    GRAPHS_HENDLERS = {0: app.load_clustering}
    for graph in graphs:
        loader_clustering = LoaderTestData("")
        GRAPHS_HENDLERS[graph](loader_clustering)


def task_2(app: Application, graphs):
    GRAPHS_HENDLERS = {0: app.load_distribution_by_price_genre,
                       1: app.load_distribution_by_price_category}
    for graph in graphs:
        loader = LoaderTestData("")
        GRAPHS_HENDLERS[graph](loader)

def task_3(app: Application, graphs):
    GRAPHS_HENDLERS = {0: app.calculate_geo_games, 1: app.calculate_geo_categories}
    for graph in graphs:
        GRAPHS_HENDLERS[graph]()


def visualize_for_task(task: int, graphs: List[int]):
    app = Application(examples_statistics_images_path)
    TASKS = {1: task_1,
             2: task_2,
             3: task_3}
    return TASKS[task](app, graphs)


if __name__ == "__main__":
    # calculate_for_task(4, [0])
    visualize_for_task(2, [0])
