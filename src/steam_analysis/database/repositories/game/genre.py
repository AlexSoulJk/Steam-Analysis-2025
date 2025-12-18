from steam_analysis.core.schemas.game.dictionaries import GenreCreate, GenreUpdate
from steam_analysis.database.models.game import Genre
from steam_analysis.database.repositories.base import DictionaryRepository


class GenreRepository(DictionaryRepository[Genre, GenreCreate, GenreUpdate]):

    def __init__(self):
        super().__init__(Genre)


