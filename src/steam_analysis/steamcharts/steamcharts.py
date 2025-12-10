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
from batch_json_saver import BatchJsonSaver


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


def save_success_games(games_data, filename='received_games.json'):
    """
    Сохраняет успешные игры в JSON файл

    Args:
        games_data: список игр для добавления
        filename: имя файла (по умолчанию 'games.json')
    """

    existing_data = {"success_games": []}

    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️ Файл {filename} поврежден. Создаем новый.")

    if isinstance(games_data, list):
        existing_data["success_games"].extend(games_data)
    else:
        existing_data["success_games"].append(games_data)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Сохранено {len(games_data) if isinstance(games_data, list) else 1} игр")
    print(f"📊 Всего игр в файле: {len(existing_data['success_games'])}")

    return existing_data


def read_success_games(filename='received_games.json'):
    """
    Читает успешные игры из JSON файла

    Returns:
        Список успешных игр или пустой список если файла нет
    """

    if not os.path.exists(filename):
        print(f"⚠️ Файл {filename} не найден")
        return {"success_games": []}

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Проверяем структуру
        if "success_games" not in data:
            print(f"⚠️ Неверный формат файла {filename}")
            return {"success_games": []}

        print(f"📖 Прочитано {len(data['success_games'])} игр из {filename}")
        return data

    except json.JSONDecodeError as e:
        print(f"❌ Ошибка чтения JSON: {e}")
        return {"success_games": []}
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return {"success_games": []}


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


def save_games_in_batches(batch_size=25, base_filename='games', start_id=1, limit=4000):
    """
    Сохраняет игры батчами по batch_size
    """
    games = []
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


class SteamChartsPipeline:
    def __init__(self, read=False):
        super().__init__()
        self.read_games = read_batch_file(filename="games_all.json")
        self.jsonSaver = BatchJsonSaver()
        self.batch_id = read_last_batch()
    # def save_games_to_json(self):
    #     with get_db() as session:
    #         games = self.gameRepo.get_games_ids(session)
    #
    #         data = [f"{g.app_id}: {g.id}" for g in games]
    #
    #         # Сохраняем как JSON список строк
    #         with open('games.json', 'w') as f:
    #             json.dump(data, f, indent=2)
    #
    #         print(f"Сохранено {len(data)} записей")

    def scraping(self):
        app_ids = self.read_games.get(self.batch_id, None)
        if app_ids is None:
            return

        self.jsonSaver.batch_scrape(app_ids)
        self.batch_id += 1

    def save_last_batch_id(self):
        save_last_batch(self.batch_id)


if __name__ == "__main__":
    # Вызывается один раз:
    # save_games_in_batches(base_filename='games_all')
    peak = SteamChartsPipeline()
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


