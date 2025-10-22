import json
from datetime import datetime
from pathlib import Path

from steam_analysis.config import test_data_path
from steam_analysis.core.schemas.game.service import FillGameAnalysisChunk, FillTypeSchemaChunk
from steam_analysis.core.schemas.player.service import FillPlayerAnalysisChunk, FillPlayerSchemaChunk


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
        pass

    def save_fill_player_butch(self, fill_model: FillPlayerAnalysisChunk) -> bool:
        """Сохраняет батч данных без информации по играм в JSON файл"""
        try:
            # Создаем имя файла с timestamp и диапазоном app_id
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"players_{timestamp}_{fill_model.success_count}.json"
            filepath = self.dir_to_save / Path(filename)

            # Конвертируем в словарь с обработкой специальных типов
            data_dict = fill_model.model_dump()

            # Сохраняем в JSON с красивым форматированием
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=2, ensure_ascii=False, default=str)

            print(f"✅ Данные сохранены в: {filepath}")
            print(f"📊 Статистика:")
            print(f"   - Диапазон steam_id: {fill_model.start_steam_id} - {fill_model.end_steam_id}")
            print(f"   - Пользователей в батче: {fill_model.processed_count}")
            print(f"   - Успешных парсингов: {fill_model.success_count}")
            print(f"   - Время выполнения: {fill_model.response_time}")

            return True

        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            return

    def save_fill_player_time_butch(self, fill_model: FillPlayerSchemaChunk) -> bool:
        """Сохраняет батч данных с информацией по играм в JSON файл"""
        try:
            # Создаем имя файла с timestamp и диапазоном app_id
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"players_timed_{timestamp}_{fill_model.success_count}.json"
            filepath = self.dir_to_save / Path(filename)

            # Конвертируем в словарь с обработкой специальных типов
            data_dict = fill_model.model_dump()

            # Сохраняем в JSON с красивым форматированием
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=2, ensure_ascii=False, default=str)

            print(f"✅ Данные сохранены в: {filepath}")
            print(f"📊 Статистика:")
            print(f"   - Диапазон steam_id: {fill_model.steam_ids[0]} - {fill_model.steam_ids[-1]}")
            print(f"   - Пользователей в батче: {len(fill_model.data_chunk)}")
            print(f"   - Успешных парсингов: {fill_model.success_count}")
            print(f"   - Время выполнения: {fill_model.response_time}")

            return True

        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            return False


default_saver = SaveTestData(test_data_path)
