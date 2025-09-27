# Steam Analysis Toolkit (For Developers)

Минимальная библиотека для работы с Steam API. Чтобы посмотреть примеры данных.

## Быстрый старт

1. Установите зависимости:
```bash
pip install -e .
```

2. Получите STEAM_API_KEY по ссылке:
    https://steamcommunity.com/dev/apikey

3. Создайте в корне проекта файл .env в котором нужно указать:
```env
    STEAM_API_KEY=your_steam_api_key_here
```

4. Запустите:
```bash
python examples/steamapi/basic_usage.py
```