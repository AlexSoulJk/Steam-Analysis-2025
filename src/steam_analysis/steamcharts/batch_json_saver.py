import json
import os
import time
import random
from datetime import datetime
from typing import Dict, Any, Optional
import requests
from bs4 import BeautifulSoup


class BatchJsonSaver:
    ua_list = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
    ]

    def __init__(self, batch_file="pages\steam_pages.json", max_pages_per_file=100):
        """
        Сохраняет страницы в формате:
        {
            "total_games": n,
            "games": {
                "app_id": "html_content",
                "app_id": "html_content",
                ...
            }
        }

        Args:
            batch_file: Имя JSON файла для сохранения
            max_pages_per_file: Максимальное число страниц в одном файле
        """
        self.batch_file = batch_file
        self.max_pages = max_pages_per_file
        self.DELAY_MIN = 1
        self.DELAY_MAX = 2
        self.HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate'}

        # Инициализируем или загружаем существующий файл
        self.current_data = self._load_or_init_file()

    def _load_or_init_file(self) -> Dict[str, Any]:
        """Загружает существующий файл или создает новую структуру"""
        if os.path.exists(self.batch_file):
            try:
                with open(self.batch_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"📂 Загружен существующий файл: {self.batch_file}")
                print(f"   Уже сохранено страниц: {data.get('total_games', 0)}")
                return data
            except Exception as e:
                print(f"⚠️  Ошибка загрузки файла, создаю новый: {e}")

        # Новая структура
        return {
            "total_games": 0,
            "created_at": datetime.now().isoformat(),
            "last_updated": None,
            "games": {}
        }

    def _should_create_new_file(self) -> bool:
        """Проверяет, нужно ли создавать новый файл"""
        return self.current_data["total_games"] >= self.max_pages

    def _create_new_filename(self) -> str:
        """Создает имя для нового файла"""
        base_name = os.path.splitext(self.batch_file)[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        count = 1

        while True:
            new_name = f"{base_name}_{timestamp}_{count}.json"
            if not os.path.exists(new_name):
                return new_name
            count += 1

    def save_to_file(self):
        """Сохраняет текущие данные в файл"""
        self.current_data["last_updated"] = datetime.now().isoformat()

        try:
            with open(self.batch_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_data, f, indent=2, ensure_ascii=False)

            # Проверяем размер файла
            file_size = os.path.getsize(self.batch_file) / 1024 / 1024  # в МБ
            print(f"💾 Сохранено в {self.batch_file}")
            print(f"   Страниц: {self.current_data['total_games']}, Размер: {file_size:.2f} MB")

            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения файла: {e}")
            return False

    def make_request(self, url, retries=1) -> Optional[str]:
        """Безопасный запрос с повторными попытками, возвращает HTML"""
        for attempt in range(retries):
            try:
                # Случайная задержка
                delay = random.uniform(self.DELAY_MIN, self.DELAY_MAX)
                print(f"  Ждем {delay:.1f} сек...")
                time.sleep(delay)

                response = requests.get(url, headers=self.HEADERS, timeout=60)

                # Проверяем статус
                if response.status_code == 429:
                    wait = 60 * (attempt + 1) * 2
                    print(f"  Слишком много запросов. Ждем {wait} сек...")
                    time.sleep(wait)
                    continue

                if response.status_code == 404:
                    print(f"  Страница не найдена: {url}")
                    return None

                response.raise_for_status()
                return response.text

            except requests.exceptions.Timeout:
                print(f"  Таймаут (попытка {attempt + 1}/{retries})")
            except requests.exceptions.RequestException as e:
                print(f"  Ошибка запроса: {e} (попытка {attempt + 1}/{retries})")

            if attempt < retries - 1:
                retry_delay = random.uniform(30, 90)
                print(f"  Повтор через {retry_delay:.1f} сек...")
                time.sleep(retry_delay)

        return None

    @staticmethod
    def parse_steam_chart_simple(html_content: str):
        """Упрощенная версия парсера."""

        soup = BeautifulSoup(html_content, 'html.parser')

        result = {
            "all-time peak": None,
            "months": {}
        }

        # Ищем all-time peak
        for stat in soup.find_all('div', class_='app-stat'):
            text = stat.get_text()
            if 'all-time peak' in text:
                num_element = stat.find('span', class_='num')
                if num_element:
                    result["all-time peak"] = int(num_element.text.replace(',', ''))
                break

        # Обрабатываем таблицу
        table = soup.find('table', class_='common-table')
        if table:
            tbody = table.find('tbody')
            for row in tbody.find_all('tr'):
                cols = row.find_all('td')

                if len(cols) == 5:
                    # Месяц/период
                    date = cols[0].get_text(strip=True)

                    # Данные
                    data = {
                        "Avg. Players": cols[1].get_text(strip=True),
                        "Gain": cols[2].get_text(strip=True),
                        "% Gain": cols[3].get_text(strip=True),
                        "Peak Players": cols[4].get_text(strip=True)
                    }

                    # Преобразуем строки в числа
                    for key in ["Avg. Players", "Peak Players"]:
                        val = data[key].replace(',', '')
                        data[key] = float(val) if '.' in val else int(val) if val != '-' else 0

                    # Преобразуем Gain
                    gain = data["Gain"].replace('+', '').replace(',', '')
                    gain = gain.replace('−', '-').replace('–', '-')
                    if '.' in gain and gain != '-':
                        data["Gain"] = float(gain)
                    elif gain.isdigit() or (gain.startswith('-') and gain[1:].isdigit()):
                        data["Gain"] = int(gain)
                    else:
                        data["Gain"] = 0

                    # Преобразуем % Gain
                    percent = data["% Gain"].replace('+', '').replace('%', '')
                    percent = percent.replace('−', '-').replace('–', '-')
                    if percent and percent != '-':
                        data["% Gain"] = float(percent)
                    else:
                        data["% Gain"] = 0.0

                    result["months"][date] = data

        return result

    def add_page(self, app_id: int, html_content: str, metadata: Dict = None) -> bool:
        """
        Добавляет страницу в текущий пакет

        Args:
            app_id: ID приложения Steam
            html_content: HTML содержимое
            metadata: Дополнительные метаданные

        Returns:
            True если успешно добавлено, False если нужен новый файл
        """
        # Проверяем лимит
        if self._should_create_new_file():
            print(f"⚠️  Достигнут лимит {self.max_pages} страниц в файле")
            return False

        # Парсим страницу:
        game_info = self.parse_steam_chart_simple(html_content)
        # Добавляем страницу
        self.current_data["games"][str(app_id)] = game_info
        self.current_data["total_games"] += 1

        # # Добавляем метаданные если есть
        # if metadata:
        #     if "metadata" not in self.current_data:
        #         self.current_data["metadata"] = []
        #
        #     page_meta = {
        #         "app_id": app_id,
        #         "added_at": datetime.now().isoformat(),
        #         "html_size": len(html_content),
        #         **metadata
        #     }
        #     self.current_data["metadata"].append(page_meta)

        # Автосохранение каждые 10 страниц
        if self.current_data["total_games"] % 10 == 0:
            print(f"💾 Автосохранение после {self.current_data['total_games']} страниц...")
            self.save_to_file()

        return True

    def scrape_and_save(self, app_id: int) -> bool:
        """
        Полный цикл: скачать страницу и сохранить в пакет

        Returns:
            True если успешно, False если ошибка
        """
        url = f"https://steamcharts.com/app/{app_id}"
        print(f"\n🔄 Обрабатываем app_id {app_id}")

        # Проверяем, не скачивали ли уже
        if str(app_id) in self.current_data.get("games", {}):
            print(f"⚠️  app_id {app_id} уже есть в файле, пропускаем")
            return True

        # Скачиваем
        html = self.make_request(url)

        if not html:
            print(f"❌ Не удалось скачать app_id {app_id}")
            return False

        # Подготавливаем метаданные
        metadata = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "content_length": len(html)
        }

        # Пытаемся добавить
        added = self.add_page(app_id, html, metadata)

        if not added:
            # Достигнут лимит - нужно создать новый файл
            print(f"📦 Создаем новый файл для app_id {app_id}")

            # Сохраняем старый файл
            self.save_to_file()

            # Создаем новый
            new_filename = self._create_new_filename()
            old_file = self.batch_file

            # Переносим данные в новый объект
            self.batch_file = new_filename
            self.current_data = {
                "total_games": 0,
                "created_at": datetime.now().isoformat(),
                "last_updated": None,
                "games": {},
                "metadata": [],
                "previous_file": old_file
            }

            # Добавляем текущую страницу в новый файл
            self.add_page(app_id, html, metadata)

            print(f"📁 Создан новый файл: {new_filename}")

        print(f"✅ app_id {app_id} добавлен (всего: {self.current_data['total_games']})")
        return True

    def batch_scrape(self, app_ids, pause_between=1):
        """
        Пакетный сбор списка app_id

        Args:
            app_ids: Список ID для сбора
            pause_between: Пауза между запросами
        """
        print(f"🚀 Начинаем пакетный сбор {len(app_ids)} app_id")
        print(f"   Файл: {self.batch_file}")
        print(f"   Макс. страниц в файле: {self.max_pages}")
        print("-" * 50)

        success_count = 0
        fail_count = 0

        for i, app_id in enumerate(app_ids, 1):
            print(f"\n[{i}/{len(app_ids)}] ", end="")

            if self.scrape_and_save(app_id):
                success_count += 1
            else:
                fail_count += 1

            # # Пауза между запросами (кроме последнего)
            # if i < len(app_ids):
            #     pass
            #     # pause = random.uniform(pause_between, pause_between + 1)
            #     # print(f"⏸️  Пауза {pause:.1f} сек...")
            #     # time.sleep(pause)

        # Финальное сохранение
        print(f"\n💾 Финальное сохранение...")
        self.save_to_file()

        # Статистика
        print(f"\n{'=' * 50}")
        print(f"📊 СБОР БАЧА ЗАВЕРШЕН")
        print(f"   ✅ Успешно: {success_count}")
        print(f"   ❌ Ошибок: {fail_count}")
        print(f"   📁 Текущий файл: {self.batch_file}")
        print(f"   📄 Всего страниц: {self.current_data['total_games']}")

        return success_count, fail_count

    def get_file_info(self):
        """Выводит информацию о текущем файле"""
        print(f"\n📊 ИНФОРМАЦИЯ О ФАЙЛЕ {self.batch_file}")
        print(f"   Страниц: {self.current_data.get('total_games', 0)}")
        print(f"   Создан: {self.current_data.get('created_at', 'N/A')}")
        print(f"   Обновлен: {self.current_data.get('last_updated', 'N/A')}")

        # Список сохраненных app_id
        saved_ids = list(self.current_data.get("games", {}).keys())
        if saved_ids:
            print(f"   Сохраненные app_id: {', '.join(saved_ids[:10])}", end="")
            if len(saved_ids) > 10:
                print(f" ... и еще {len(saved_ids) - 10}")
            else:
                print()

        # Размер файла
        if os.path.exists(self.batch_file):
            size_mb = os.path.getsize(self.batch_file) / 1024 / 1024
            print(f"   Размер файла: {size_mb:.2f} MB")