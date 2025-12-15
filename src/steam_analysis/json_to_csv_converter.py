import csv
import io

from steam_analysis.core.schemas.analysis.geoshemas import ListCountryGameStat, CountryGameStat


class JsonToCsvConverter:

    def __init__(self):
        pass

    def convert_geo_games(self, obj: ListCountryGameStat) -> str:
        """
        Конвертирует ListCountryGameStat в CSV строку

        Args:
            obj: объект ListCountryGameStat с данными

        Returns:
            CSV строка с данными
        """
        if not obj.data:
            return ""

        # Создаем строковый буфер для CSV
        output = io.StringIO()

        # Определяем заголовки из полей модели
        headers = list(CountryGameStat.__annotations__.keys())

        # Создаем writer
        writer = csv.DictWriter(output, fieldnames=headers)

        # Записываем заголовки
        writer.writeheader()

        # Записываем данные
        for item in obj.data:
            writer.writerow(item.model_dump())

        # Получаем CSV строку
        csv_string = output.getvalue()
        output.close()

        return csv_string

