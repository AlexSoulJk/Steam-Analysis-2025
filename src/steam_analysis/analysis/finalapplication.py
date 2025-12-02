import os
from pathlib import Path
from steam_analysis.app.processed_data_provider import ProcessedDataProvider
from steam_analysis.core.services.fastlogger import setup_logger
from steam_analysis.saver_test_data import default_saver


class Application:

    TITLES = {
        "Clustering": {
            "ByType": "Гистограмму"
        }
    }

    def __init__(self, path_to_save_work: Path):
        self.path_to_save_work: Path = path_to_save_work
        self.folder_clustering = self.path_to_save_work / Path("clustering")
        self.data_provider = ProcessedDataProvider()
        self.logger = setup_logger("Steam_Analysis_App")
        self._prepare_paths()

    def _prepare_paths(self):
        os.makedirs(self.path_to_save_work, exist_ok=True)
        os.makedirs(self.folder_clustering, exist_ok=True)

    def generate_distribution_by_type(self):

        path_for_type_pic = self.folder_clustering / Path("distribution_by_types.png")
        path_for_type_json = self.folder_clustering / Path("dist_by_types.json")
        data_for_response = self.data_provider.get_games_by_types()

        default_saver.save_data(data_for_response, filepath=path_for_type_json)

        if data_for_response:
            from steam_analysis.analysis.utils import generate_clustering_task_picture
            generate_clustering_task_picture.generate_distribution_by_feature(data=data_for_response,
                                                                              title_name=self.TITLES["Clustering"][
                                                                                  "ByType"],
                                                                              path_to_save=path_for_type_pic)
        else:
            self.logger.warning("Пустота в данных распределения по типам приложений! Обратитесь к авторам софта)")

    def generate_distribution_by_category(self, columns_num: int):

        path_for_type_pic = self.folder_clustering / Path("distribution_by_categories.png")
        path_for_type_json = self.folder_clustering / Path("dist_by_categories.json")
        data_for_response = self.data_provider.get_games_by_categories()

        default_saver.save_data(data_for_response, filepath=path_for_type_json)

        if data_for_response:
            from steam_analysis.analysis.utils import generate_clustering_task_picture
            generate_clustering_task_picture.generate_distribution_by_feature(data=data_for_response,
                                                                              title_name=self.TITLES["Clustering"][
                                                                                  "ByType"],
                                                                              path_to_save=path_for_type_pic,
                                                                              columns_num=columns_num)
        else:
            self.logger.warning("Пустота в данных распределения по типам приложений! Обратитесь к авторам софта)")


    def generate_distribution_by_count_category(self, columns_num):
        path_for_type_pic = self.folder_clustering / Path("distribution_by_count_categories.png")
        path_for_type_json = self.folder_clustering / Path("dist_by_count_categories.json")
        data_for_response = self.data_provider.get_games_by_categories_count()

        default_saver.save_data(data_for_response, filepath=path_for_type_json)

        if data_for_response:
            from steam_analysis.analysis.utils import generate_clustering_task_picture
            generate_clustering_task_picture.generate_distribution_by_feature(data=data_for_response,
                                                                              title_name=self.TITLES["Clustering"][
                                                                                  "ByType"],
                                                                              path_to_save=path_for_type_pic,
                                                                              columns_num=columns_num)
        else:
            self.logger.warning("Пустота в данных распределения по типам приложений! Обратитесь к авторам софта)")