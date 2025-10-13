from steam_analysis.strategies.basestrategy import BaseStrategy


class GameTimedDataStrategy(BaseStrategy):

    def __init__(self):
        super().__init__()

    def get_data(self) -> list[int]:
        return [1, 2]
