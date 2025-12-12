from typing import Any

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


# Хуета для кластеризации от дипсика:

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
import numpy as np


class GameFeatureVector(BaseSchema):
    """Вектор признаков для одной игры"""
    app_id: int
    name: str
    features: Dict[str, Union[float, int]]  # Название признака -> значение
    feature_values: List[float]  # Вектор значений в фиксированном порядке
    feature_names: List[str]  # Соответствующие имена признаков


class GamesClusteringData(AbstractGameBy_):
    """Данные для кластеризации игр"""
    games: List[GameFeatureVector] = Field(default_factory=list)
    feature_names: List[str] = Field(default_factory=list)
    feature_matrix: Optional[List[List[float]]] = None  # Матрица признаков [игры × признаки]

    # Для обратной совместимости с AbstractGameBy_
    values: Dict[str, Any] = Field(default_factory=dict)  # Можем хранить статистику кластеров
    ticks: List[str] = Field(default_factory=list)  # Можем хранить названия кластеров или признаки


class ClusterInfo(BaseSchema):
    """Информация о кластере"""
    cluster_id: int
    size: int
    centroid: List[float]
    feature_stats: Dict[str, Dict[str, float]]  # Статистика по признакам: mean, std, min, max
    top_games: List[Dict[str, Any]]  # Топ игр в кластере
    description: Optional[str] = None  # Описание кластера


class ClusteringResult(AbstractGameBy_):
    """Результат кластеризации"""
    clusters: List[ClusterInfo]
    game_assignments: Dict[int, int]  # app_id -> cluster_id
    n_clusters: int
    method: str = "kmeans"

    # Для визуализации
    reduced_2d: Optional[List[List[float]]] = None  # Координаты в 2D (PCA/t-SNE)

    # Для обратной совместимости
    values: Dict[str, Any] = Field(default_factory=dict)
    ticks: List[str] = Field(default_factory=list)



# Хуета с хитмапами от дипсика:

from typing import Tuple, List, Dict, Any, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap


class CorrelationHeatmapData(AbstractGameBy_):
    """Данные для heatmap корреляций"""
    correlation_matrix: List[List[float]]  # Матрица корреляций
    feature_names: List[str]  # Названия признаков

    # Для обратной совместимости
    values: Dict[str, Any] = Field(default_factory=dict)
    ticks: List[str] = Field(default_factory=list)


class TwoDHistogramData(AbstractGameBy_):
    """Данные для 2D гистограммы/heatmap"""
    x_values: List[float]  # Значения по оси X
    y_values: List[float]  # Значения по оси Y
    x_bins: int = 20
    y_bins: int = 20
    x_label: str = "X"
    y_label: str = "Y"

    # Для обратной совместимости
    values: Dict[str, Any] = Field(default_factory=dict)
    ticks: List[str] = Field(default_factory=list)




# Хуета с гистограммами от дипсика:

class HistogramAnalysisResult(BaseSchema):
    """Результат анализа распределения"""
    distribution_type: str  # "normal", "exponential", "lognormal", "bimodal", "multimodal", "unknown"
    skewness: float  # Коэффициент асимметрии
    kurtosis: float  # Коэффициент эксцесса
    is_normal: bool  # Тест на нормальность (Shapiro-Wilk)
    normality_p_value: float
    mean: float
    median: float
    std: float
    iqr: float  # Interquartile range
    outliers_count: int
    percentiles: Dict[str, float]  # 1%, 5%, 25%, 50%, 75%, 95%, 99%
    modality: int  # Количество мод (пиков)


class EnhancedHistogramData(AbstractGameBy_):
    """Улучшенные данные для гистограммы"""
    values: List[float]  # Числовые значения для анализа
    value_name: str = "Значение"  # Название величины
    unit: str = ""  # Единица измерения
    bins_method: str = "auto"  # "auto", "sturges", "fd", "doane", "scott", "rice", "sqrt"
    show_density: bool = True  # Показывать кривую плотности
    show_stats: bool = True  # Показывать статистику
    show_outliers: bool = True  # Выделять выбросы
    compare_with_normal: bool = True  # Сравнивать с нормальным распределением
    log_scale: bool = False  # Логарифмическая шкала

    # Для обратной совместимости
    ticks: List[str] = Field(default_factory=list)

class GroupedHistogramData(AbstractGameBy_):
    """Данные для группированной гистограммы"""
    groups: Dict[str, List[float]]  # Название группы -> значения
    group_names: List[str]  # Порядок групп
    value_name: str = "Значение"
    show_kde: bool = True  # Показывать Kernel Density Estimation
    show_violin: bool = False  # Показывать violin plot вместо гистограммы
    normalize: bool = False  # Нормализовать каждую группу

    # Для обратной совместимости
    values: Dict[str, Any] = Field(default_factory=dict)
    ticks: List[str] = Field(default_factory=list)