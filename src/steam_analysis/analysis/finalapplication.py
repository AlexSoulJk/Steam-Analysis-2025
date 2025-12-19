import os
from pathlib import Path

from distribution.pathmanager import pm, DEFAULT_FILENAME_GAMES, DEFAULT_NODE_AGE_NAME, \
    DEFAULT_FILENAME_CLUSTERING, DEFAULT_FILENAME_DISTR_PRICE_GENRE, DEFAULT_FILENAME_DISTR_PRICE_CATEGORY
from geo_mapper import GeoRemapper
from google_loader import GoogleLoader
import numpy as np
from typing import List

from datetime import datetime

from steam_analysis.proccessors.schemas.games import GamesClusteringData, CharacterByPrice
from steam_analysis.app.processed_data_provider import ProcessedDataProvider
from steam_analysis.core.schemas.analysis.friends import FriendsByGames
from steam_analysis.core.schemas.analysis.geoshemas import ListCountryGameStat
from steam_analysis.core.services.fastlogger import setup_logger
from steam_analysis.json_to_csv_converter import JsonToCsvConverter
from steam_analysis.loader_test_data import LoaderTestData
from steam_analysis.saver_test_data import default_saver, SaveTestData
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
        self.convert_to_csv = JsonToCsvConverter()
        self.data_provider = ProcessedDataProvider()
        self.google_uploader = GoogleLoader()
        self.geo_remapper = GeoRemapper()
        self.logger = setup_logger("Steam_Analysis_App")
        self._prepare_paths()

    def _prepare_paths(self):
        os.makedirs(self.path_to_save_work, exist_ok=True)
        os.makedirs(self.folder_clustering, exist_ok=True)
        os.makedirs(self.folder_prices, exist_ok=True)
        os.makedirs(self.folder_dynamics, exist_ok=True)

    def generate_distribution_by_type(self, columns_num=15):

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
                                                                                  "ByType"],
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

    def calculate_geo_games(self, geo_game_saver: SaveTestData, limit_of_games=3):
        res = self.data_provider.get_geo_games(limit_of_games)
        geo_game_saver.save_task_data_simple(res, Path(DEFAULT_FILENAME_GAMES))
        return res

    def calculate_geo_categories(self, limit_of_games=3):
        res = self.data_provider.get_geo_games(limit_of_games)
        return res

    def calculate_friends_graphs_by_games(self, friends_game_saver: SaveTestData, steam_id: str = "76561198287722531"):
        res = self.data_provider.get_friends_by_games(steam_id)
        friends_game_saver.save_task_data_simple(res, Path(DEFAULT_FILENAME_GAMES))
        return res

    def load_geo_games(self, geo_game_loader: LoaderTestData, spreadsheet_url=str):
        loaded_data = geo_game_loader.load_from_files_by_schema(pm.file_to_task_geo_games, ListCountryGameStat)
        loaded_data_remaped = self.geo_remapper.convert_for_datawrapper(loaded_data)
        tmp = self.convert_to_csv.convert_geo_games(loaded_data_remaped)

        self.google_uploader.upload_csv_by_url_from_str(spreadsheet_url, tmp)

    def load_friends_graphs_by_games(self, friends_loader: LoaderTestData, spreadsheet_url=str):
        loaded_data = friends_loader.load_from_files_by_schema(pm.file_to_task_friends_games, FriendsByGames)
        df_nodes, df_orts = self.convert_to_csv.convert_for_cosmograph(loaded_data)
        nodes_id = self.google_uploader.upload_csv_by_title_from_df(DEFAULT_NODE_AGE_NAME, [df_nodes, df_orts],
                                                                    folder_id=spreadsheet_url)
        nodes_csv_link = f"https://docs.google.com/spreadsheets/d/{nodes_id}"

        print(f"Проверьте документ по ссылке: {nodes_csv_link}")

    def generate_distribution_by_price(self, n: int = 10, type: str = "category"):
        path_for_json = self.folder_prices / Path(f"price_by_{type}.json")
        path_for_bar = self.folder_prices / Path(f"price_by_{type}_bar.png")
        print(f"Графики цен по {type} будут сохранены в {self.folder_prices}")
        if type == "category":
            data_for_response = self.data_provider.get_category_by_price(n_columns=n)
            title_name = f"{self.TITLES['Clustering']['PriceByCategory']} (Топ-{n})"
            xlabel_val = "Категория"
        else:
            data_for_response = self.data_provider.get_genre_by_price(n_columns=n)
            title_name = f"{self.TITLES['Clustering']['PriceByGenre']} (Топ-{n})"
            xlabel_val = "Жанр"
        if not data_for_response:
            self.logger.warning(f"Нет данных о ценах по {type}")
            print(f"Нет данных о ценах по {type}")
            return
        if isinstance(data_for_response, dict):
            try:
                from steam_analysis.proccessors.schemas.games import CharacterByPrice
                data_for_response = CharacterByPrice(**data_for_response)
            except Exception as e:
                print(f"Ошибка при преобразовании словаря в CharacterByPrice: {e}")
                return
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
                save_data = data_for_response
            elif hasattr(data_for_response, 'dict'):
                save_data = data_for_response
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

    def generate_distribution_dynamics(self, n: int = 5, type: str = "category", years_back: int = 5):
        """
        Генерирует график динамики релизов по категориям или жанрам
        Использует generate_multi_line_plot для отображения нескольких временных рядов
        """
        path_for_json = self.folder_prices / Path(f"dynamics_by_{type}.json")
        path_for_plot = self.folder_prices / Path(f"dynamics_by_{type}_plot.png")

        print(f"Графики динамики по {type} будут сохранены в {self.folder_prices}")

        if type == "category":
            data_for_response = self.data_provider.get_categories_dynamics(n_columns=n, years_back=years_back)
            title_name = f"{self.TITLES['Clustering']['CategoryDynamics']} (Топ-{n})"
            xlabel_val = "Год"
        else:
            data_for_response = self.data_provider.get_genres_dynamics(n_columns=n, years_back=years_back)
            title_name = f"{self.TITLES['Clustering']['GenreDynamics']} (Топ-{n})"
            xlabel_val = "Год"

        if not data_for_response:
            self.logger.warning(f"Нет данных о динамике по {type}")
            print(f"Нет данных о динамике по {type}")
            return

        if isinstance(data_for_response, dict):
            try:
                from steam_analysis.proccessors.schemas.games import CharacterByTime
                values = data_for_response.get('values', [])
                ticks = data_for_response.get('ticks', [])
                data_for_response = CharacterByTime(values=values, ticks=ticks)
            except Exception as e:
                print(f"Ошибка создания CharacterByTime: {e}")
                return

        if not hasattr(data_for_response, 'values') or not hasattr(data_for_response, 'ticks'):
            print(f"Некорректный формат данных: {type(data_for_response)}")
            return

        if not data_for_response.values or not data_for_response.ticks:
            print(f"Пустые данные о динамике по {type}")
            return

        print(f"=== ДАННЫЕ О ДИНАМИКЕ по {type} ===")
        print(f"Количество рядов (категорий/жанров): {len(data_for_response.ticks)}")
        print(f"Длина временного ряда: {len(data_for_response.values[0]) if data_for_response.values else 0}")
        print(f"Пример: {data_for_response.ticks[:3]}")
        print("=" * 50)

        try:
            save_data = {
                "values": data_for_response.values,
                "ticks": data_for_response.ticks,
                "type": type,
                "n": n,
                "timestamp": datetime.now().isoformat()
            }
            default_saver.save_data(save_data, filepath=path_for_json)
            print(f"Данные сохранены в JSON: {path_for_json}")
        except Exception as e:
            print(f"Ошибка при сохранении JSON: {e}")

        data_list = []
        labels = []

        current_year = datetime.now().year
        years_count = len(data_for_response.values[0]) if data_for_response.values else 5
        time_labels = [str(current_year - i) for i in range(years_count - 1, -1, -1)]

        for i, (category_genre, values) in enumerate(zip(data_for_response.ticks, data_for_response.values)):
            if i < n:
                from steam_analysis.analysis.response_schemas.graphics import AbstractGameBy_
                if len(values) == len(time_labels):
                    time_series_data = AbstractGameBy_(
                        values=values,
                        ticks=time_labels
                    )
                    data_list.append(time_series_data)
                    labels.append(category_genre)
                else:
                    print(f"Предупреждение: Несоответствие длины для {category_genre} "
                          f"({len(values)} != {len(time_labels)})")
        if not data_list:
            print("Нет данных для построения графика")
            return
        try:
            from steam_analysis.analysis.utils.generate_clustering_task_picture import generate_multi_line_plot

            generate_multi_line_plot(
                data_list=data_list,
                labels=labels,
                title_name=title_name,
                path_to_save=path_for_plot,
                xlabel_val=xlabel_val,
                ylabel_val="Количество релизов"
            )
            print(f"График динамики сохранен: {path_for_plot}")

        except Exception as e:
            print(f"Ошибка при построении графика: {e}")

        self.logger.info(f"Графики динамики по {type} сохранены")
        print(f"Графики динамики по {type} сохранены")

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
                    features_to_show= [
                        "price_rub",            # Финансы
                        "positive_ratio",       # Качество
                        "game_age_years"        # Время ⭐
                    ],
                    auto_select_params=auto_select_params,
                    make_3d_viz=True,  # Вместо create_3d_visualization
                    make_interactive_3d=False
                )
            else:
                self.logger.warning(
                    f"Недостаточно данных для детальной кластеризации: {len(data_for_response.games)} игр < {n_clusters} кластеров")
        except Exception as e:
            self.logger.error(f"Ошибка при кластеризации игр: {e}", exc_info=True)

    def calculate_game_clustering(self,
                                  clustering_saver: SaveTestData = default_saver,
                                  limit: int = None):
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
            clustering_saver.save_task_data_simple(data_for_response,
                                                   file_name=DEFAULT_FILENAME_CLUSTERING)

        except Exception as save_error:
            self.logger.error(f"Ошибка сохранения данных кластеризации: {save_error}")

    def load_clustering(self,
                        clustering_loader: LoaderTestData,
                        n_clusters=6,
                        method="kmeans",
                        auto_select_params=False):

        path = pm.file_clustering_games
        loaded_data = clustering_loader.load_from_files_by_schema(path, GamesClusteringData)
        if not loaded_data:
            print(f"❌ Ошибка чтения файла: '{path}'")
            return
        try:
            from steam_analysis.analysis.utils import clustering
            path_clustering_pic = path.parent / f"{path.stem}_scatter.png"
            if len(loaded_data.games) >= n_clusters:
                clustering.perform_games_clustering(
                    data=loaded_data,
                    title_name=f"Детальный анализ кластеризации игр",
                    path_to_save=str(path_clustering_pic),
                    method=method,
                    n_clusters=min(n_clusters, len(loaded_data.games) // 2),
                    features_to_show=[
                        "price_rub",
                        "review_score",
                        "review_confidence",
                        "review_count_log",
                        "achievements_count_norm",
                        "game_age_years",
                    ],
                    auto_select_params=auto_select_params,
                )

                from PIL import Image
                image = Image.open(path_clustering_pic)
                image.show()
            else:
                self.logger.warning(
                    f"Недостаточно данных для детальной кластеризации: "
                    f"{len(loaded_data.games)} игр < {n_clusters} кластеров")

        except Exception as e:
            self.logger.error(f"Ошибка при кластеризации игр: {e}", exc_info=True)

    def calculate_distribution_by_price_genre(self,
                                              distr_by_price_saver: SaveTestData = default_saver,
                                              n: int = 10,
                                              limit: int = None):

        data_for_response = self.data_provider.get_genre_by_price(n_columns=n)
        # Проверяем, что получили данные и что это объект CharacterByPrice или словарь
        if not data_for_response:
            self.logger.warning(f"Нет данных о ценах по жанрам")
            print(f"Нет данных о ценах по жанрам")
            return

        self.save_distribution_by_price(distr_by_price_saver, data_for_response,
                                        DEFAULT_FILENAME_DISTR_PRICE_GENRE, "жанрам")

    def calculate_distribution_by_price_category(self,
                                                 distr_by_price_saver: SaveTestData = default_saver,
                                                 n: int = 10,
                                                 limit: int = None):
        data_for_response = self.data_provider.get_category_by_price(n_columns=n)

        if not data_for_response:
            self.logger.warning(f"Нет данных о ценах по категориям")
            print(f"Нет данных о ценах по категориям")
            return

        self.save_distribution_by_price(distr_by_price_saver, data_for_response,
                                        DEFAULT_FILENAME_DISTR_PRICE_CATEGORY, "категориям")

    def save_distribution_by_price(self, distr_by_price_saver, data_for_response, filename, type_):
        # Преобразуем в объект CharacterByPrice если это словарь
        if isinstance(data_for_response, dict):
            try:
                data_for_response = CharacterByPrice(**data_for_response)
            except Exception as e:
                print(f"Ошибка при преобразовании словаря в CharacterByPrice: {e}")
                return

        # Теперь проверяем атрибуты
        if not hasattr(data_for_response, 'values') or not hasattr(data_for_response, 'ticks'):
            self.logger.warning(f"Некорректный формат данных по {type_}")
            print(f"Некорректный формат данных по {type_}")
            return

        if not data_for_response.values or not data_for_response.ticks:
            self.logger.warning(f"Пустые данные о ценах по {type_}")
            print(f"Пустые данные о ценах по {type_}")
            return

        print(f"=== ДАННЫЕ О ЦЕНАХ по {type_} ===")
        print(f"Количество элементов: {len(data_for_response.ticks)}")
        print(f"Первые 5 категорий: {data_for_response.ticks[:5]}")
        print(f"Первые 5 цен: {data_for_response.values[:5]}")
        print(f"Диапазон цен: min=${min(data_for_response.values):.2f}, max=${max(data_for_response.values):.2f}")
        print("=" * 50)

        try:
            distr_by_price_saver.save_task_data_simple(data_for_response, filename)
        except Exception as e:
            print(f"Ошибка при сохранении JSON: {e}")

    def load_distribution_by_price_genre(self,
                                         loader: LoaderTestData,
                                         n: int = 25):
        path = pm.file_price_by_genre
        loaded_data = loader.load_from_files_by_schema(path, CharacterByPrice)
        if not loaded_data:
            print(f"❌ Ошибка чтения файла: '{path}'")
            return

        path_for_bar = path.parent / f"{path.stem}_bar.png"

        title_name = f"{self.TITLES['Clustering']['PriceByGenre']} (Топ-{n})"
        xlabel_val = "Жанр"
        self.load_distribution_by_price(loaded_data,
                                        title_name, xlabel_val,
                                        len(loaded_data.ticks), path_for_bar)
        from PIL import Image
        image = Image.open(path_for_bar)
        image.show()

    def load_distribution_by_price_category(self,
                                         loader: LoaderTestData,
                                         n: int = 25):
        path = pm.file_price_by_category
        loaded_data = loader.load_from_files_by_schema(path, CharacterByPrice)
        if not loaded_data:
            print(f"❌ Ошибка чтения файла: '{path}'")
            return

        path_for_bar = path.parent / f"{path.stem}_bar.png"

        title_name = f"{self.TITLES['Clustering']['PriceByCategory']} (Топ-{n})"
        xlabel_val = "Категория"
        self.load_distribution_by_price(loaded_data,
                                        title_name, xlabel_val,
                                        len(loaded_data.ticks), path_for_bar)

        from PIL import Image
        image = Image.open(path_for_bar)
        image.show()

    def load_distribution_by_price(self,
                                   loaded_data,
                                   title_name,
                                   xlabel_val,
                                   columns_num,
                                   path_for_bar):

        try:
            from steam_analysis.analysis.utils.generate_clustering_task_picture import generate_bar_plot

            generate_bar_plot(
                data=loaded_data,
                title_name=title_name,
                path_to_save=path_for_bar,
                xlabel_val=xlabel_val,
                ylabel_val="Средняя цена (Рубли)",
                # columns_num=min(20, len(data_for_response.ticks)),
                columns_num=min(20, columns_num),
                show_values=True,
                color='steelblue'
            )
            print(f"Вертикальный график сохранен: {path_for_bar}")

        except Exception as e:
            print(f"Ошибка при построении вертикального графика: {e}")

        self.logger.info(f"Графики цен по {title_name} сохранены")
        print(f"Графики цен по {title_name} сохранены")
