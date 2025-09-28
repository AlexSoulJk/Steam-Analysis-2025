from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class GameShortInfo:
    app_id: int
    name: str

@dataclass
class GameAnalysisData:
    """Структурированные данные игры для анализа"""
    # Базовые идентификаторы
    app_id: int
    name: str
    type: str  # game/dlc/demo/etc

    # Временные метки
    release_date: Optional[datetime]
    release_year: Optional[int]
    coming_soon: bool

    # Классификация
    genres: List[Dict[str, Any]]  # [{id, description}]
    categories: List[Dict[str, Any]]  # [{id, description}]
    developers: List[str]
    publishers: List[str]

    # Локализация
    supported_languages: List[str]
    language_options: Dict[str, bool]  # {interface, full_audio, subtitles}

    # Контент и геймплей
    is_free: bool
    achievements_count: int
    controller_support: str
    platforms: Dict[str, bool]  # {windows, mac, linux}
    game_features: Dict[str, bool]  # {single_player, multiplayer, coop, etc}

    # Коммерция
    price_info: Dict[str, Any]  # {currency, initial, final, discount_percent}

    # Метрики популярности
    recommendations_count: int
    metacritic_score: Optional[int]
    review_score: float  # 0.0-1.0
    review_count: int

    # Динамические метрики (будут заполняться отдельно)
    current_players: int = 0
    peak_players_24h: int = 0
    peak_players_all_time: int = 0