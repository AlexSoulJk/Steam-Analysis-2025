from typing import List

from steam_analysis.core.schemas.base import BaseSchema


class UserBase(BaseSchema):
    id: int


class OrtBase(BaseSchema):
    id_1: int
    id_2: int


class OrtByGames(OrtBase):
    game: str


class FriendsByGames(BaseSchema):
    users: List[UserBase]
    orts: List[OrtByGames]
