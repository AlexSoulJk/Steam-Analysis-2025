from typing import List, Dict, Any, Optional, Union
from pydantic import Field

from steam_analysis.core.schemas.base import BaseSchema
from  steam_analysis.proccessors.schemas.games import AbstractGameBy_


class ClusterInfo(BaseSchema):
    cluster_id: int                             # Номер кластера (0, 1, 2, ...)
    size: int                                   # Количество игр в кластере
    centroid: List[float]                       # Центр кластера в пространстве признаков
    feature_stats: Dict[str, Dict[str, float]]  # Статистика по признакам
    top_games: List[Dict[str, Any]]             # Примеры игр из кластера
    description: Optional[str]                  # Текстовое описание кластера


# ClusterInfo формируется автоматом - это тупо формат ответа + хранение/вывод инфо
# feature_stats:
# {
#     "price": {"mean": 29.99, "std": 20.5, "min": 0.0, "max": 59.99},
#     "rating": {"mean": 0.85, "std": 0.1, "min": 0.7, "max": 0.98},
#     ...
# }
# top_games:
# [
#     {"app_id": 730, "name": "CS:GO", "rating": 0.88},
#     {"app_id": 570, "name": "Dota 2", "rating": 0.82}
# ]


class ClusteringResult(AbstractGameBy_):     # <--- вот эта штука на отрисовку
    clusters: List[ClusterInfo]              # Информация о всех кластерах
    game_assignments: Dict[int, int]         # Сопоставление app_id -> cluster_id
    n_clusters: int                          # Фактическое количество кластеров
    method: str = "kmeans"                   # Использованный метод
    reduced_2d: Optional[List[List[float]]]  # Координаты для визуализации
    values: Dict[str, Any]                   # Общая статистика
    ticks: List[str]                         # Названия признаков или кластеров


# Из "непонятного":
# Это валуес
# {
#     "total_games": 100,
#     "feature_count": 7,
#     "cluster_sizes": {0: 45, 1: 32, 2: 23}
# }
# Это тики - ["Cluster_0", "Cluster_1", ...]