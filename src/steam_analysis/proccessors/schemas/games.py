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


class GamesByCountCategoriesWithSubs(AbstractGameBy_):
    values: dict[int, dict[str, int]]
    ticks: list[int]
