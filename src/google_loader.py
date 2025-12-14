import csv
import io

import gspread
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


    def upload_csv(self, sheet_title: str, csv_data: str) -> str:
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
    def upload_csv(self, sheet_title: str, csv_data: str) -> str:
        """
        spreadsheet_ref — либо title, либо URL
        """

        try:
            if sheet_title.startswith("http"):
                spreadsheet = self.client.open_by_url(sheet_title)
            else:
                spreadsheet = self.client.open(sheet_title)

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