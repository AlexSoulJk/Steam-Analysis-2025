import json
from datetime import datetime
from pathlib import Path

from steam_analysis.config import test_data_path, test_data_add_game_path
from steam_analysis.core.schemas.analysis.game import GameAnalysisChunkCreate, GameAnalysisFromJson
from steam_analysis.core.schemas.game.service import FillGameAnalysisChunk, FillTypeSchemaChunk, FillAddSchemaChunk
from steam_analysis.core.schemas.player.service import FillPlayerAnalysisChunk, FillPlayerGameSchemaChunk


class SaveTestData:

    def __init__(self, dir_to_save: str):
        self.dir_to_save = Path(dir_to_save)
        self.current_file = None
        self.current_batch_count = 0
        self.current_file_data = {}

    def save_data(self, fill_model, filepath):
        data_dict = fill_model.model_dump()

        # Сохраняем в JSON с красивым форматированием
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, indent=2, ensure_ascii=False, default=str)

    def save_fill_game_batch(self, fill_model: FillGameAnalysisChunk):
        """Сохраняет батч данных в JSON файл"""
        try:
            # Создаем имя файла с timestamp и диапазоном app_id
            timestamp = datetime.now().strftime("%Y%m%d%M")
            filename = f"games_chunk_{timestamp}.json"
            filepath = self.dir_to_save / Path(filename)

            # Конвертируем в словарь с обработкой специальных типов
            data_dict = fill_model.model_dump()

            # Сохраняем в JSON с красивым форматированием
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=2, ensure_ascii=False, default=str)

            print(f"✅ Данные сохранены в: {filepath}")
            print(f"📊 Статистика:")
            # print(f"   - Диапазон app_id: {fill_model.start_app_id} - {fill_model.end_app_id}")
            print(f"   - Игр в батче: {len(fill_model.data_chunk)}")
            # print(f"   - Успешных парсингов: {sum(1 for item in fill_model.data_chunk if item is not None)}")
            print(f"   - Время выполнения: {fill_model.data_for_analysis_db.chunk.response_time}")

            return filepath

        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            return None

    def save_fill_add_info_game_batch(self, fill_model: FillAddSchemaChunk):
        """Сохраняет батч данных в JSON файл"""
        try:
            # Создаем имя файла с timestamp и диапазоном app_id
            timestamp = datetime.now().strftime("%Y%m%d%M")
            filename = f"games_add_info_chunk_{timestamp}.json"
            filepath = self.dir_to_save / Path(filename)

            # Конвертируем в словарь с обработкой специальных типов
            data_dict = fill_model.model_dump()

            # Сохраняем в JSON с красивым форматированием
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=2, ensure_ascii=False, default=str)

            print(f"✅ Данные сохранены в: {filepath}")
            print(f"📊 Статистика:")
            # print(f"   - Диапазон app_id: {fill_model.start_app_id} - {fill_model.end_app_id}")
            print(f"   - Игр в батче: {len(fill_model.data_chunk)}")
            # print(f"   - Успешных парсингов: {sum(1 for item in fill_model.data_chunk if item is not None)}")
            print(f"   - Время выполнения: {fill_model.data_for_analysis_db.chunk.response_time}")

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

    def save_fill_player_butch(self, fill_model: FillPlayerAnalysisChunk):
        """Сохраняет батч данных без информации по играм в JSON файл"""
        try:
            # Создаем имя файла с timestamp и диапазоном app_id
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"players_{timestamp}_{len(fill_model.data_chunk)}.json"
            filepath = self.dir_to_save / Path(filename)

            # Конвертируем в словарь с обработкой специальных типов
            data_dict = fill_model.model_dump()

            # Сохраняем в JSON с красивым форматированием
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=2, ensure_ascii=False, default=str)

            print(f"✅ Данные сохранены в: {filepath}")
            print(f"📊 Статистика:")
            print(f"   - Пользователей в батче: {len(fill_model.data_chunk)}")
            print(f"   - Время выполнения: {fill_model.data_for_analysis_db.chunk.response_time}")

            return filepath

        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            return

    def save_fill_player_game_butch(self, fill_model: FillPlayerGameSchemaChunk):
        """Сохраняет батч данных без информации по играм в JSON файл"""
        try:
            # Создаем имя файла с timestamp и диапазоном app_id
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"players_game_{timestamp}_{len(fill_model.data_chunk)}.json"
            filepath = self.dir_to_save / Path(filename)

            # Конвертируем в словарь с обработкой специальных типов
            data_dict = fill_model.model_dump()

            # Сохраняем в JSON с красивым форматированием
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=2, ensure_ascii=False, default=str)

            print(f"✅ Данные сохранены в: {filepath}")
            print(f"📊 Статистика:")
            print(f"   - Пользователей в батче: {len(fill_model.data_chunk)}")
            print(f"   - Время выполнения (с учетом времени заполнения информации по пользователям): "
                  f"{fill_model.data_for_analysis_db.chunk.response_time}")

            return filepath

        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            return

    def save_fill_game_analysis_butch_chunck(self, data_for_create:
                                                    tuple[list[GameAnalysisChunkCreate], list[list[GameAnalysisFromJson]]]):
        try:
            # Создаем имя файла с timestamp и диапазоном app_id
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"game_chunk_create_{timestamp}.json"
            filepath = self.dir_to_save / Path(filename)
            # Конвертируем в словарь с обработкой специальных типов
            # Сохраняем в JSON с красивым форматированием
            chunk, games_in_chunks = data_for_create
            res = []
            for chunk, games in zip(chunk, games_in_chunks):
                res.append({"chunk": chunk.model_dump(),
                            "games": list(map(lambda x: x.model_dump(), games))})

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(res, f, indent=2, ensure_ascii=False, default=str)

            print(f"✅ Данные для создания бача игр сохранены в: {filepath}")
            return True

        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            return False

    def batch_save_data_simple(self, fill_model: 'FillAddSchemaChunk'):
        """Упрощенная версия с последовательным сохранением"""
        try:
            chunk_id = fill_model.data_for_analysis_db.chunk.id
            data_to_save = fill_model.model_dump()

            # Проверяем, нужно ли создать новый файл
            if (self.current_file is None or
                    self.current_batch_count >= 50 or
                    not self.current_file.exists()):
                # Создаем новый файл
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"games_add_info_chunk_{timestamp}.json"
                self.current_file = self.dir_to_save / filename
                self.current_batch_count = 0
                self.current_file_data = {}
                print(f"📁 Создан новый файл: {filename}")

            # Добавляем данные
            self.current_file_data[str(chunk_id)] = data_to_save
            self.current_batch_count += 1

            # Сохраняем в файл
            with open(self.current_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_file_data, f, indent=2, ensure_ascii=False, default=str)

            print(f"✅ Батч {chunk_id} сохранен в {self.current_file.name}")
            print(f"   - Батчей в файле: {self.current_batch_count}/50")

            if self.current_batch_count >= 50:
                print(f"⚠️  Достигнут лимит в 50 батчей. Следующий батч будет в новом файле.")

            return self.current_file

        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            return None



default_saver = SaveTestData(test_data_path)
save_add_info_games = SaveTestData(test_data_add_game_path)
