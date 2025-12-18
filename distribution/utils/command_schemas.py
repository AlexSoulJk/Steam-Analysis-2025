# ---------- 1. Формирование стратегии: Создание ----------
from enum import Enum
from typing import Optional, Literal, Union, List

from pydantic import Field

from steam_analysis.core.schemas.base import BaseSchema


class SubjectEnum(str, Enum):
    player = "Player"
    game = "Game"


class BaseConfigCommandSchema(BaseSchema):
    command: Literal["base"]


class CreateStrategyConfig(BaseConfigCommandSchema):
    """Конфиг для .exe --create_strategy"""
    command: Literal["create_strategy"]  # Для идентификации
    subject: SubjectEnum
    path_to_data: Optional[str] = Field(
        default="",
        description="Путь к JSON-файлу с новыми данными (играми или игроками)"
    )


# ---------- 2. Формирование стратегии: Обновление ----------
class UpdateStrategyConfig(BaseConfigCommandSchema):
    """Конфиг для .exe --update_strategy"""
    command: Literal["update_strategy"]  # Для идентификации
    subject: SubjectEnum
    path_to_data: Optional[str] = Field(
        default="",
        description="Путь к JSON-файлу с данными для обновления"
    )


# ---------- 3. Сбор данных ----------
class CollectDataConfig(BaseConfigCommandSchema):
    """Конфиг для .exe --collect_data"""
    command: Literal["collect_data"]
    subject: SubjectEnum
    stage: int = Field(ge=0, le=1, description="Номер stage: 0 или 1")
    processor_name: str = Field(default="FullSuccesser", description="Имя процессора")
    steam_api_key: str = ""
    amount_of_butch: int = 10
    path_to_save: Optional[str] = Field(
        default="",
        description="Путь к папке для сохранения JSON-ов (будет создана подпапка)"
    )


class CollectDataPeeksConfig(BaseConfigCommandSchema):
    """Конфиг для .exe --collect_data_peeks"""
    command: Literal["collect_data_peeks"]
    path_to_save: Optional[str] = Field(
        default="",
        description="Путь к папке для сохранения JSON-ов (будет создана подпапка)"
    )


# ---------- 4. Добавление данных в АБД ----------
class FillAnalysDBConfig(BaseConfigCommandSchema):
    """Конфиг для .exe --fill_analys_db"""
    command: Literal["fill_analys_db"]
    subject: SubjectEnum
    stage: int = Field(ge=0, le=1, description="Номер stage: 0 или 1")
    path_to_load: Optional[str] = Field(
        default="",
        description="Путь к папке, откуда подгружать JSON-ы"
    )


class FillAnalysDBPeeksConfig(BaseConfigCommandSchema):
    """Конфиг для .exe --fill_analys_db_peeks"""
    command: Literal["fill_analys_db_peeks"]
    path_to_load: Optional[str] = Field(
        default="",
        description="Путь к папке, откуда подгружать JSON-ы"
    )


# ---------- 5. Решение аналитической задачи ----------
class CalculateConfig(BaseConfigCommandSchema):
    """Конфиг для .exe --calculate"""
    command: Literal["calculate"]
    task: Union[int, Literal["all"]] = Field(
        default="all",
        description="Номер таски: список [0..4] или 'all'"
    )
    graph: Union[List[int], Literal["all"]] = Field(
        default="all",
        description="Номер графика: список или 'all'"
    )
    path_to_save: Optional[str] = Field(
        default="",
        description="Путь к папке для сохранения JSON-ов (будет создана подпапка)"
    )


# ---------- 6. Выгрузка в Google Таблицы ----------
class GoogleLoadConfig(BaseConfigCommandSchema):
    """Конфиг для .exe --google_load"""
    command: Literal["google_load"]
    task: Union[int, Literal["all"]] = Field(
        default="all",
        description="Номер таски: список [0..4] или 'all'"
    )
    graph: Union[List[int], Literal["all"]] = Field(
        default="all",
        description="Номер графика: список или 'all'"
    )
    # Возможно, здесь нужны credentials или ссылка на таблицу
    spreadsheet_url: Optional[str] = Field(default="", description="URL Google-таблицы")
    credentials_path: Optional[str] = Field(default="", description="Путь к credentials")


# ---------- 7. Визуализация ----------
class VisualizeConfig(BaseConfigCommandSchema):
    """Конфиг для .exe --visualize"""
    command: Literal["visualize"]
    task: Union[int, Literal["all"]] = Field(
        default="all",
        description="Номер таски: список [0..4] или 'all'"
    )
    graph: Union[List[int], Literal["all"]] = Field(
        default="all",
        description="Номер графика: список или 'all'"
    )
    path_to_save: Optional[str] = Field(
        default="",
        description="Путь к папке для сохранения картинок (будет создана подпапка)"
    )
    path_to_data: Optional[str] = Field(
        default="",
        description="Путь к папке с данными для визуализации"
    )
