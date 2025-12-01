import os
from pathlib import Path
from steam_analysis.app.processed_data_provider import ProcessedDataProvider


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
        self.logger = set_logger("Steam_Analysis_App")
        self._prepare_paths()

    def _prepare_paths(self):
        os.makedirs(self.path_to_save_work, exist_ok=True)
        os.makedirs(self.folder_clustering)

    def generate_distribution_by_type(self):

        path_for_type = self.folder_clustering / Path("distribution.png")
        data_for_response = self.data_provider.get_games_by_types()

        if data_for_response:
            from steam_analysis.analysis.utils import generate_clustering_task_picture
            generate_clustering_task_picture.generate_distribution_by_feature(data=data_for_response,
                                                                              title_name=self.TITLES["Clustering"][
                                                                                  "ByType"],
                                                                              path_to_save=path_for_type)
        else:
            self.logger.warning("Пустота в данных распределения по типам приложений! Обратитесь к авторам софта)")
