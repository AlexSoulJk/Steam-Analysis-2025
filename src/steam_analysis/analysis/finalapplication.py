import os
from pathlib import Path
import numpy as np
from typing import List

from steam_analysis.app.processed_data_provider import ProcessedDataProvider
from steam_analysis.core.services.fastlogger import setup_logger
from steam_analysis.saver_test_data import default_saver

from steam_analysis.analysis.response_schemas.graphics import HistogramAnalysisResult, GroupedHistogramData, \
CorrelationHeatmapData

class Application:
    TITLES = {
        "Clustering": {
            "ByType": "Распределение собранных данных по типам ",
            "ByCategory": "Распределение игр по категориям",
            "BySeason": "Количество выпущенных по сезонам игр за всё время",
            "PriceByCategory": "Распределение цен по категориям",
            "PriceByGenre": "Распределение цен по жанрам",
            "CategoryDynamics": "Динамика выпуска игр по категориям",
            "GenreDynamics": "Динамика выпуска игр по жанрам"
        },
    }

    def __init__(self, path_to_save_work: Path):
        self.path_to_save_work: Path = path_to_save_work
        self.folder_clustering = self.path_to_save_work / Path("clustering")
        self.folder_prices = self.path_to_save_work / Path("prices")
        self.folder_dynamics = self.path_to_save_work / Path("dynamics")
        self.data_provider = ProcessedDataProvider()
        self.logger = setup_logger("Steam_Analysis_App")
        self._prepare_paths()

    def _prepare_paths(self):
        os.makedirs(self.path_to_save_work, exist_ok=True)
        os.makedirs(self.folder_clustering, exist_ok=True)
        os.makedirs(self.folder_prices, exist_ok=True)
        os.makedirs(self.folder_dynamics, exist_ok=True)

    def generate_distribution_by_type(self,  columns_num: int = 15):

        path_for_type_pic = self.folder_clustering / Path("distribution_by_types.png")
        path_for_type_json = self.folder_clustering / Path("dist_by_types.json")
        path_for_type_pic_clustering = self.folder_clustering / Path("dist_by_types.json")
        data_for_response = self.data_provider.get_games_by_types()

        default_saver.save_data(data_for_response, filepath=path_for_type_json)

        if data_for_response:
            from steam_analysis.analysis.utils import generate_clustering_task_picture
            generate_clustering_task_picture.generate_distribution_by_feature(data=data_for_response,
                                                                              title_name=self.TITLES["Clustering"][
                                                                                  "ByType"],
                                                                              path_to_save=path_for_type_pic,
                                                                              columns_num=columns_num)
            # generate_clustering_task_picture.generate_scatter_clusters(data=data_for_response,
            #                                                                   title_name=self.TITLES["Clustering"][
            #                                                                       "ByType"],
            #                                                                   path_to_save=path_for_type_pic_clustering)
        else:
            self.logger.warning("Пустота в данных распределения по типам приложений! Обратитесь к авторам софта)")

    def generate_distribution_for_release_by_season(self, mode):

        path_for_type_pic = self.folder_clustering / Path(f"distribution_by_release_by_season_{mode}.png")
        path_for_type_json = self.folder_clustering / Path(f"dist_release_by_season_{mode}.json")
        data_for_response = self.data_provider.get_games_release_by_season(mode)

        default_saver.save_data(data_for_response, filepath=path_for_type_json)

        if data_for_response:
            from steam_analysis.analysis.utils import generate_clustering_task_picture
            generate_clustering_task_picture.generate_distribution_by_feature(data=data_for_response,
                                                                              title_name=self.TITLES["Clustering"][
                                                                                  "BySeason"],
                                                                              path_to_save=path_for_type_pic,
                                                                              columns_num=12, num_highlited_bins=1)
        else:
            self.logger.warning("Пустота в данных распределения по типам приложений! Обратитесь к авторам софта)")

        pass

    def generate_distribution_by_category(self, columns_num: int = 10):

        path_for_type_pic = self.folder_clustering / Path("distribution_by_categories.png")
        path_for_type_plot = self.folder_clustering / Path("distribution_by_categories_plot.png")
        path_for_type_json = self.folder_clustering / Path("dist_by_categories.json")
        data_for_response = self.data_provider.get_games_by_categories()

        default_saver.save_data(data_for_response, filepath=path_for_type_json)

        if data_for_response:
            from steam_analysis.analysis.utils import generate_clustering_task_picture
            generate_clustering_task_picture.generate_distribution_by_feature(data=data_for_response,
                                                                              title_name=self.TITLES["Clustering"][
                                                                                  "ByCategory"],
                                                                              path_to_save=path_for_type_pic,
                                                                              columns_num=columns_num)
            generate_clustering_task_picture.generate_line_plot(data=data_for_response,
                                                                              title_name=self.TITLES["Clustering"][
                                                                                  "ByCategory"],
                                                                              path_to_save=path_for_type_plot,
                                                                              columns_num=columns_num)
            generate_clustering_task_picture.generate_histogram(data=data_for_response,
                                                                title_name=self.TITLES["Clustering"][
                                                                    "ByCategory"],
                                                                path_to_save=path_for_type_plot,
                                                                bins_num=50, density=True, xlabel_val="Категории")
        else:
            self.logger.warning("Пустота в данных распределения по типам приложений! Обратитесь к авторам софта)")

    def generate_distribution_by_genre(self, columns_num: int = 10):

        path_for_type_pic = self.folder_clustering / Path("distribution_by_genres.png")
        path_for_type_json = self.folder_clustering / Path("dist_by_genres.json")
        data_for_response = self.data_provider.get_games_by_genres()
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

    def generate_distribution_by_count_category(self, columns_num: int = 10):
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

    def generate_distribution_by_price(self, n: int = 10, type: str = "category"):
        """
        Генерирует график распределения ЦЕН по категориям или жанрам
        """
        path_for_json = self.folder_prices / Path(f"price_by_{type}.json")
        path_for_bar = self.folder_prices / Path(f"price_by_{type}_bar.png")
        path_for_hbar = self.folder_prices / Path(f"price_by_{type}_hbar.png")

        print(f"Графики цен по {type} будут сохранены в {self.folder_prices}")

        # Получаем данные
        if type == "category":
            data_for_response = self.data_provider.get_category_by_price(n_columns=n)
            title_name = f"{self.TITLES['Clustering']['PriceByCategory']} (Топ-{n})"
            xlabel_val = "Категория"
        else:
            data_for_response = self.data_provider.get_genre_by_price(n_columns=n)
            title_name = f"{self.TITLES['Clustering']['PriceByGenre']} (Топ-{n})"
            xlabel_val = "Жанр"

        # Проверяем, что получили данные и что это объект CharacterByPrice или словарь
        if not data_for_response:
            self.logger.warning(f"Нет данных о ценах по {type}")
            print(f"Нет данных о ценах по {type}")
            return

        # Преобразуем в объект CharacterByPrice если это словарь
        if isinstance(data_for_response, dict):
            try:
                from steam_analysis.proccessors.schemas.games import CharacterByPrice
                data_for_response = CharacterByPrice(**data_for_response)
            except Exception as e:
                print(f"Ошибка при преобразовании словаря в CharacterByPrice: {e}")
                return

        # Теперь проверяем атрибуты
        if not hasattr(data_for_response, 'values') or not hasattr(data_for_response, 'ticks'):
            self.logger.warning(f"Некорректный формат данных по {type}")
            print(f"Некорректный формат данных по {type}")
            return

        if not data_for_response.values or not data_for_response.ticks:
            self.logger.warning(f"Пустые данные о ценах по {type}")
            print(f"Пустые данные о ценах по {type}")
            return

        print(f"=== ДАННЫЕ О ЦЕНАХ по {type} ===")
        print(f"Количество элементов: {len(data_for_response.ticks)}")
        print(f"Первые 5 категорий: {data_for_response.ticks[:5]}")
        print(f"Первые 5 цен: {data_for_response.values[:5]}")
        print(f"Диапазон цен: min=${min(data_for_response.values):.2f}, max=${max(data_for_response.values):.2f}")
        print("=" * 50)

        try:
            if hasattr(data_for_response, 'model_dump'):
                save_data = data_for_response.model_dump()
            elif hasattr(data_for_response, 'dict'):
                save_data = data_for_response.dict()
            else:
                save_data = {
                    "values": data_for_response.values,
                    "ticks": data_for_response.ticks
                }

            default_saver.save_data(save_data, filepath=path_for_json)
            print(f"Данные успешно сохранены в {path_for_json}")

        except Exception as e:
            print(f"Ошибка при сохранении JSON: {e}")
            try:
                save_data = {
                    "values": data_for_response.values,
                    "ticks": data_for_response.ticks
                }
                default_saver.save_data(save_data, filepath=path_for_json)
            except Exception as e2:
                print(f"Не удалось сохранить даже простой словарь: {e2}")

        try:
            from steam_analysis.analysis.utils.generate_clustering_task_picture import generate_bar_plot

            generate_bar_plot(
                data=data_for_response,
                title_name=title_name,
                path_to_save=path_for_bar,
                xlabel_val=xlabel_val,
                ylabel_val="Средняя цена (Рубли)",
                columns_num=min(20, len(data_for_response.ticks)),
                show_values=True,
                color='steelblue'
            )
            print(f"Вертикальный график сохранен: {path_for_bar}")
        except Exception as e:
            print(f"Ошибка при построении вертикального графика: {e}")

        self.logger.info(f"Графики цен по {type} сохранены")
        print(f"Графики цен по {type} сохранены")


    def generate_distribution_categories_dinamics(self, categories: list[str]):
        pass

    def generate_distribution_genres_dinamics(self, genres: list[str]):
        pass

    def generate_game_clustering(self,
                                 method: str = "kmeans",
                                 n_clusters: int = 5,
                                 limit: int = None, auto_select_params: bool = False):
        clustering_prefix = f"clustering_{method}_{n_clusters}"
        path_clustering_pic = self.folder_clustering / Path(f"{clustering_prefix}_scatter.png")
        path_clustering_json = self.folder_clustering / Path(f"{clustering_prefix}_data.json")

        try:
            data_for_response = self.data_provider.get_game_clustering_data(
                type_id=1,
                limit=limit
            )
        except Exception as e:
            self.logger.error(f"Ошибка получения данных кластеризации: {e}")
            return
        if data_for_response is None:
            self.logger.warning("Получены пустые данные для кластеризации!")
            return
        if not data_for_response.games:
            self.logger.warning(f"Нет игр для кластеризации (получено {len(data_for_response.games)} игр)")
        try:
            default_saver.save_data(data_for_response, filepath=path_clustering_json)
        except Exception as save_error:
            self.logger.error(f"Ошибка сохранения данных кластеризации: {save_error}")

        try:
            from steam_analysis.analysis.utils import clustering
            if len(data_for_response.games) >= n_clusters:
                clustering.perform_games_clustering(
                    data=data_for_response,
                    title_name=f"Детальный анализ кластеризации игр",
                    path_to_save=str(path_clustering_pic),
                    method=method,
                    n_clusters=min(n_clusters, len(data_for_response.games) // 2),
                    features_to_show=[
                    "price_rub",
                    "review_score",
                    "review_confidence",
                    "review_count_log",
                    "achievements_count_norm",
                    "game_age_years",
                    ],
                    auto_select_params = auto_select_params,
                )
            else:
                self.logger.warning(
                    f"Недостаточно данных для детальной кластеризации: {len(data_for_response.games)} игр < {n_clusters} кластеров")
        except Exception as e:
            self.logger.error(f"Ошибка при кластеризации игр: {e}", exc_info=True)

