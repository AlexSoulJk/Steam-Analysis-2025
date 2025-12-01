from typing import Any

from steam_analysis.core.schemas.base import BaseSchema


class GameBySmth(BaseSchema):
    values: list[Any]
    ticks: list[Any]


class GamesByTypes(BaseSchema):
    values: dict[str, int]
    ticks: list[str]
