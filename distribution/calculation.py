import os
from typing import List

from distribution.pathmanager import pm, DEFAULT_FOLDER_GEO_TASKS, \
    DEFAULT_FOLDER_FRIENDS_TASKS, DEFAULT_FOLDER_CLUSTERING, DEFAULT_FOLDER_DISTRIBUTION_BY_PRICE
from steam_analysis.analysis.finalapplication import Application
from steam_analysis.config import examples_statistics_images_path
from steam_analysis.saver_test_data import SaveTestData


def task_1(app: Application, graphs):
    GRAPHS_HENDLERS = {0: app.calculate_game_clustering}
    for graph in graphs:
        func = GRAPHS_HENDLERS[graph]
        path_to_graph_folder = pm.folder_to_task_save / DEFAULT_FOLDER_CLUSTERING
        os.makedirs(path_to_graph_folder, exist_ok=True)
        saver = SaveTestData(path_to_graph_folder)
        func(saver)


def task_2(app: Application, graphs):
    GRAPHS_HENDLERS = {0: app.calculate_distribution_by_price_genre,
                       1: app.calculate_distribution_by_price_category}
    for graph in graphs:
        func = GRAPHS_HENDLERS[graph]
        path_to_graph_folder = pm.folder_to_task_save / DEFAULT_FOLDER_DISTRIBUTION_BY_PRICE
        os.makedirs(path_to_graph_folder, exist_ok=True)
        saver = SaveTestData(path_to_graph_folder)
        func(saver)


def task_3(app: Application, graphs):
    GRAPHS_HENDLERS = {0: app.calculate_geo_games, 1: app.calculate_geo_categories}
    for graph in graphs:
        GRAPHS_HENDLERS[graph]()


def task_4(app: Application, graphs):
    GRAPHS_HENDLERS = {0: app.calculate_geo_games, 1: app.calculate_geo_categories}
    for graph in graphs:
        func = GRAPHS_HENDLERS[graph]
        path_to_graph_folder = pm.folder_to_task_save / DEFAULT_FOLDER_GEO_TASKS
        os.makedirs(path_to_graph_folder, exist_ok=True)
        saver = SaveTestData(path_to_graph_folder)
        func(saver)


def task_5(app: Application, graphs):
    GRAPHS_HENDLERS = {0: app.calculate_friends_graphs_by_games}
    for graph in graphs:
        func = GRAPHS_HENDLERS[graph]
        path_to_graph_folder = pm.folder_to_task_save / DEFAULT_FOLDER_FRIENDS_TASKS
        os.makedirs(path_to_graph_folder, exist_ok=True)
        saver = SaveTestData(path_to_graph_folder)
        func(saver)


def calculate_for_task(task: int, graphs: List[int]):
    app = Application(examples_statistics_images_path)
    TASKS = {1: task_1,
             2: task_2,
             3: task_3,
             4: task_4,
             5: task_5}
    return TASKS[task](app, graphs)

# calculate_for_task(4, [0])

if __name__ == "__main__":
    calculate_for_task(2, [0])
