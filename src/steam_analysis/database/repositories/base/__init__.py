"""
Репозитории для работы с базой данных Steam Analysis
"""
from steam_analysis.database.repositories.base.dictionary import DictionaryRepository

from steam_analysis.core.repositories.base import BaseRepository

__all__ = [
    # Базовые классы
    "BaseRepository",
    "DictionaryRepository",
]
