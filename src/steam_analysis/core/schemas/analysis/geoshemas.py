from typing import List

from steam_analysis.core.schemas.base import BaseSchema


class GeoItem(BaseSchema):
    country_code: str


class CountryGameStat(GeoItem):
    country_code: str
    game_name: str
    player_count: int


class ListGeoItems(BaseSchema):
    data: List[GeoItem]


class ListCountryGameStat(ListGeoItems):
    data: List[CountryGameStat]
