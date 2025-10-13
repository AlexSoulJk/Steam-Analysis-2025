from abc import ABC, abstractmethod
from typing import Any


class BaseStrategy(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def get_data(self) -> Any:
        pass

    @abstractmethod
    def create_report(self, data):
        pass
