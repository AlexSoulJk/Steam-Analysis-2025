import json
import os
import time
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import random


class SteamAppIdCollector:
    """
    Упрощенный сборщик app_id с сайта Steam Charts.
    Собирает ID игр с топ страниц и сохраняет в JSON.
    """

    # BASE_URL = "https://steamcharts.com/top"

    def __init__(self,
                 output_file: str = "steam_app_ids.json",
                 base_url: str = "https://steamcharts.com/top",
                 page_ident: str = "/p."
                 ):
        """
        Args:
            output_file: Путь к файлу для сохранения app_id
        """
        self.BASE_URL = base_url
        self.PAGE_URL = f"{self.BASE_URL}{page_ident}"
        self.output_file = output_file
        self.DELAY_MIN = 0.5
        self.DELAY_MAX = 1
        # Заголовки для запросов (упрощенные)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        # Загружаем существующие данные или создаем новые
        self.data = self._load_or_create_data()

        print(f"📁 Файл: {self.output_file}")
        print(f"🆔 Найдено app_id: {len(self.data['app_ids'])}")
        print(f"📄 Обработано страниц: {self.data.get('last_page', 0)}")

    def _load_or_create_data(self) -> Dict:
        """Загружает существующие данные или создает новый файл"""
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                print(f"⚠️  Не удалось загрузить файл {self.output_file}, создаю новый")

        # Простая структура JSON файла
        return {
            "app_ids": [],  # Список всех найденных app_id
            "last_page": 0,  # Номер последней обработанной страницы
            "total_count": 0,  # Общее количество app_id
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated": None
        }

    def _save_data(self):
        """Сохраняет данные в JSON файл"""
        self.data["total_count"] = len(self.data["app_ids"])
        self.data["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            print(f"💾 Сохранено в {self.output_file}")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            return False

    def _extract_app_ids(self, html: str) -> List[str]:
        """
        Извлекает все app_id из HTML страницы.

        Args:
            html: HTML код страницы

        Returns:
            Список найденных app_id
        """
        soup = BeautifulSoup(html, 'html.parser')
        app_ids = []

        # Ищем таблицу с играми
        table = soup.find('table', {'id': 'top-games'})
        if not table:
            return app_ids

        # Ищем все строки с играми
        rows = table.find_all('tr')

        for row in rows:
            # Ищем ячейку с названием игры
            game_cell = row.find('td', class_='game-name left')
            if game_cell:
                # Ищем ссылку в ячейке
                link = game_cell.find('a', href=True)
                if link and '/app/' in link['href']:
                    # Извлекаем app_id из ссылки
                    app_id = link['href'].split('/app/')[1].strip('/')
                    if app_id and app_id.isdigit():
                        app_ids.append(app_id)

        return app_ids

    def _extract_app_ids_v2(self, html: str):
        """For steamplayercount"""
        soup = BeautifulSoup(html, 'html.parser')

        # Найти все ссылки, содержащие /app/ и извлечь app_id
        app_ids = []
        for link in soup.find_all('a', href=True):
            if '/app/' in link['href']:
                # Извлекаем число после /app/
                parts = link['href'].split('/app/')
                if len(parts) > 1 and parts[1].strip():
                    app_id = parts[1].strip()
                    if app_id.isdigit():  # Проверяем, что это число
                        app_ids.append(app_id)

        # Удаляем дубликаты
        unique_app_ids = list(set(app_ids))
        print(f"Найдено {len(unique_app_ids)} уникальных app_id:")
        return unique_app_ids

    def _get_page_html(self, page_num: int) -> Optional[str]:
        """
        Скачивает HTML страницу.

        Args:
            page_num: Номер страницы

        Returns:
            HTML контент или None при ошибке
        """
        if page_num == 1:
            url = self.BASE_URL
        else:
            url = f"{self.PAGE_URL}{page_num}"

        try:
            delay = random.uniform(self.DELAY_MIN, self.DELAY_MAX)
            print(f"  Ждем {delay:.1f} сек...")
            time.sleep(delay)
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"  ❌ Ошибка загрузки страницы {page_num}: {e}")
            return None

    def collect_page(self, page_num: int) -> bool:
        """
        Собирает app_id с одной страницы.

        Args:
            page_num: Номер страницы

        Returns:
            True если успешно, False если ошибка
        """
        print(f"\n📄 Страница {page_num}: ", end="")

        # Скачиваем страницу
        html = self._get_page_html(page_num)
        if not html:
            return False

        # Извлекаем app_id
        # found_ids = self._extract_app_ids(html)
        found_ids = self._extract_app_ids_v2(html)

        if not found_ids:
            print("не найдено app_id")
            return False

        # Добавляем новые app_id
        existing_ids = set(self.data["app_ids"])
        new_ids = [app_id for app_id in found_ids if app_id not in existing_ids]

        for app_id in new_ids:
            self.data["app_ids"].append(app_id)

        # Обновляем номер последней страницы
        self.data["last_page"] = page_num

        print(f"найдено {len(found_ids)}, новых {len(new_ids)}")
        return True

    def collect_pages(self, start_page: int = 1, end_page: int = 10):
        """
        Собирает app_id с диапазона страниц.

        Args:
            start_page: Начальная страница
            end_page: Конечная страница
        """
        print(f"\n🚀 Начинаем сбор app_id")
        print(f"📄 Страницы: {start_page} - {end_page}")

        total_new = 0
        successful_pages = 0

        for page_num in range(start_page, end_page + 1):
            # Проверяем, не обрабатывали ли уже эту страницу
            if page_num <= self.data["last_page"]:
                print(f"📄 Страница {page_num}: уже обработана, пропускаем")
                continue

            # Собираем данные со страницы
            if self.collect_page(page_num):
                successful_pages += 1

                # Автосохранение каждые 10 страниц
                if page_num % 10 == 0:
                    print(f"\n💾 Автосохранение после {page_num} страниц...")
                    self._save_data()

            # Пауза между запросами
            if page_num < end_page:
                time.sleep(1)  # Фиксированная пауза 1 секунда

        # Финальное сохранение
        print(f"\n💾 Финальное сохранение...")
        self._save_data()

        # Итоги
        total_count = len(self.data["app_ids"])
        print(f"\n📊 Сбор завершен!")
        print(f"✅ Успешных страниц: {successful_pages}/{end_page - start_page + 1}")
        print(f"🎮 Всего app_id: {total_count}")
        print(f"💾 Сохранено в: {self.output_file}")

        # Показываем примеры
        if total_count > 0:
            print(f"\n📋 Примеры app_id:")
            examples = self.data["app_ids"][:5]
            for app_id in examples:
                print(f"  • {app_id}")
            if total_count > 5:
                print(f"  ... и еще {total_count - 5}")

    def get_app_ids(self) -> List[str]:
        """Возвращает список всех собранных app_id"""
        return self.data["app_ids"].copy()

    def get_stats(self) -> Dict:
        """Возвращает статистику"""
        return {
            "total_app_ids": len(self.data["app_ids"]),
            "last_page": self.data["last_page"],
            "created": self.data["created"],
            "updated": self.data["updated"],
            "file": self.output_file
        }

    def print_stats(self):
        """Выводит статистику"""
        stats = self.get_stats()

        print(f"\n📊 Статистика:")
        print(f"   Всего app_id: {stats['total_app_ids']}")
        print(f"   Последняя страница: {stats['last_page']}")
        print(f"   Создано: {stats['created']}")
        print(f"   Обновлено: {stats['updated']}")
        print(f"   Файл: {stats['file']}")

    @staticmethod
    def read_app_ids_from_json(filename='steam_app_ids.json'):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            app_ids = data.get("app_ids", [])

            if not app_ids:
                print(f"⚠️  Отсутвуют app_ids в файле")
                return []

            print(f"📁 Найдено {len(app_ids)} app_ids")
            return app_ids

        except FileNotFoundError:
            print(f"⚠️ Файл {filename} не найден")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
            return {}
        except Exception as e:
            print(f"❌ Ошибка чтения файла: {e}")
            return {}


if __name__ == "__main__":
    # steam charts
    # collector = SteamAppIdCollector("steam_app_ids.json")
    # collector_popular = SteamAppIdCollector("steamplayer_app_ids.json",
    #                                         "https://steamplayercount.com/popular",
    #                                         "?page=")
    # collector_popular.collect_pages(start_page=1, end_page=81)
    # collector_popular.print_stats()

    collector_trend = SteamAppIdCollector("steamplayer_app_ids_trends.json",
                                          "https://steamplayercount.com/trending",
                                          "?page=")
    collector_trend.collect_pages(start_page=1, end_page=52)
    collector_trend.print_stats()
