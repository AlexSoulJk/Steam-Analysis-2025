from enum import Enum
from typing import Dict, List, Any, Optional
from collections import defaultdict

import statistics

from steam_analysis.database.facade import get_db
from steam_analysis.database.repositories import GameRepository
from steam_analysis.database.repositories.game.type import TypeRepository
from steam_analysis.database.repositories.game.category import CategoryRepository

from steam_analysis.proccessors.schemas.games import (AbstractGameBy_, GamesClusteringData,
                                                      TwoDHistogramData, GamesReleaseBySeason,
                                                      EnhancedHistogramData, CharacterByTime, CharacterByPrice,
                                                      GamesByTypes, GamesByCategories, GamesByCountCategoriesWithSubs, \
                                                      GamesByGenres)


class SeasonMode(str, Enum):
    monthly = "monthly"
    quarter = "quarter"


LABELS = {

        "monthly": {
                1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
                5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
                9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
        },

        "quarter": {
                1: "Q1 (Янв-Мар)", 2: "Q2 (Апр-Июн)",
                3: "Q3 (Июл-Сен)", 4: "Q4 (Окт-Дек)"
        }
    }

class ClusteringGameProcessor:  # ЭТО СЕРВИС: ПООБЩАЛСЯ С БАЗОЙ И СОБРАЛ ДАННЫЕ ДЛЯ КЛАСТЕРИЗАЦИИ И ОТДАЛ В ПРОВАЙДЕР (ФАСАД)

    def __init__(self):
        self.game_repo = GameRepository()
        self.game_type_repo = TypeRepository()
        self.categories = CategoryRepository()

    def get_games_by_types(self) -> Optional[GamesByTypes]:
        ret = None
        with get_db() as session:
            types = self.game_type_repo.get_multi(session=session)
            ticks = list(map(lambda x: x.description, types))
            values = {type.description: self.game_repo.count(session=session, filters={"type_id": type.id})
                      for type in types}
            ret = GamesByTypes(ticks=ticks,
                               values=values)
        return ret

    def get_games_by_genres(self) -> Optional[GamesByGenres]:
        ret = None
        with get_db() as session:
            genres = self.categories.get_multi(session=session)
            genres_dict = {genre.id: genre.description for genre in genres}
            ticks = list(map(lambda x: x.description, genres))
            values = self.game_repo.count_games_by_genres_for_type(session=session)
            values = {genres_dict[value[0]]: value[1] for value in values}
            ret = GamesByGenres(ticks=ticks,
                                    values=values)
        return ret

    def get_games_by_categories(self) -> Optional[GamesByCategories]:
        ret = None
        with get_db() as session:
            categories = self.categories.get_multi(session=session)
            categories_dict = {category.id: category.description for category in categories}
            ticks = list(map(lambda x: x.description, categories))
            values = self.game_repo.count_games_by_categories_for_type(session=session)
            values = {categories_dict[value[0]]: value[1]for value in values}
            ret = GamesByCategories(ticks=ticks,
                                    values=values)
        return ret

    def get_games_by_categories_count(self) -> Optional[GamesByCountCategoriesWithSubs]:
        values = None
        with get_db() as session:
            values = self.game_repo.get_games_by_category_combinations_sql(session=session, max_category_count=15)
        return values

    def get_games_release_by_season(self, code: SeasonMode = SeasonMode.monthly) -> Optional[GamesReleaseBySeason]:
        values = None

        with get_db() as session:
            values, ticks = self.game_repo.get_games_release_by_season(session=session,
                                                                        season_mode=code)
            values = {LABELS[code][int(value[0])]: value[1] for value in values.items()}
            ticks = list(map(lambda tick: LABELS[code][int(tick)], ticks))
        return GamesReleaseBySeason(values=values, ticks=ticks)



    def get_categories_dinamics(self, categories: List[str] = None,
                                time_period: str = "yearly") -> Optional[CharacterByTime]:
        pass

    def get_genres_dinamics(self, genres: List[str] = None,
                            time_period: str = "yearly") -> Optional[CharacterByTime]:
        pass

    def get_price_distribution_by_genre(self,
                                        n: int = 10,
                                        price_type: str = 'final',
                                        min_games: int = 5) -> Optional[CharacterByPrice]:
        """
        Получает распределение цен по топ-N жанрам

        Args:
            n: количество топ жанров для анализа (по количеству игр)
            price_type: 'final' для финальной цены, 'initial' для начальной
            min_games: минимальное количество игр в жанре для включения в статистику

        Returns:
            CharacterByPrice со средними ценами по жанрам
        """
        try:
            with get_db() as session:
                price_data = self.game_repo.get_prices_by_genre(
                    session=session,
                    n=n,
                    price_type=price_type,
                    min_games=min_games
                )
                return price_data
        except Exception as e:
            print(f"Ошибка при получении распределения цен по жанрам: {e}")
            return None


    def get_game_clustering_data(
            self,
            type_id: int = 1,
            limit: Optional[int] = None
    ) -> Optional[GamesClusteringData]:
        """
            type_id: ID типа игр (по умолчанию 1 - игры)
            limit: Ограничение количества игр
            min_review_count: Минимальное количество отзывов

        """
        result = None
        with get_db() as session:
            try:
                result = self.game_repo.get_game_clustering_data(
                    session=session,
                    type_id=type_id,
                    limit=limit
                )
                if result and result.games:
                    if result.feature_matrix is None and result.games:
                        feature_matrix = []
                        feature_names = result.feature_names
                        for game in result.games:
                            if game.feature_values and len(game.feature_values) == len(feature_names):
                                feature_matrix.append(game.feature_values)
                            elif game.features:
                                vector = []
                                for feature_name in feature_names:
                                    vector.append(game.features.get(feature_name, 0.0))
                                feature_matrix.append(vector)
                                game.feature_values = vector
                            else:
                                continue
                        if feature_matrix:
                            result.feature_matrix = feature_matrix
            except Exception as e:
                print(f"Ошибка получения данных кластеризации: {e}")
                self.logger.error(f"Ошибка в get_game_clustering_data: {e}")

        return result


    def get_2d_hist_data(
            self,
            x_field: str = "review_score",
            y_field: str = "price",
            type_id: int = 1,
            x_bins: int = 20,
            y_bins: int = 20,
            min_review_count: int = 10
    ) -> Optional[TwoDHistogramData]:
        """
            x_field: Поле для оси X
            y_field: Поле для оси Y
            type_id: ID типа игр
            x_bins: Количество бинов по оси X
            y_bins: Количество бинов по оси Y
            min_review_count: Минимальное количество отзывов
        """
        result = None
        with get_db() as session:
            try:
                result = self.game_repo.get_2d_hist_data(
                    session=session,
                    x_field=x_field,
                    y_field=y_field,
                    type_id=type_id,
                    x_bins=x_bins,
                    y_bins=y_bins,
                    min_review_count=min_review_count
                )

                if result and result.x_values and result.y_values:
                    stats: Dict[str, Any] = {}
                    if result.x_values:
                        stats.update({
                            "x_mean": float(statistics.mean(result.x_values)) if result.x_values else 0,
                            "x_median": float(statistics.median(result.x_values)) if result.x_values else 0,
                            "x_min": float(min(result.x_values)) if result.x_values else 0,
                            "x_max": float(max(result.x_values)) if result.x_values else 0,
                            "x_count": len(result.x_values)
                        })
                    if result.y_values:
                        stats.update({
                            "y_mean": float(statistics.mean(result.y_values)) if result.y_values else 0,
                            "y_median": float(statistics.median(result.y_values)) if result.y_values else 0,
                            "y_min": float(min(result.y_values)) if result.y_values else 0,
                            "y_max": float(max(result.y_values)) if result.y_values else 0,
                            "y_count": len(result.y_values)
                        })
                    if len(result.x_values) == len(result.y_values) and len(result.x_values) > 1:
                        try:
                            correlation = statistics.correlation(result.x_values, result.y_values)
                            stats["correlation"] = float(correlation)
                        except:
                            stats["correlation"] = 0.0
                    stats["total_points"] = len(result.x_values)
                    result_dict = result.dict()
                    result_dict["values"] = stats
                    result = TwoDHistogramData(**result_dict)

            except Exception as e:
                print(f"Error getting 2D histogram data: {e}")
                result = TwoDHistogramData(
                    x_values=[],
                    y_values=[],
                    x_bins=x_bins,
                    y_bins=y_bins,
                    x_label=x_field,
                    y_label=y_field
                )
        return result


    def enhanced_histogram_data(
            self,
            value_field: str = "review_score",
            type_id: int = 1,
            bins_method: str = "auto",
            min_review_count: int = 10,
            show_stats: bool = True,
            show_outliers: bool = True,
            compare_with_normal: bool = True,
            log_scale: bool = False,
            filter_free: Optional[bool] = None
    ) -> Optional[EnhancedHistogramData]:
        """
            value_field: Анализируемое поле
            type_id: ID типа игр
            bins_method: Метод расчета бинов
            min_review_count: Минимальное количество отзывов
            show_stats: Показывать статистику
            show_outliers: Выделять выбросы
            compare_with_normal: Сравнивать с нормальным распределением
            log_scale: Использовать логарифмическую шкалу
            filter_free: Фильтр по бесплатным играм
        """
        result = None
        with get_db() as session:
            try:
                result = self.game_repo.enhanced_histogram_data(
                    session=session,
                    value_field=value_field,
                    type_id=type_id,
                    bins_method=bins_method,
                    min_review_count=min_review_count,
                    show_stats=show_stats,
                    show_outliers=show_outliers,
                    compare_with_normal=compare_with_normal,
                    log_scale=log_scale,
                    filter_free=filter_free
                )
                if result and result.values:
                    import statistics
                    from typing import List
                    values: List[float] = result.values
                    if values:
                        try:
                            mean_val = statistics.mean(values)
                            median_val = statistics.median(values)
                            std_val = statistics.stdev(values) if len(values) > 1 else 0
                            min_val = min(values)
                            max_val = max(values)
                            quantiles = []
                            if len(values) >= 5:
                                sorted_vals = sorted(values)
                                for q in [0.25, 0.5, 0.75, 0.95]:
                                    idx = int(len(sorted_vals) * q)
                                    idx = min(idx, len(sorted_vals) - 1)
                                    quantiles.append(sorted_vals[idx])
                            ticks = [
                                f"Всего: {len(values)}",
                                f"Среднее: {mean_val:.2f}",
                                f"Медиана: {median_val:.2f}",
                                f"Мин: {min_val:.2f}",
                                f"Макс: {max_val:.2f}"
                            ]
                            if std_val > 0:
                                ticks.append(f"Стд: {std_val:.2f}")
                            if quantiles:
                                ticks.extend([
                                    f"Q1: {quantiles[0]:.2f}",
                                    f"Q3: {quantiles[2]:.2f}"
                                ])
                            filter_info = []
                            if filter_free is not None:
                                filter_info.append("Бесплатные" if filter_free else "Платные")
                            if min_review_count > 0:
                                filter_info.append(f">={min_review_count} отзывов")
                            if filter_info:
                                ticks.append(f"Фильтры: {', '.join(filter_info)}")
                            result.ticks = ticks
                        except Exception as e:
                            print(f"Error calculating statistics: {e}")
                            result.ticks = [f"Данные: {len(values)} значений"]
                    else:
                        result.ticks = ["Нет данных"]
            except Exception as e:
                print(f"Error getting enhanced histogram data: {e}")
                result = EnhancedHistogramData(
                    values=[],
                    value_name=value_field,
                    unit="",
                    bins_method=bins_method,
                    show_density=show_stats,
                    show_stats=show_stats,
                    show_outliers=show_outliers,
                    compare_with_normal=compare_with_normal,
                    log_scale=log_scale,
                    ticks=["Ошибка получения данных"]
                )
        return result
