from dataclasses import dataclass
from typing import Dict

from steam_analysis.database.models.game import Category, Genre, Platform, GameType


@dataclass
class PreparedForGameCreation:
    categories: Dict[str, Category]
    genres: Dict[str, Genre]
    platforms: Dict[str, Platform]
    types: Dict[str, GameType]
