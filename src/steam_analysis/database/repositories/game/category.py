from steam_analysis.core.schemas.game.dictionaries import CategoryCreate, CategoryUpdate
from steam_analysis.database.models.game import Category
from steam_analysis.database.repositories.base import DictionaryRepository


class CategoryRepository(DictionaryRepository[Category, CategoryCreate, CategoryUpdate]):

    def __init__(self):
        super().__init__(Category)


