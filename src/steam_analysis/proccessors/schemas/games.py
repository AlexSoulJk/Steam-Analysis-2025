from typing import List, Dict, Any, Optional, Union
from pydantic import Field

from steam_analysis.core.schemas.base import BaseSchema


class AbstractGameBy_(BaseSchema):
    values: list[Any]
    ticks: list[Any]


class GamesByTypes(AbstractGameBy_):
    values: dict[str, int]
    ticks: list[str]


class GamesByCategories(AbstractGameBy_):
    values: dict[str, int]
    ticks: list[str]


class GamesByGenres(GamesByCategories):
    values: dict[str, int]
    ticks: list[str]


class GamesByCountCategoriesWithSubs(AbstractGameBy_):
    values: dict[int, dict[str, int]]
    ticks: list[int]


class GamesReleaseBySeason(AbstractGameBy_):
    values: dict[str, int]
    ticks: list[str]


class GamesReleaseBySeasonByGenre(AbstractGameBy_):
    values: dict[str, dict[str, int]]
    ticks: list[str]

# дальше (бога нет) все для кластеризации

class GameFeatureVector(BaseSchema):        # <-- короче вот это мне надо из сервиса
    app_id: int                             # Уникальный ID игры (например, Steam AppID)
    name: str                               # Название игры
    features: Dict[str, Union[float, int]]  # Словарь признаков игры
    feature_values: List[float]             # Вектор значений признаков в фиксированном порядке
    feature_names: List[str]                # Имена признаков в том же порядке, что и feature_values


# Пример для GameFeatureVector:
# game = GameFeatureVector(
#     app_id=730,
#     name="Counter-Strike: Global Offensive",
#     features={
#         "price": 0.0,
#         "rating": 0.88,
#         "review_count": 6500000,
#         "is_free": 1,
#         "has_multiplayer": 1,
#         "achievements_count": 167,
#         "average_playtime": 500.5
#     },
#     feature_values=[0.0, 0.88, 6500000, 1, 1, 167, 500.5],
#     feature_names=["price", "rating", "review_count", "is_free",
#                    "has_multiplayer", "achievements_count", "average_playtime"]
# )


class GamesClusteringData(AbstractGameBy_):
    games: List[GameFeatureVector]                  # Список векторов игр
    feature_names: List[str]                        # Общие названия признаков
    feature_matrix: Optional[List[List[float]]]     # Матрица признаков
    values: Dict[str, Any]                          # Статистика (для обратной совместимости)
    ticks: List[str]                                # Список названий кластеров или признаков


# Пример для GamesClusteringData:
# clustering_data = GamesClusteringData(
#     games=[game1, game2, game3, ...],  # Список GameFeatureVector
#     feature_names=["price", "rating", "review_count", "is_free"],
#     feature_matrix=[
#         [59.99, 0.97, 500000, 0],  # Игра 1
#         [0.0, 0.88, 6500000, 1],   # Игра 2
#         [14.99, 0.98, 380000, 0],  # Игра 3
#     ],
#     values={"total_games": 3, "feature_count": 4},
#     ticks=["price", "rating", "review_count", "is_free"]
# )


class TwoDHistogramData(AbstractGameBy_):
    x_values: List[float]    # Значения по оси X
    y_values: List[float]    # Значения по оси Y
    x_bins: int = 20         # Количество бинов по оси X
    y_bins: int = 20         # Количество бинов по оси Y
    x_label: str = "X"       # Подпись оси X
    y_label: str = "Y"       # Подпись оси Y


class EnhancedHistogramData(AbstractGameBy_):   # <-- короче вот это мне надо из сервиса
    values: List[float]                         # Числовые значения для анализа
    value_name: str = "Значение"                # Название анализируемой величины
    unit: str = ""                              # Единица измерения
    bins_method: str = "auto"                   # Метод расчета бинов
    show_density: bool = True                   # Показывать кривую плотности
    show_stats: bool = True                     # Показывать статистику
    show_outliers: bool = True                  # Выделять выбросы
    compare_with_normal: bool = True            # Сравнивать с нормальным распределением
    log_scale: bool = False                     # Использовать логарифмическую шкалу
    ticks: List[str]                            # Не используется
