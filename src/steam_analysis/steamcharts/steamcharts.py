import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Tuple
import requests
import time
import random
from datetime import datetime


from steam_analysis.database.repositories.game.game import GameRepository
from steam_analysis.database.facade import get_db
from steam_analysis.steamcharts.batch_json_saver import BatchJsonSaver
from steam_analysis.steamcharts.steamcharts_repository import SteamChartsRepository
from steam_analysis.steamcharts.collect_app_id import SteamAppIdCollector


class SteamChartsPipeline:
    def __init__(self, games=None):
        super().__init__()
        if games is None:
            games = {}
        if not games:
            self.read_games = self.read_batch_file(filename="games.json")
        else:
            self.read_games = games
        self.jsonSaver = BatchJsonSaver()
        self.batch_id = self.read_last_batch()

    @staticmethod
    def save_last_batch(batch_number: int, filename: str = 'last_batch.json'):
        """
        Сохраняет номер последнего прочитанного батча

        Args:
            batch_number: номер батча (начинается с 1 или 0)
            filename: имя файла для сохранения
        """
        data = {
            "start_butch_id": batch_number,
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ Сохранен start_butch_id = {batch_number} в {filename}")
        return data

    @staticmethod
    def read_last_batch(filename: str = 'last_batch.json') -> int:
        """
        Читает номер последнего прочитанного батча

        Returns:
            Номер батча или 0 если файла нет
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            batch_number = data.get("start_butch_id", 0)
            print(f"📖 Прочитан start_butch_id = {batch_number} из {filename}")
            return batch_number

        except FileNotFoundError:
            print(f"⚠️ Файл {filename} не найден, возвращаем 0")
            return 0
        except json.JSONDecodeError:
            print(f"❌ Ошибка чтения JSON из {filename}, возвращаем 0")
            return 0

    @staticmethod
    def read_batch_file(filename: str = 'games.json') -> Dict[int, List[str]]:
        """
        Читает файл в формате {batch_index: [games_list]}

        Args:
            filename: путь к файлу

        Returns:
            Словарь {номер_батча: список_игр}
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Преобразуем ключи в int если они строки
            result = {}
            for key, value in data.items():
                if key == "metadata":
                    continue
                if key == "batches":
                    for b_id, games in value.items():
                        try:
                            batch_num = int(b_id)
                        except ValueError:
                            batch_num = key  # оставляем как есть если не число
                        result[batch_num] = games

            print(f"📖 Прочитан файл {filename}")
            print(f"   Найдено батчей: {len(result)}")

            total_games = sum(len(games) for games in result.values())
            print(f"   Всего игр: {total_games}")

            return result

        except FileNotFoundError:
            print(f"⚠️ Файл {filename} не найден")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
            return {}
        except Exception as e:
            print(f"❌ Ошибка чтения файла: {e}")
            return {}

    @staticmethod
    def save_games_in_batches(batch_size=25, base_filename='games', all_games=None):
        """
        Сохраняет игры батчами по batch_size
        """
        if not all_games:
            with get_db() as session:
                games = GameRepository().get_games_ids(session)

            all_games = [g.app_id for g in games]

        # Создаем структуру для батчей
        result = {
            "metadata": {
                "total_games": len(all_games),
                "batch_size": batch_size,
                "created_at": datetime.now().isoformat(),
            },
            "batches": {}
        }

        # Создаем батчи
        batch_number = 1
        for i in range(0, len(all_games), batch_size):
            batch_games = all_games[i:i + batch_size]

            # Добавляем в общую структуру
            result["batches"][batch_number] = batch_games
            batch_number += 1

        # Сохраняем все в одном файле
        with open(f"{base_filename}.json", 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Сохранено: {len(all_games)} игр в {batch_number - 1} батчах")
        return result

    def generate_app_ids_batch(self):
        read_charts = SteamChartsRepository()
        read_charts.read_jsons()
        exist_app_ids = read_charts.get_app_ids_from_files()
        all_app_ids = SteamAppIdCollector.read_app_ids_from_json()
        games_ids = [x for x in all_app_ids if x not in exist_app_ids]
        self.save_games_in_batches(all_games=games_ids)

    def scraping(self):
        app_ids = self.read_games.get(self.batch_id, None)
        if app_ids is None:
            return

        self.jsonSaver.batch_scrape(app_ids)
        self.batch_id += 1

    def save_last_batch_id(self):
        self.save_last_batch(self.batch_id)

    def processed_batches(self):
        count_bathes = len(self.read_games)
        for _ in range(count_bathes):
            start_time = time.perf_counter()
            print(f"\nINFO: start batch {self.batch_id}...")
            self.scraping()

            print(f"\nINFO: start batch {self.batch_id}...")
            self.scraping()
            end_time = time.perf_counter()
            elapsed = end_time - start_time

            self.save_last_batch_id()
            print(f"⏱️  reaponse_time {elapsed:.3f} сек...")
            if elapsed < 60:
                pause = 60 - elapsed
                print(f"⏸️  Пауза {pause:.1f} сек...")
                time.sleep(pause)


if __name__ == "__main__":
    # Вызывается один раз:
    # save_games_in_batches(base_filename='games_all')

    peak = SteamChartsPipeline()
    # peak.generate_app_ids_batch()
    for _ in range(100):
        start_time = time.perf_counter()
        print(f"\nINFO: start batch {peak.batch_id}...")
        peak.scraping()

        print(f"\nINFO: start batch {peak.batch_id}...")
        peak.scraping()
        end_time = time.perf_counter()
        elapsed = end_time - start_time

        peak.save_last_batch_id()
        print(f"⏱️  reaponse_time {elapsed:.3f} сек...")
        if elapsed < 60:
            pause = 60 - elapsed
            print(f"⏸️  Пауза {pause:.1f} сек...")
            time.sleep(pause)


