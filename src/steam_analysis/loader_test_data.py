from pathlib import Path
from typing import Optional, List
import json

from steam_analysis.config import test_data_path
from steam_analysis.core.schemas.game.service import FillGameAnalysisChunk, FillSchemaChunk, FillAddSchemaChunk
from steam_analysis.core.schemas.player.service import FillPlayerAnalysisChunk, FillPlayerGameSchemaChunk


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

    def load_fill_schema_batch(self, filename: str) -> Optional[FillAddSchemaChunk]:
        """Загружает батч из JSON"""
        try:
            filepath = self.dir_to_load / Path(filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = f.read()

            return FillAddSchemaChunk.model_validate_json(data)

        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return None

    def load_fill_add_schema_batch(self, filename: str) -> Optional[FillSchemaChunk]:
        """Загружает батч из JSON"""
        try:
            filepath = self.dir_to_load / Path(filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = f.read()

            return FillSchemaChunk.model_validate_json(data)

        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return None

    def load_fill_user_batch(self, filename: str) -> Optional[FillPlayerAnalysisChunk]:
        """Загружает батч из JSON"""
        try:
            filepath = self.dir_to_load / Path(filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = f.read()

            return FillPlayerAnalysisChunk.model_validate_json(data)

        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return None

    def load_fill_user_game_batch(self, filename: str) -> Optional[FillPlayerGameSchemaChunk]:
        """Загружает батч из JSON"""
        try:
            filepath = self.dir_to_load / Path(filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = f.read()

            return FillPlayerGameSchemaChunk.model_validate_json(data)

        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return None

    def read_jsons(self, folder_path: str = "add_info_games"):
        """
                Читает все JSON файлы из указанной папки и возвращает список данных.

                Args:
                    folder_path: Путь к папке с JSON файлами (по умолчанию "pages")

                Returns:
                    Список словарей с данными из JSON файлов
                """

        folder_path = self.dir_to_load / folder_path

        if not folder_path.exists():
            print(f"❌ Папка {folder_path} не существует")
            return []

        if not folder_path.is_dir():
            print(f"❌ {folder_path} не является папкой")
            return []

        # Ищем все JSON файлы в папке
        json_files = list(folder_path.glob("*.json"))

        if not json_files:
            print(f"⚠️  В папке {folder_path} не найдено JSON файлов")
            return []

        print(f"📁 Найдено {len(json_files)} JSON файлов в папке {folder_path}")
        return json_files

    def load_add_schema_batchs(self, filename) -> List[Optional[FillAddSchemaChunk]]:
        all_chunks_from_file = []
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for k in data.keys():
                data_game = data[k]
                model = FillAddSchemaChunk.model_validate(data_game)
                all_chunks_from_file.append(model)

            return all_chunks_from_file

        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return []

    def load_games_batchs(self, filename) -> List[Optional[FillGameAnalysisChunk]]:
        all_chunks_from_file = []
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for k in data.keys():
                data_game = data[k]
                model = FillGameAnalysisChunk.model_validate(data_game)
                all_chunks_from_file.append(model)

            return all_chunks_from_file

        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return []

    def load_users_batchs(self, filename) -> List[Optional[FillPlayerAnalysisChunk]]:
        all_chunks_from_file = []
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for k in data.keys():
                data_game = data[k]
                model = FillPlayerAnalysisChunk.model_validate(data_game)
                all_chunks_from_file.append(model)

            return all_chunks_from_file

        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return []

    def load_users_games_batchs(self, filename) -> List[Optional[FillPlayerGameSchemaChunk]]:
        all_chunks_from_file = []
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for k in data.keys():
                data_game = data[k]
                model = FillPlayerGameSchemaChunk.model_validate(data_game)
                all_chunks_from_file.append(model)

            return all_chunks_from_file

        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return []

    def load_from_files_by_schema(self, file, model):
        """Загружает батч из JSON"""
        try:
            filepath = file
            with open(filepath, 'r', encoding='utf-8') as f:
                data = f.read()

            return model.model_validate_json(data)

        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return None


default_loader = LoaderTestData(dir_to_load=test_data_path)

# print(default_loader.load_fill_game_batch(filename="games_chunk_20251028.json").data_for_analysis_db)
