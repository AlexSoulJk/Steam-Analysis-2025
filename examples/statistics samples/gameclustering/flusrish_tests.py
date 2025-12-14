import csv
import gspread
from steam_analysis.app.processed_data_provider import ProcessedDataProvider
import pandas as pd

# --- КОНФИГУРАЦИЯ ---
CREDENTIALS_FILE = r'C:\Users\Hp\PycharmProjects\Steam-Analysis-2025\prismatic-iris-481012-m0-cfd925bcc88f.json'
SHEET_NAME = 'Games By Types'


def save_games_by_types_to_csv(data, filename: str = "flourish_games_by_types.csv"):
    """Сохраняет данные локально в CSV (как и было)."""
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Game Type', 'Count'])  # Заголовки
        writer.writerows(data)  # Данные
    print(f"📁 Данные сохранены локально в {filename}")
    return filename


def save_games_by_types_to_gsheet(data):
    """Отправляет данные в Google Sheets."""
    print(f"☁️ Начинаем загрузку в Google Таблицу '{SHEET_NAME}'...")

    try:
        # 1. Аутентификация
        gc = gspread.service_account(filename=CREDENTIALS_FILE)

        # 2. Открытие таблицы
        try:
            sh = gc.open(SHEET_NAME)
        except gspread.SpreadsheetNotFound:
            print(f"❌ Ошибка: Таблица с именем '{SHEET_NAME}' не найдена. Создайте её или проверьте доступ.")
            return

        # Берем первый лист
        worksheet = sh.get_worksheet(0)

        # 3. Подготовка данных
        # Добавляем заголовки к данным (так же, как в CSV)
        headers = ['Game Type', 'Count']

        # Превращаем данные в список списков (если они вдруг кортежи)
        # И объединяем заголовки с данными
        # Если data - это список кортежей/списков, то:
        final_data = [headers] + [list(row) for row in data]

        # 4. Очистка и Обновление
        worksheet.clear()  # Стираем старые данные
        worksheet.update(final_data)  # Заливаем новые

        print(f"✅ Успешно! Данные обновлены в облаке: {sh.url}")

    except Exception as e:
        print(f"❌ Произошла ошибка при работе с Google Sheets: {e}")


def draw_games_by_types():
    # Получаем данные
    pdp = ProcessedDataProvider()
    data = pdp.get_games_by_types_for_flurish()

    # 1. Сохраняем в CSV (как резервная копия)
    save_games_by_types_to_csv(data)

    # 2. Отправляем в Google Sheets
    save_games_by_types_to_gsheet(data)


if __name__ == "__main__":
    draw_games_by_types()