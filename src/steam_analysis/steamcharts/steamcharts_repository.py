import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Tuple, Any
import requests
import time
import random
from datetime import datetime
from pathlib import Path

from steam_analysis.database.repositories.game.game import GameRepository
from steam_analysis.database.facade import get_db

from steam_analysis.database.models.game import Game
from steam_analysis.database.models.timeseries import PlayerCountHistory


class SteamChartsRepository:
    def __init__(self):
        super().__init__()
        self.game_repo = GameRepository()
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
            app_ids = [int(app_id) for app_id in games.keys()]
            exist_games = self.game_repo.get_existing_by_app_ids(app_ids, session)

            game_ids = {str(app_id): game.id for app_id, game in exist_games.items()}
            all_tables = []
            for app_id in games.keys():
                if exist_games.get(int(app_id), None) is None:
                    continue

                game = games[app_id]
                exist_games[int(app_id)].all_time_peak = game.get("all-time peak", 0)

                table = game.get("months", {})
                if not table:
                    continue

                for month in table.keys():
                    percent_gain = table[month].get("% Gain", 0.0)
                    if percent_gain == "inf" or percent_gain == "-inf" or percent_gain == "nan":
                        percent_gain = float(percent_gain)

                    gain = table[month].get("Gain", 0.0)
                    if gain == "inf" or gain == "-inf" or gain == "nan":
                        gain = float(gain)

                    all_tables.append(
                        PlayerCountHistory(
                            game_id=game_ids[app_id],
                            player_count=table[month].get("Peak Players", 0),
                            date=month,
                            avg_players=table[month].get("Avg. Players", 0.0),
                            percent_gain=percent_gain,
                            gain=gain
                        )
                    )

            if all_tables:
                session.add_all(all_tables)
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
    chart_repo.read_jsons()
    chart_repo.add_files_to_db()
