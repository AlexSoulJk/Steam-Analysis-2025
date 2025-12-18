from enum import Enum


class ResourceCodes(str, Enum):
    """Коды ресурсов с типизацией"""
    GAME_LIST = "GameList"
    GAME_CATEGORIES = "GameCategories"
    USER_LIST = "UserList"