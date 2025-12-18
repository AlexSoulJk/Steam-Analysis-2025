from pathlib import Path

from pydantic import ValidationError, BaseModel

from ..utils.command_schemas import CreateStrategyConfig, UpdateStrategyConfig, \
    CollectDataConfig, FillAnalysDBConfig, CalculateConfig, GoogleLoadConfig, VisualizeConfig, BaseConfigCommandSchema, \
    FillAnalysDBPeeksConfig, CollectDataPeeksConfig
import json

CONFIG_MODELS = {
    "create_strategy": CreateStrategyConfig,
    "update_strategy": UpdateStrategyConfig,
    "collect_data": CollectDataConfig,
    "fill_analys_db": FillAnalysDBConfig,
    "calculate": CalculateConfig,
    "google_load": GoogleLoadConfig,
    "visualize": VisualizeConfig,
    "fill_analys_db_peeks": FillAnalysDBPeeksConfig,
    "collect_data_peeks": CollectDataPeeksConfig,
}


def parse_config_file(config_path: str, command: str) -> BaseConfigCommandSchema:
    """
    Парсит JSON-конфиг и возвращает соответствующую Pydantic модель.

    Args:
        config_path: Путь к JSON-файлу с конфигурацией
        command: Имя команды (для проверки соответствия)

    Returns:
        Валидированный конфиг-объект

    Raises:
        FileNotFoundError: Если файл не существует
        ValidationError: Если JSON не соответствует схеме
        ValueError: Если команда в конфиге не совпадает с переданной
    """
    # Проверяем существование файла
    if not Path(config_path).exists():
        raise FileNotFoundError(f"Конфигурационный файл не найден: {config_path}")

    # Загружаем JSON
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Невалидный JSON в файле {config_path}: {e}")

    # Добавляем команду в конфиг, если её нет
    if "command" not in config_data:
        config_data["command"] = command

    # Проверяем соответствие команды
    if config_data.get("command") != command:
        raise ValueError(
            f"Команда в конфиге ({config_data.get('command')}) "
            f"не соответствует переданной команде ({command})"
        )

    # Выбираем соответствующую модель и валидируем
    model_class = CONFIG_MODELS.get(command)
    if not model_class:
        raise ValueError(f"Неизвестная команда: {command}")

    return model_class(**config_data)
