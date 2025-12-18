from typing import List, Dict, Any, Optional, Union
from pydantic import Field

from  steam_analysis.proccessors.schemas.games import BaseSchema, AbstractGameBy_


class HistogramAnalysisResult(BaseSchema):
    distribution_type: str          # Тип распределения
    skewness: float                 # Коэффициент асимметрии
    kurtosis: float                 # Коэффициент эксцесса
    is_normal: bool                 # Нормальное ли распределение
    normality_p_value: float        # p-value теста на нормальность
    mean: float                     # Среднее значение
    median: float                   # Медиана
    std: float                      # Стандартное отклонение
    iqr: float                      # Межквартильный размах
    outliers_count: int             # Количество выбросов
    percentiles: Dict[str, float]   # Процентили
    modality: int                   # Количество мод (пиков)


class GroupedHistogramData(BaseSchema):
    groups: Dict[str, List[float]]  # Группы значений
    group_names: List[str]          # Порядок отображения групп
    value_name: str = "Значение"    # Название величины
    show_kde: bool = True           # Показывать оценку плотности
    show_violin: bool = False       # Показывать violin plot
    normalize: bool = False         # Нормализовать распределения


# Прмер:
# groups: {
#     "Action": [59.99, 39.99, 29.99, 19.99],
#     "RPG": [39.99, 29.99, 14.99, 9.99],
#     "Strategy": [29.99, 24.99, 19.99, 14.99],
#     "Indie": [14.99, 9.99, 4.99, 0.0]
# }
#
# Например, можно цены по жанрам отрисовать
# grouped_data = GroupedHistogramData(
#     groups={
#         "Экшн": [59.99, 39.99, 29.99, 19.99, 49.99],
#         "RPG": [39.99, 29.99, 14.99, 9.99, 19.99],
#         "Стратегия": [29.99, 24.99, 19.99, 14.99, 9.99],
#         "Инди": [14.99, 9.99, 4.99, 0.0, 7.99]
#     },
#     group_names=["Экшн", "RPG", "Стратегия", "Инди"],
#     value_name="Цена игры ($)",
#     show_kde=True,
#     show_violin=False,
#     normalize=False,
#     values={"total_groups": 4},
#     ticks=[]
# )


class CorrelationHeatmapData(AbstractGameBy_):
    correlation_matrix: List[List[float]]  # Квадратная матрица корреляций
    feature_names: List[str]               # Названия признаков (для осей)
    values: Dict[str, Any]                 # Дополнительная информация
    ticks: List[str]                       # Обычно копия feature_names