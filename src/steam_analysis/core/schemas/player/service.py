import datetime
from typing import List, Optional, Dict

from steam_analysis.core.schemas.base import BaseSchema

from steam_analysis.core.schemas.player.player import PlayerFromHttp, PlayerFullFromHttp
from .playergame import AchievementBase, OwnershipBase, ReviewBase, PlaytimeBase


class PlayerCreateReportInfo(BaseSchema):
    """Информация о создании отчета по игрокам"""
    start_steam_id: str
    end_steam_id: str
    response_time: datetime.timedelta


class PlayerDataAnalysisCreate(BaseSchema):
    """Данные анализа игрока"""
    player: PlayerFromHttp


class PlayerAnalysesSchema(BaseSchema):
    """Схема анализа игрока"""
    player: PlayerFullFromHttp


# region FillChunk schemas
class FillPlayerAnalysisChunk(BaseSchema):
    """Чанк данных анализа игроков"""
    start_steam_id: str
    end_steam_id: str
    response_time: datetime.timedelta
    data_chunk: List[Optional[PlayerDataAnalysisCreate]]

    # Статистика чанка
    processed_count: int = 0
    success_count: int = 0
    error_count: int = 0

    def get_report_info(self) -> PlayerCreateReportInfo:
        """Получить информацию об отчете"""
        return PlayerCreateReportInfo(
            start_steam_id=self.start_steam_id,
            end_steam_id=self.end_steam_id,
            response_time=self.response_time
        )

    def calculate_stats(self) -> None:
        """Рассчитать статистику чанка"""
        self.processed_count = len(self.data_chunk)
        self.success_count = sum(1 for item in self.data_chunk if item is not None)
        self.error_count = self.processed_count - self.success_count


class FillPlayerSchemaChunk(BaseSchema):
    """Чанк данных схем игроков"""
    steam_ids: List[str]
    start_time: datetime.datetime
    data_chunk: Dict[str, PlayerAnalysesSchema]
    response_time: datetime.timedelta
    success_count: int


# endregion
