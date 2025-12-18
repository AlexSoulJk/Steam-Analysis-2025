import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Tuple, Any
import requests
import time
import random
from datetime import datetime
from pathlib import Path
from sqlalchemy import select, and_, or_

from steam_analysis.database.repositories.game import PeakRepository
from steam_analysis.database.facade import get_db

from steam_analysis.database.models.game import Game
from steam_analysis.database.models.timeseries import PlayerCountHistory


class SteamChartsRepository:
    def __init__(self):
        super().__init__()
        self.peak_repos = PeakRepository()
        self.json_files = []

    def read_jsons(self, folder_path: str = "pages"):
        """
                Читает все JSON файлы из указанной папки и возвращает список данных.

                Args:
                    folder_path: Путь к папке с JSON файлами (по умолчанию "pages")

                Returns:
                    Список словарей с данными из JSON файлов
                """

        folder_path = Path(folder_path)

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
        self.json_files = json_files

    def get_app_ids_from_files(self):
        all_app_ids = []

        for json_file in self.json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                games = data.get("games", [])
                if not games:
                    continue
                all_app_ids.extend(list(games.keys()))

            except json.JSONDecodeError as e:
                print(f"  ❌ Ошибка чтения JSON в файле {json_file.name}: {e}")
            except Exception as e:
                print(f"  ❌ Ошибка чтения файла {json_file.name}: {e}")

        print(f"📊 Всего найдено app_id: {len(all_app_ids)}")
        return all_app_ids

    def add_one_part_to_db(self, games: Dict[str, Any]):
        success = False
        with get_db() as session:
            create_tables = self.peak_repos.create_bulk_from_json(games=games, session=session)
            if create_tables:
                success = True

        if success:
            print(f"✅ Бач успешно добавлен в БД")

    def add_one_file_to_db(self, all_games: Dict[str, Any], batch_size=10):
        all_games_list = list(all_games.items())

        for i in range(0, len(all_games_list), batch_size):
            batch_games = all_games_list[i:i + batch_size]
            games = dict(batch_games)
            print(f"ℹ️ Добавили бач {i} в БД")
            self.add_one_part_to_db(games)

    def add_files_to_db(self):
        for json_file in self.json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                games = data.get("games", {})
                if not games:
                    continue

                print(f"\nℹ️ Файл {json_file} успешно прочитан")
                print(f"ℹ️ Добавляем файл {json_file} в БД.....")
                self.add_one_file_to_db(games)

            except json.JSONDecodeError as e:
                print(f"  ❌ Ошибка чтения JSON в файле {json_file.name}: {e}")
            except Exception as e:
                print(f"  ❌ Ошибка чтения файла {json_file.name}: {e}")


if __name__ == "__main__":
    chart_repo = SteamChartsRepository()
    chart_repo.read_jsons("games_page")
    chart_repo.add_files_to_db()
