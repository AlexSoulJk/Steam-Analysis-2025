from pathlib import Path
from typing import Optional

from steam_analysis.config import test_data_path
from steam_analysis.core.schemas.game.service import FillGameAnalysisChunk, FillSchemaChunk


class LoaderTestData:

    def __init__(self, dir_to_load: str):
        self.dir_to_load = Path(dir_to_load)

    def load_fill_game_batch(self, filename: str) -> Optional[FillGameAnalysisChunk]:
        """Загружает батч из JSON"""
        try:
            filepath = self.dir_to_load / Path(filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = f.read()

            return FillGameAnalysisChunk.model_validate_json(data)

        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return None
        
    def load_fill_schema_batch(self, filename: str) -> Optional[FillSchemaChunk]:
        """Загружает батч из JSON"""
        try:
            filepath = self.dir_to_load / Path(filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = f.read()

            return FillSchemaChunk.model_validate_json(data)

        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return None

default_loader = LoaderTestData(dir_to_load=test_data_path)

# print(default_loader.load_fill_game_batch(filename="games_chunk_20251028.json").data_for_analysis_db)