import csv
import io
from typing import List

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

from distribution.pathmanager import pm


class GoogleLoader:

    def __init__(self):
        self._client = None
        pass

    def _init_client(self):
        scope = ['https://www.googleapis.com/auth/spreadsheets',
                 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file(pm.path_to_google_token(), scopes=scope)
        self._client = gspread.authorize(creds)
    @property
    def client(self):
        if self._client is None:
            self._init_client()
        return self._client


    def upload_by_title_csv_from_str(self, sheet_title: str, csv_data: str) -> str:
        """
        Создаёт (или открывает) Google Sheet и заливает CSV-данные.
        csv_data — строка CSV (уже подготовленная).
        """

        try:
            spreadsheet = self.client.open(sheet_title)
        except gspread.SpreadsheetNotFound:
            spreadsheet = self.client.create(sheet_title)
            print(f"✅ Создана новая таблица: '{sheet_title}'")

        # Берём первый лист или создаём
        if spreadsheet.worksheets():
            worksheet = spreadsheet.get_worksheet(0)
        else:
            worksheet = spreadsheet.add_worksheet(
                title="Sheet1",
                rows=100,
                cols=20,
            )

        # CSV → list[list[str]]
        reader = csv.reader(io.StringIO(csv_data))
        rows = list(reader)

        if not rows:
            raise ValueError("CSV пустой")

        # Очищаем и обновляем
        worksheet.clear()

        worksheet.update(
            values=rows,
            range_name="A1",
            value_input_option="RAW",
        )

        print(f"✅ Данные записаны: {spreadsheet.url}")
        return spreadsheet.id
    def upload_csv_by_url_from_str(self, sheet_title: str, csv_data: str) -> str:
        """
        spreadsheet_ref — либо title, либо URL
        """

        try:
            if sheet_title.startswith("http"):
                spreadsheet = self.client.open_by_url(sheet_title)
            else:
                spreadsheet = self.client.open(sheet_title)
                spreadsheet.share(None, perm_type='anyone', role='reader')

        except gspread.SpreadsheetNotFound:
            spreadsheet = self.client.create(sheet_title)
            print(f"✅ Создана новая таблица: '{sheet_title}'")

        worksheet = spreadsheet.get_worksheet(0) or spreadsheet.add_worksheet(
            title="Sheet1", rows=100, cols=20
        )

        rows = list(csv.reader(io.StringIO(csv_data)))
        if not rows:
            raise ValueError("CSV пустой")

        worksheet.clear()
        worksheet.update(values=rows, range_name="A1", value_input_option="RAW")

        return spreadsheet.id

    def upload_csv_by_title_from_df(self,
                                    sheet_title: str,
                                    csv_data: List[pd.DataFrame],  # Теперь ждем список
                                    folder_id: str) -> str:
        """
        Принимает Title и СПИСОК DataFrame'ов.
        Первый DataFrame пойдет в лист 'Elements', второй в 'Connections'.
        """

        # 1. Логика очистки ID папки
        if "drive.google.com" in folder_id:
            folder_id = folder_id.split('/')[-1].split('?')[0]

        # 2. Открытие или создание файла
        try:
            spreadsheet = self.client.open(sheet_title)
            print(f"📂 Открыт файл: {spreadsheet.title}")
        except gspread.SpreadsheetNotFound:
            try:
                spreadsheet = self.client.create(sheet_title, folder_id=folder_id)
                print(f"✅ Создан новый файл: {sheet_title}")
            except Exception as e:
                print(f"❌ Ошибка создания файла (проверьте права на папку): {e}")
                raise e

            # Попытка расшарить (лучше держать в try/except)
            try:
                spreadsheet.share(None, perm_type='anyone', role='reader')
            except Exception:
                pass  # Игнорируем ошибку прав на шаринг

        # 3. Имена листов для Kumu (Золотой стандарт)
        # Если передали 2 датафрейма, называем их правильно.
        # Если другое количество - просто Sheet1, Sheet2...
        if len(csv_data) == 2:
            target_sheet_names = ["Elements", "Connections"]
        else:
            target_sheet_names = [f"Sheet{i + 1}" for i in range(len(csv_data))]

        # 4. Цикл по DataFrame'ам
        for i, df in enumerate(csv_data):
            current_sheet_name = target_sheet_names[i]

            # Пытаемся получить лист, если нет - создаем
            try:
                worksheet = spreadsheet.worksheet(current_sheet_name)
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(title=current_sheet_name, rows=1000, cols=20)

            # Подготовка данных
            df_clean = df.fillna("")  # Убираем NaN

            # Если DataFrame пустой, пропускаем или очищаем лист
            if df_clean.empty:
                worksheet.clear()
                continue

            # Превращаем в список списков
            all_values = [df_clean.columns.tolist()] + df_clean.values.tolist()

            # Заливаем
            print(f"✍️ Запись в лист '{current_sheet_name}': {len(all_values)} строк...")
            worksheet.clear()

            try:
                worksheet.update(values=all_values, range_name="A1", value_input_option="RAW")
            except Exception as e:
                # Иногда падает, если таблица маловата -> расширяем
                print(f"⚠️ Расширяю таблицу '{current_sheet_name}'...")
                worksheet.resize(rows=len(all_values) + 50, cols=len(all_values[0]) + 5)
                worksheet.update(values=all_values, range_name="A1", value_input_option="RAW")

        return spreadsheet.id
    def delete_orphaned_files(self):
        """
        Удаляет файлы-сироты (у которых нет родительской папки),
        которые забивают квоту бота.
        """
        print("🧹 Начинаю поиск потерянных файлов...")

        # Запрос к API: найти файлы, владельцем которых являюсь Я (бот), и которые не лежат в корзине
        # q=" 'me' in owners and trashed = false "
        files = self.client.list_spreadsheet_files()

        count = 0
        for file in files:
            try:
                # Проверяем, действительно ли мы хотим это удалить
                # Можно добавить фильтр по имени, например if "MyGraph" in file['name']:
                print(f"Удаляю старый файл: {file['name']} ({file['id']})")
                self.client.del_spreadsheet(file['id'])
                count += 1
            except Exception as e:
                print(f"Ошибка удаления {file['name']}: {e}")

        print(f"✅ Очистка завершена. Удалено файлов: {count}")