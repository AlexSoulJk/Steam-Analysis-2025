import datetime
from typing import List, Optional

from steam_analysis.core.schemas.base import BaseSchema
from steam_analysis.core.schemas.game.dictionaries import GenreCreate, CategoryCreate, PlatformCreate
from steam_analysis.core.schemas.game.game import GameCreate


class GameDataAnalysisCreate(BaseSchema):
    game: GameCreate
    genres: List[GenreCreate]
    categories: List[CategoryCreate]
    platforms: List[PlatformCreate]


class FillGameAnalysisChunk(BaseSchema):
    start_app_id: int
    end_app_id: int

    response_time: datetime.timedelta
    data_chunk: List[Optional[GameDataAnalysisCreate]]
