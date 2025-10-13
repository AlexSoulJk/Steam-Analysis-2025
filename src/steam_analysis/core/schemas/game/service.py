import datetime
from typing import List, Optional, Dict

from steam_analysis.core.schemas.base import BaseSchema
from steam_analysis.core.schemas.game.dictionaries import GenreCreate, CategoryCreate, PlatformCreate, StatsCreate, \
    AchievCreate, AchievPercentCreate, ReviewCreate, NewCreate
from steam_analysis.core.schemas.game.game import GameCreate, GameFromHttp


class GameDataAnalysisCreate(BaseSchema):
    game: GameFromHttp
    genres: List[GenreCreate]
    categories: List[CategoryCreate]
    platforms: List[PlatformCreate]


class TypeAnalysesSchema(BaseSchema):
    pass

# region FillChunk schemas
class FillGameAnalysisChunk(BaseSchema):
    start_app_id: int
    end_app_id: int

    # null amount
    # not null amount
    #

    response_time: datetime.timedelta
    data_chunk: List[Optional[GameDataAnalysisCreate]]


class FillTypeSchemaChunk(BaseSchema):
    app_ids: list[int]
    start_time: datetime.datetime
    data_chunck: Dict[int, TypeAnalysesSchema]
    response_time: datetime.timedelta
    success_count: int

# endregion

class SchemaDataAnalysisCreate(BaseSchema):
    game_id: int
    game_version: int
    stats: List[StatsCreate]
    achievs: List[AchievCreate]


class AchievDataAnalysisCreate(BaseSchema):
    game_id: int
    achievs: List[AchievPercentCreate]


class PlayersDataAnalysisCreate(BaseSchema):
    game_id: int
    number_of_players: int


class ReviewsDataAnalysisCreate(BaseSchema):
    game_id: int
    num_reviews: int
    review_score: int
    review_score_desc: str
    total_positive: int
    total_negative: int
    total_reviews: int
    reviews: List[ReviewCreate]


class NewsDataAnalysisCreate(BaseSchema):
    game_id: int
    news: List[NewCreate]
