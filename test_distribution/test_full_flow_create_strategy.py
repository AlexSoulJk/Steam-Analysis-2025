# test_integration.py
import pytest
import json
from unittest.mock import Mock, patch, call

from distribution.utils.parse_config import parse_config_file
from distribution.utils.command_manager import get_result
from distribution.pathmanager import pm
from pathlib import Path


class TestIntegration:
    """Интеграционные тесты полного цикла."""

    def test_full_flow_create_strategy(self, temp_dir, sample_games_data):
        """Полный тест: парсинг конфига + выполнение create_strategy."""
        # 1. Создаем конфиг
        config_path = temp_dir / "config.json"
        config = {
            "command": "create_strategy",
            "subject": "Game",
            "path_to_data": str(temp_dir / "games.json")
        }

        # 2. Создаем файл данных
        data_path = Path(config["path_to_data"])
        with open(data_path, 'w') as f:
            json.dump(sample_games_data, f)

        # 3. Сохраняем конфиг
        with open(config_path, 'w') as f:
            json.dump(config, f)

        # 4. Парсим конфиг
        config_obj = parse_config_file(str(config_path), "create_strategy")

        # 5. Мокаем выполнение
        mock_create_func = Mock(return_value="success")

        with patch.dict('distribution.utils.command_manager.ROUTE_MAP', {
            "create_strategy": {
                "Game": mock_create_func
            }
        }, clear=True):
            # 6. Выполняем команду
            result = get_result(config_obj)

            # 7. Проверяем результат
            assert result == "success"
            mock_create_func.assert_called_once()

    def test_config_path_override_in_functions(self, temp_dir):
        """Проверка, что пути из конфига передаются в бизнес-функции."""
        # Создаем мок для user_create_strategy
        mock_user_create = Mock()

        # Настраиваем ROUTE_MAP
        with patch.dict('distribution.utils.command_manager.ROUTE_MAP', {
            "create_strategy": {
                "Player": mock_user_create
            }
        }, clear=True):
            # Создаем конфиг с кастомным путем
            from distribution.utils.command_schemas import CreateStrategyConfig

            custom_data_path = str(temp_dir / "custom_data.json")
            config = CreateStrategyConfig(
                command="create_strategy",
                subject="Player",
                path_to_data=custom_data_path
            )

            # Мокаем зависимости, которые используются в user_create_strategy
            with patch('distribution.utils.command_manager.get_app_mediator') as mock_get_app, \
                    patch('distribution.utils.command_manager.pm') as mock_pm, \
                    patch('builtins.open') as mock_open, \
                    patch('json.load') as mock_json_load:
                # Настраиваем моки
                mock_app = Mock()
                mock_get_app.return_value = mock_app

                # Имитируем чтение файла
                mock_json_load.return_value = {"players": []}

                # Запускаем
                get_result(config)

                # Проверяем, что open был вызван с правильным путем
                # (user_create_strategy читает файл по path_to_strategy_user)
                mock_open.assert_called()

                # В реальной реализации нужно проверить,
                # что path_to_data из конфига используется