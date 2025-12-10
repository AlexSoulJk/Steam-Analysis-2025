import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Tuple
import requests
import time
import random
from datetime import datetime
from pathlib import Path


from steam_analysis.database.repositories.game.game import GameRepository
from steam_analysis.database.facade import get_db


class SteamChartsRepository:
    def __init__(self):
        super().__init__()
        self.game_repo = GameRepository()
        self.json_files = []

    def add_to_db(self):
        pass

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

