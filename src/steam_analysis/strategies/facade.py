from enum import Enum

from steam_analysis.core.schemas.game.service import GameCreateReportInfo


class StrategyInfoProvider:

    class Code(str, Enum):
        fill_game_create = "fill_game_create"
        fill_game_timed_data = "fill_game_timed_data"

    def __init__(self):
        from steam_analysis.strategies.basestrategy import BaseStrategy
        from steam_analysis.strategies.filldata import GameCreateStrategy, GameTimedDataStrategy

        self.fill_data_strategies: dict[StrategyInfoProvider.Code, BaseStrategy] = {
            StrategyInfoProvider.Code.fill_game_create: GameCreateStrategy(),
            StrategyInfoProvider.Code.fill_game_timed_data: GameTimedDataStrategy()
        }

    def _get_fill_strategy(self, code: Code):
        return self.fill_data_strategies[code]

    def get_game_create_info(self) -> tuple[int, int]:
        return self._get_fill_strategy(StrategyInfoProvider.Code.fill_game_create).get_data()

    def get_game_timed_data_info(self) -> list[int]:
        return self._get_fill_strategy(StrategyInfoProvider.Code.fill_game_timed_data).get_data()

    def add_report_game_create_info(self, report_info: GameCreateReportInfo):
        self._get_fill_strategy(StrategyInfoProvider.Code.fill_game_create).create_report(report_info)

    def add_report_game_timed_data_info(self, report_info: GameCreateReportInfo):
        self._get_fill_strategy(StrategyInfoProvider.Code.fill_game_timed_data).create_report(report_info)