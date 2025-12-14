import os
from pathlib import Path
import numpy as np

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
            "BySeason": "Количество выпущенных по сезонам игр за всё время"
        },
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


    # def generate_clustering_diagrams(self):
    #     path_for_type_pic = self.folder_clustering / Path("distribution_by_count_categories.png")
    #     path_for_type_json = self.folder_clustering / Path("dist_by_count_categories.json")
    #     data_for_response = self.data_provider.get_games_by_categories_count()
    #
    #     default_saver.save_data(data_for_response, filepath=path_for_type_json)
    #
    #     if data_for_response:
    #         from steam_analysis.analysis.utils import generate_clustering_task_picture
    #         generate_clustering_task_picture.generate_grouped_histogram(data=data_for_response,
    #                                                                           title_name=self.TITLES["Clustering"][
    #                                                                               "By"],
    #                                                                           path_to_save=path_for_type_pic,
    #                                                                           )
    #     else:
    #         self.logger.warning("Пустота в данных распределения по типам приложений! Обратитесь к авторам софта)")
    #
    #
    # def generate_enhanced_hist(self, bins: int = 10):
    #     path_for_type_pic = self.folder_clustering / Path("distribution_by_count_categories.png")
    #     path_for_type_json = self.folder_clustering / Path("dist_by_count_categories.json")
    #     data_for_response = self.data_provider.get_games_by_categories_count()
    #
    #     default_saver.save_data(data_for_response, filepath=path_for_type_json)
    #
    #     if data_for_response:
    #         from steam_analysis.analysis.utils import generate_clustering_task_picture
    #         generate_clustering_task_picture.generate_enhanced_histogram(data=data_for_response,
    #                                                                           title_name=self.TITLES["Clustering"][
    #                                                                               "By"],
    #                                                                           path_to_save=path_for_type_pic,
    #                                                                           )
    #     else:
    #         self.logger.warning("Пустота в данных распределения по типам приложений! Обратитесь к авторам софта)")
    #
    #
    # def generate_grouped_hist(self, bins: int = 10):
    #     path_for_type_pic = self.folder_clustering / Path("distribution_by_count_categories.png")
    #     path_for_type_json = self.folder_clustering / Path("dist_by_count_categories.json")
    #     data_for_response = self.data_provider.get_games_by_categories_count()
    #
    #     default_saver.save_data(data_for_response, filepath=path_for_type_json)
    #
    #     if data_for_response:
    #         from steam_analysis.analysis.utils import generate_clustering_task_picture
    #         generate_clustering_task_picture.generate_grouped_histogram(data=data_for_response,
    #                                                                           title_name=self.TITLES["Clustering"][
    #                                                                               "By"],
    #                                                                           path_to_save=path_for_type_pic,
    #                                                                           )
    #     else:
    #         self.logger.warning("Пустота в данных распределения по типам приложений! Обратитесь к авторам софта)")

    def generate_game_clustering(self,
                                 method: str = "kmeans",
                                 n_clusters: int = 5,
                                 limit: int = None):
        clustering_prefix = f"clustering_{method}_{n_clusters}"
        path_clustering_pic = self.folder_clustering / Path(f"{clustering_prefix}_scatter.png")
        path_clustering_json = self.folder_clustering / Path(f"{clustering_prefix}_data.json")
        path_heatmap_pic = self.folder_clustering / Path(f"{clustering_prefix}_heatmap.png")

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
            from steam_analysis.analysis.utils import generate_clustering_task_picture

            if len(data_for_response.games) >= n_clusters:
                generate_clustering_task_picture.perform_games_clustering(
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
                    ]
                )
            else:
                self.logger.warning(
                    f"Недостаточно данных для детальной кластеризации: {len(data_for_response.games)} игр < {n_clusters} кластеров")

            if data_for_response.feature_matrix and len(data_for_response.feature_matrix) > 1:
                try:
                    correlation_matrix = np.corrcoef(data_for_response.feature_matrix)

                    heatmap_data = CorrelationHeatmapData(
                        correlation_matrix=correlation_matrix.tolist(),
                        feature_names=data_for_response.feature_names,
                        values={"features_count": len(data_for_response.feature_names)},
                        ticks=data_for_response.feature_names[:min(15, len(data_for_response.feature_names))]
                    )

                    generate_clustering_task_picture.generate_correlation_heatmap(
                        data=heatmap_data,
                        title_name="Корреляция признаков игр",
                        path_to_save=str(path_heatmap_pic),
                        annotate=True,
                        figsize=(14, 12)
                    )

                    self.logger.info(f"✅ Heatmap корреляций сохранена: {path_heatmap_pic}")

                except Exception as heatmap_error:
                    self.logger.warning(f"Не удалось создать heatmap корреляций: {heatmap_error}")

            self.logger.info(f"✅ Кластеризация игр завершена! Файлы сохранены в: {self.folder_clustering}")

        except Exception as e:
            self.logger.error(f"Ошибка при кластеризации игр: {e}", exc_info=True)
    #
    # def generate_2d_histogram_analysis(self,
    #                                    x_field: str = "review_score",
    #                                    y_field: str = "price",
    #                                    x_bins: int = 20,
    #                                    y_bins: int = 20,
    #                                    min_review_count: int = 10) -> None:
    #     """
    #     Генерирует 2D гистограммы и анализ распределений
    #
    #     Args:
    #         x_field: Поле для оси X
    #         y_field: Поле для оси Y
    #         x_bins: Количество бинов по X
    #         y_bins: Количество бинов по Y
    #         min_review_count: Минимальное количество отзывов
    #     """
    #     # Определяем пути для сохранения
    #     prefix = f"2d_hist_{x_field}_vs_{y_field}"
    #     path_main_pic = self.folder_clustering / Path(f"{prefix}_main.png")
    #     path_dist_pic = self.folder_clustering / Path(f"{prefix}_distribution.png")
    #     path_data_json = self.folder_clustering / Path(f"{prefix}_data.json")
    #     path_correlation_pic = self.folder_clustering / Path(f"{prefix}_correlation.png")
    #
    #     # Получаем данные для 2D гистограммы
    #     data_for_response = self.data_provider.get_2d_hist_data(
    #         x_field=x_field,
    #         y_field=y_field,
    #         x_bins=x_bins,
    #         y_bins=y_bins,
    #         min_review_count=min_review_count
    #     )
    #
    #     # Сохраняем сырые данные
    #     default_saver.save_data(data_for_response, filepath=path_data_json)
    #
    #     if not data_for_response or len(data_for_response.x_values) == 0:
    #         self.logger.warning(f"Нет данных для 2D гистограммы {x_field} vs {y_field}")
    #         return
    #
    #     try:
    #         from steam_analysis.analysis.utils import generate_clustering_task_picture
    #
    #         # 1. Основная 2D density heatmap
    #         generate_clustering_task_picture.generate_2d_density_heatmap(
    #             data=data_for_response,
    #             title_name=f"2D Распределение: {x_field} vs {y_field}",
    #             path_to_save=str(path_main_pic),
    #             cmap="viridis",
    #             log_scale=True,
    #             figsize=(14, 12)
    #         )
    #
    #         # 2. Анализ отдельных распределений
    #         # Получаем данные для отдельных гистограмм
    #         for field_name, values, field_label in [
    #             (x_field, data_for_response.x_values, data_for_response.x_label),
    #             (y_field, data_for_response.y_values, data_for_response.y_label)
    #         ]:
    #             # Создаем данные для улучшенной гистограммы
    #             hist_data = EnhancedHistogramData(
    #                 values=values,
    #                 value_name=field_label,
    #                 unit="" if field_name != "price" else "$",
    #                 bins_method="auto",
    #                 show_density=True,
    #                 show_stats=True,
    #                 show_outliers=True,
    #                 compare_with_normal=True,
    #                 log_scale=False,
    #                 ticks=[]
    #             )
    #
    #             hist_path = self.folder_clustering / Path(f"hist_{field_name}.png")
    #
    #             analysis_result = generate_clustering_task_picture.generate_enhanced_histogram(
    #                 data=hist_data,
    #                 title_name=f"Распределение: {field_label}",
    #                 path_to_save=str(hist_path),
    #                 figsize=(14, 10)
    #             )
    #
    #             # Сохраняем результат анализа
    #             analysis_json = self.folder_clustering / Path(f"hist_{field_name}_analysis.json")
    #             default_saver.save_data(analysis_result, filepath=analysis_json)
    #
    #             self.logger.info(f"✅ Гистограмма {field_label} сохранена: {hist_path}")
    #
    #         # 3. Анализ корреляции
    #         correlation = np.corrcoef(data_for_response.x_values, data_for_response.y_values)[0, 1]
    #
    #         # Создаем scatter plot с линией регрессии
    #         fig, ax = plt.subplots(figsize=(10, 8))
    #
    #         # Scatter plot
    #         scatter = ax.scatter(data_for_response.x_values, data_for_response.y_values,
    #                              alpha=0.6, s=20, c='blue', edgecolors='black', linewidth=0.5)
    #
    #         # Линия регрессии
    #         if len(data_for_response.x_values) > 1:
    #             coeffs = np.polyfit(data_for_response.x_values, data_for_response.y_values, 1)
    #             poly = np.poly1d(coeffs)
    #             x_line = np.linspace(min(data_for_response.x_values), max(data_for_response.x_values), 100)
    #             y_line = poly(x_line)
    #             ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'Линейная регрессия (R²={correlation ** 2:.3f})')
    #
    #         # Гистограммы на полях
    #         divider = make_axes_locatable(ax)
    #         ax_histx = divider.append_axes("top", 0.25, pad=0.1, sharex=ax)
    #         ax_histy = divider.append_axes("right", 0.25, pad=0.1, sharey=ax)
    #
    #         ax_histx.hist(data_for_response.x_values, bins=x_bins, color='skyblue', edgecolor='black')
    #         ax_histy.hist(data_for_response.y_values, bins=y_bins, color='lightgreen',
    #                       edgecolor='black', orientation='horizontal')
    #
    #         ax_histx.set_title(f"Распределение по {data_for_response.x_label}", fontsize=10)
    #         ax_histy.set_title(f"Распределение по {data_for_response.y_label}", fontsize=10)
    #
    #         ax_histx.grid(True, alpha=0.3)
    #         ax_histy.grid(True, alpha=0.3)
    #
    #         ax.set_xlabel(data_for_response.x_label, fontsize=12)
    #         ax.set_ylabel(data_for_response.y_label, fontsize=12)
    #         ax.set_title(f"Scatter plot с корреляцией: {x_field} vs {y_field}\n"
    #                      f"Корреляция: {correlation:.3f} (n={len(data_for_response.x_values)})",
    #                      fontsize=14, fontweight='bold')
    #
    #         ax.legend()
    #         ax.grid(True, alpha=0.3, linestyle='--')
    #
    #         plt.tight_layout()
    #         plt.savefig(str(path_correlation_pic), dpi=300, bbox_inches='tight')
    #         plt.close(fig)
    #
    #         # 4. Создаем сводный отчет
    #         self._create_2d_analysis_report(
    #             x_field=x_field,
    #             y_field=y_field,
    #             data=data_for_response,
    #             correlation=correlation
    #         )
    #
    #         self.logger.info(f"✅ 2D анализ завершен! Файлы сохранены в: {self.folder_clustering}")
    #
    #     except Exception as e:
    #         self.logger.error(f"Ошибка при генерации 2D гистограммы: {e}", exc_info=True)
    #
    # def generate_enhanced_histogram_analysis(self,
    #                                          value_field: str = "review_score",
    #                                          bins_method: str = "auto",
    #                                          min_review_count: int = 10,
    #                                          filter_free: Optional[bool] = None) -> None:
    #     """
    #     Генерирует расширенный анализ гистограмм с детальной статистикой
    #
    #     Args:
    #         value_field: Анализируемое поле
    #         bins_method: Метод расчета бинов
    #         min_review_count: Минимальное количество отзывов
    #         filter_free: Фильтр по бесплатным играм
    #     """
    #     # Определяем пути для сохранения
    #     prefix = f"enhanced_hist_{value_field}"
    #     if filter_free is not None:
    #         prefix += f"_{'free' if filter_free else 'paid'}"
    #
    #     path_main_pic = self.folder_clustering / Path(f"{prefix}_main.png")
    #     path_comparison_pic = self.folder_clustering / Path(f"{prefix}_comparison.png")
    #     path_data_json = self.folder_clustering / Path(f"{prefix}_data.json")
    #     path_analysis_json = self.folder_clustering / Path(f"{prefix}_analysis.json")
    #
    #     # Получаем данные для расширенной гистограммы
    #     data_for_response = self.data_provider.enhanced_histogram_data(
    #         value_field=value_field,
    #         bins_method=bins_method,
    #         min_review_count=min_review_count,
    #         filter_free=filter_free
    #     )
    #
    #     # Сохраняем сырые данные
    #     default_saver.save_data(data_for_response, filepath=path_data_json)
    #
    #     if not data_for_response or len(data_for_response.values) == 0:
    #         self.logger.warning(f"Нет данных для анализа поля {value_field}")
    #         return
    #
    #     try:
    #         from steam_analysis.analysis.utils import generate_clustering_task_picture
    #
    #         # 1. Основная улучшенная гистограмма с анализом
    #         analysis_result = generate_clustering_task_picture.generate_enhanced_histogram(
    #             data=data_for_response,
    #             title_name=f"Анализ распределения: {data_for_response.value_name}",
    #             path_to_save=str(path_main_pic),
    #             figsize=(16, 12)
    #         )
    #
    #         # Сохраняем результат анализа
    #         default_saver.save_data(analysis_result, filepath=path_analysis_json)
    #
    #         # 2. Сравнительный анализ (если есть данные для сравнения)
    #         try:
    #             # Получаем данные для сравнения (бесплатные vs платные)
    #             if filter_free is None:
    #                 # Сравниваем бесплатные и платные игры
    #                 data_free = self.data_provider.enhanced_histogram_data(
    #                     value_field=value_field,
    #                     min_review_count=min_review_count,
    #                     filter_free=True
    #                 )
    #
    #                 data_paid = self.data_provider.enhanced_histogram_data(
    #                     value_field=value_field,
    #                     min_review_count=min_review_count,
    #                     filter_free=False
    #                 )
    #
    #                 if data_free and data_paid and len(data_free.values) > 0 and len(data_paid.values) > 0:
    #                     # Создаем данные для групповой гистограммы
    #                     grouped_data = GroupedHistogramData(
    #                         groups={
    #                             'Бесплатные игры': data_free.values,
    #                             'Платные игры': data_paid.values
    #                         },
    #                         group_names=['Бесплатные игры', 'Платные игры'],
    #                         value_name=data_for_response.value_name,
    #                         normalize=True,
    #                         show_violin=True,
    #                         values={},
    #                         ticks=[]
    #                     )
    #
    #                     generate_clustering_task_picture.generate_grouped_histogram(
    #                         data=grouped_data,
    #                         title_name=f"Сравнение: {data_for_response.value_name}",
    #                         path_to_save=str(path_comparison_pic),
    #                         figsize=(14, 10)
    #                     )
    #
    #                     self.logger.info(f"✅ Сравнительный анализ сохранен: {path_comparison_pic}")
    #
    #         except Exception as comparison_error:
    #             self.logger.debug(f"Не удалось создать сравнительный анализ: {comparison_error}")
    #
    #         # 3. Дополнительные визуализации
    #         # Создаем временной ряд (если это поле с датой)
    #         if "year" in value_field.lower() or "date" in value_field.lower():
    #             try:
    #                 time_path = self.folder_clustering / Path(f"{prefix}_time_series.png")
    #
    #                 # Преобразуем данные для временного ряда
    #                 time_data = AbstractGameBy_(
    #                     values=data_for_response.values,
    #                     ticks=list(range(len(data_for_response.values)))
    #                 )
    #
    #                 generate_clustering_task_picture.generate_time_series_heatmap(
    #                     data=time_data,
    #                     title_name=f"Временной ряд: {data_for_response.value_name}",
    #                     path_to_save=str(time_path),
    #                     time_period="year-month",
    #                     value_type="count",
    #                     cmap="YlOrRd",
    #                     figsize=(12, 8)
    #                 )
    #
    #                 self.logger.info(f"✅ Временной ряд сохранен: {time_path}")
    #
    #             except Exception as time_error:
    #                 self.logger.debug(f"Не удалось создать временной ряд: {time_error}")
    #
    #         # 4. Создаем сводный отчет
    #         self._create_histogram_report(
    #             field_name=value_field,
    #             data=data_for_response,
    #             analysis=analysis_result
    #         )
    #
    #         self.logger.info(f"✅ Расширенный анализ гистограммы завершен! Файлы сохранены в: {self.folder_clustering}")
    #
    #     except Exception as e:
    #         self.logger.error(f"Ошибка при генерации расширенной гистограммы: {e}", exc_info=True)
    #
    # def _create_2d_analysis_report(self,
    #                                x_field: str,
    #                                y_field: str,
    #                                data: TwoDHistogramData,
    #                                correlation: float) -> None:
    #     """
    #     Создает текстовый отчет по 2D анализу
    #     """
    #     report_path = self.folder_clustering / Path(f"report_2d_{x_field}_{y_field}.txt")
    #
    #     with open(report_path, 'w', encoding='utf-8') as f:
    #         f.write(f"ОТЧЕТ ПО 2D АНАЛИЗУ\n")
    #         f.write(f"==================\n\n")
    #
    #         f.write(f"Анализируемые поля:\n")
    #         f.write(f"  X: {data.x_label}\n")
    #         f.write(f"  Y: {data.y_label}\n\n")
    #
    #         f.write(f"Общая статистика:\n")
    #         f.write(f"  Количество точек: {len(data.x_values):,}\n")
    #         f.write(f"  Корреляция (r): {correlation:.3f}\n")
    #         f.write(f"  Коэффициент детерминации (R²): {correlation ** 2:.3f}\n\n")
    #
    #         if correlation > 0.7:
    #             f.write(f"❗ СИЛЬНАЯ ПОЛОЖИТЕЛЬНАЯ КОРРЕЛЯЦИЯ\n")
    #             f.write(f"   Значения {x_field} и {y_field} сильно связаны\n\n")
    #         elif correlation < -0.7:
    #             f.write(f"❗ СИЛЬНАЯ ОТРИЦАТЕЛЬНАЯ КОРРЕЛЯЦИЯ\n")
    #             f.write(f"   Значения {x_field} и {y_field} сильно связаны обратной зависимостью\n\n")
    #         elif abs(correlation) < 0.3:
    #             f.write(f"📊 СЛАБАЯ КОРРЕЛЯЦИЯ\n")
    #             f.write(f"   Значения {x_field} и {y_field} слабо связаны\n\n")
    #
    #         # Статистика по X
    #         if data.x_values:
    #             f.write(f"Статистика по {data.x_label}:\n")
    #             f.write(f"  Среднее: {np.mean(data.x_values):.2f}\n")
    #             f.write(f"  Медиана: {np.median(data.x_values):.2f}\n")
    #             f.write(f"  Минимум: {np.min(data.x_values):.2f}\n")
    #             f.write(f"  Максимум: {np.max(data.x_values):.2f}\n")
    #             f.write(f"  Стандартное отклонение: {np.std(data.x_values):.2f}\n\n")
    #
    #         # Статистика по Y
    #         if data.y_values:
    #             f.write(f"Статистика по {data.y_label}:\n")
    #             f.write(f"  Среднее: {np.mean(data.y_values):.2f}\n")
    #             f.write(f"  Медиана: {np.median(data.y_values):.2f}\n")
    #             f.write(f"  Минимум: {np.min(data.y_values):.2f}\n")
    #             f.write(f"  Максимум: {np.max(data.y_values):.2f}\n")
    #             f.write(f"  Стандартное отклонение: {np.std(data.y_values):.2f}\n\n")
    #
    #         f.write(f"Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    #
    #     self.logger.info(f"📄 Текстовый отчет сохранен: {report_path}")
    #
    # def _create_histogram_report(self,
    #                              field_name: str,
    #                              data: EnhancedHistogramData,
    #                              analysis: Any) -> None:
    #     """
    #     Создает текстовый отчет по анализу гистограммы
    #     """
    #     report_path = self.folder_clustering / Path(f"report_hist_{field_name}.txt")
    #
    #     with open(report_path, 'w', encoding='utf-8') as f:
    #         f.write(f"ОТЧЕТ ПО АНАЛИЗУ РАСПРЕДЕЛЕНИЯ\n")
    #         f.write(f"===============================\n\n")
    #
    #         f.write(f"Анализируемое поле: {data.value_name}\n")
    #         f.write(f"Количество значений: {len(data.values):,}\n\n")
    #
    #         f.write(f"ОСНОВНЫЕ ХАРАКТЕРИСТИКИ РАСПРЕДЕЛЕНИЯ:\n")
    #         f.write(f"  Тип распределения: {analysis.distribution_type.upper()}\n")
    #         f.write(f"  Нормальность: {'ДА' if analysis.is_normal else 'НЕТ'} (p={analysis.normality_p_value:.3f})\n")
    #         f.write(f"  Модальность: {analysis.modality} пик(а)\n\n")
    #
    #         f.write(f"МЕРЫ ЦЕНТРА:\n")
    #         f.write(f"  Среднее: {analysis.mean:.2f}\n")
    #         f.write(f"  Медиана: {analysis.median:.2f}\n")
    #         f.write(f"  Мода: {stats.mode(data.values, keepdims=True)[0][0]:.2f}\n\n")
    #
    #         f.write(f"МЕРЫ РАЗБРОСА:\n")
    #         f.write(f"  Стандартное отклонение: {analysis.std:.2f}\n")
    #         f.write(f"  Дисперсия: {analysis.std ** 2:.2f}\n")
    #         f.write(f"  IQR: {analysis.iqr:.2f}\n")
    #         f.write(f"  Размах: {max(data.values) - min(data.values):.2f}\n\n")
    #
    #         f.write(f"ФОРМА РАСПРЕДЕЛЕНИЯ:\n")
    #         f.write(f"  Асимметрия: {analysis.skewness:.3f}\n")
    #         f.write(f"  Эксцесс: {analysis.kurtosis:.3f}\n\n")
    #
    #         f.write(f"ПРОЦЕНТИЛИ:\n")
    #         for perc_name, perc_value in analysis.percentiles.items():
    #             f.write(f"  {perc_name}: {perc_value:.2f}\n")
    #
    #         f.write(f"\n")
    #
    #         f.write(f"ВЫБРОСЫ:\n")
    #         f.write(f"  Количество выбросов: {analysis.outliers_count}\n")
    #         f.write(f"  Процент выбросов: {analysis.outliers_count / len(data.values) * 100:.1f}%\n\n")
    #
    #         f.write(f"ИНТЕРПРЕТАЦИЯ:\n")
    #         if analysis.skewness > 1:
    #             f.write(f"  • Распределение сильно смещено вправо\n")
    #             f.write(f"  • Большинство значений меньше среднего\n")
    #         elif analysis.skewness < -1:
    #             f.write(f"  • Распределение сильно смещено влево\n")
    #             f.write(f"  • Большинство значений больше среднего\n")
    #
    #         if analysis.kurtosis > 3:
    #             f.write(f"  • Распределение имеет тяжелые хвосты\n")
    #             f.write(f"  • Больше экстремальных значений чем в нормальном распределении\n")
    #         elif analysis.kurtosis < 3:
    #             f.write(f"  • Распределение имеет легкие хвосты\n")
    #             f.write(f"  • Меньше экстремальных значений чем в нормальном распределении\n")
    #
    #         if analysis.is_normal:
    #             f.write(f"  • Распределение близко к нормальному\n")
    #             f.write(f"  • Можем применять параметрические тесты\n")
    #
    #         f.write(f"\n")
    #         f.write(f"Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    #
    #     self.logger.info(f"📄 Текстовый отчет по гистограмме сохранен: {report_path}")
    #
    # def generate_comprehensive_analysis(self,
    #                                     top_n_features: int = 10) -> None:
    #     """
    #     Генерирует комплексный анализ всех доступных метрик
    #
    #     Args:
    #         top_n_features: Количество топовых признаков для анализа
    #     """
    #     self.logger.info("🚀 Запуск комплексного анализа Steam игр...")
    #
    #     # 1. Основные распределения
    #     self.generate_game_clustering(method="kmeans", n_clusters=5, limit=1000)
    #
    #     # 2. Анализ ключевых метрик
    #     key_metrics = [
    #         "review_score",
    #         "price",
    #         "game_age_years",
    #         "achievements_count",
    #         "genres_count"
    #     ]
    #
    #     for metric in key_metrics[:top_n_features]:
    #         try:
    #             self.generate_enhanced_histogram_analysis(
    #                 value_field=metric,
    #                 bins_method="auto",
    #                 min_review_count=10
    #             )
    #         except Exception as e:
    #             self.logger.warning(f"Не удалось проанализировать метрику {metric}: {e}")
    #
    #     # 3. Анализ ключевых пар
    #     key_pairs = [
    #         ("review_score", "price"),
    #         ("review_score", "game_age_years"),
    #         ("price", "achievements_count"),
    #         ("metacritic_score", "review_score")
    #     ]
    #
    #     for x_field, y_field in key_pairs:
    #         try:
    #             self.generate_2d_histogram_analysis(
    #                 x_field=x_field,
    #                 y_field=y_field,
    #                 x_bins=20,
    #                 y_bins=20
    #             )
    #         except Exception as e:
    #             self.logger.warning(f"Не удалось проанализировать пару {x_field} vs {y_field}: {e}")
    #
    #     # 4. Создаем сводный отчет
    #     self._create_comprehensive_report()
    #
    #     self.logger.info("✅ Комплексный анализ завершен!")
