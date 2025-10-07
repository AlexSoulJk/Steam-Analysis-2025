import datetime
from typing import List, Optional

from steam_analysis.core.schemas.base import BaseSchema
from steam_analysis.core.schemas.game.dictionaries import GenreCreate, CategoryCreate, PlatformCreate, StatsCreate, AchievCreate, AchievPercentCreate, ReviewCreate, NewCreate
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
