import json
from datetime import datetime
from pathlib import Path

from steam_analysis.config import test_data_path
from steam_analysis.core.schemas.game.service import FillGameAnalysisChunk, FillTypeSchemaChunk


class SaveTestData:

    def __init__(self, dir_to_save: str):
        self.dir_to_save = Path(dir_to_save)

    def save_fill_game_batch(self, fill_model: FillGameAnalysisChunk):
        """Сохраняет батч данных в JSON файл"""
        try:
            # Создаем имя файла с timestamp и диапазоном app_id
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"games_{fill_model.start_app_id}_{fill_model.end_app_id}_{timestamp}.json"
            filepath = self.dir_to_save / Path(filename)

            # Конвертируем в словарь с обработкой специальных типов
            data_dict = fill_model.model_dump()

            # Сохраняем в JSON с красивым форматированием
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=2, ensure_ascii=False, default=str)

            print(f"✅ Данные сохранены в: {filepath}")
            print(f"📊 Статистика:")
            print(f"   - Диапазон app_id: {fill_model.start_app_id} - {fill_model.end_app_id}")
            print(f"   - Игр в батче: {len(fill_model.data_chunk)}")
            print(f"   - Успешных парсингов: {sum(1 for item in fill_model.data_chunk if item is not None)}")
            print(f"   - Время выполнения: {fill_model.response_time}")

            return filepath

        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            return None

    def save_fill_game_timed_data(self, fill_model: FillTypeSchemaChunk):
        """Сохраняет батч данных в JSON файл"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"timed_games_{timestamp}_{fill_model.success_count}_of_{len(fill_model.app_ids)}.json"
            filepath = self.dir_to_save / Path(filename)

            data_dict = fill_model.model_dump()

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=2, ensure_ascii=False, default=str)

            print(f"✅ Данные сохранены в: {filepath}")
            print(f"📊 Статистика:")
            print(f"   - Игры: {fill_model.app_ids}")
            print(f"   - Количество игр в батче: {len(fill_model.app_ids)}")
            print(f"   - Успешных парсингов: {fill_model.success_count}")
            print(f"   - Время выполнения: {fill_model.response_time}")

            return filepath

        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            return None

default_saver = SaveTestData(test_data_path)
