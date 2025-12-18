import datetime
from typing import List, Optional, Dict

from steam_analysis.core.schemas.analysis.game import GameAnalysisChunkForRequest
from steam_analysis.core.schemas.base import BaseSchema
from steam_analysis.core.schemas.game.dictionaries import GenreCreate, CategoryCreate, PlatformCreate, StatsCreate, \
    AchievCreate, AchievPercentCreate, ReviewCreate, NewCreate
from steam_analysis.core.schemas.game.game import GameCreate, GameFromHttp
from steam_analysis.core.schemas.game.ratings import RatingHttp

class GameCreateReportInfo(BaseSchema):
    start_app_id: int
    end_app_id: int
    response_time: datetime.timedelta


class UserDataAnalysisCreate(BaseSchema):
    game: GameFromHttp
    genres: List[GenreCreate]
    categories: List[CategoryCreate]
    platforms: List[PlatformCreate]
  

class SchemaCreate(BaseSchema):
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
    # reviews: List[ReviewCreate]


class NewsDataAnalysisCreate(BaseSchema):
    game_id: int
    news: List[NewCreate]


class TypeAnalysesSchema(BaseSchema):
    news: Optional[NewsDataAnalysisCreate]
    achiev_persentage: Optional[AchievDataAnalysisCreate]
    # global_stats: тут нет схемки :(
    number_of_players: Optional[PlayersDataAnalysisCreate]
    reviews: Optional[ReviewsDataAnalysisCreate]


class Price(BaseSchema):
    game_id: int
    currency: str
    initial: int
    final: int
    discount_percent: int


class AddDetails(BaseSchema):
    game_id: int
    developers: List[str]
    publishers: List[str]
    price_overview: Optional[Price]
    ratings: List[RatingHttp]


class AddInfo(BaseSchema):
    add_details: Optional[AddDetails]
    schema_data: Optional[SchemaCreate]
    achiev_persentage: Optional[AchievDataAnalysisCreate]
    review_info: Optional[ReviewsDataAnalysisCreate]


# region FillChunk schemas
class FillGameAnalysisChunk(BaseSchema):
    data_for_analysis_db: GameAnalysisChunkForRequest
    data_chunk: List[Optional[UserDataAnalysisCreate]]

    def get_report_into(self) -> GameCreateReportInfo:
        return GameCreateReportInfo(start_app_id=self.start_app_id,
                                    end_app_id=self.end_app_id,
                                    response_time=self.response_time)


class FillSchemaChunk(BaseSchema):
    data_for_analysis_db: GameAnalysisChunkForRequest
    data_chunk: List[Optional[SchemaCreate]]

    def get_report_into(self) -> GameCreateReportInfo:
        return GameCreateReportInfo(start_app_id=self.start_app_id,
                                    end_app_id=self.end_app_id,
                                    response_time=self.response_time)


class FillAddSchemaChunk(BaseSchema):
    data_for_analysis_db: GameAnalysisChunkForRequest
    data_chunk: List[Optional[AddInfo]]

    def get_report_into(self) -> GameCreateReportInfo:
        return GameCreateReportInfo(start_app_id=self.start_app_id,
                                    end_app_id=self.end_app_id,
                                    response_time=self.response_time)


class FillTypeSchemaChunk(BaseSchema):
    app_ids: list[int]
    start_time: datetime.datetime
    data_chunck: Dict[int, TypeAnalysesSchema]
    response_time: datetime.timedelta
    success_count: int


# endregion


