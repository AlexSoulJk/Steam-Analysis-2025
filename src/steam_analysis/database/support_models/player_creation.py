from typing import List, Dict, Any
from dataclasses import dataclass

from steam_analysis.database.models import User, UserPlaytime, UserGameOwnership, UserAchievement, Friend, Review, \
    UserLogoffHistory


@dataclass
class PreparedForPlayerCreation:
    """Подготовленные данные для создания игроков"""
    friends: Dict[str, List[User]]
    no_created_friends: Dict[str, List[str]]
    # playtimes: Dict[str, UserPlaytime]
    # ownerships: Dict[str, UserGameOwnership]
    # achievements: Dict[str, UserAchievement]
    # friends: Dict[str, Friend]
    # reviews: Dict[str, Review]
