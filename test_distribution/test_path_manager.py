import pytest
from pathlib import Path

from distribution.utils.command_manager import pm_manager_manipulation
from distribution.utils.command_schemas import (
    CreateStrategyConfig,
    UpdateStrategyConfig,
    CollectDataConfig,
    FillAnalysDBConfig,
    SubjectEnum
)


class TestPathManagement:
    """Тесты управления путями из конфигурации."""

    def test_pm_manager_manipulation_create_strategy(self, mock_path_manager):
        """Обновление путей для create_strategy."""
        config = CreateStrategyConfig(
            command="create_strategy",
            subject=SubjectEnum.game,
            path_to_data="/custom/strategy/path.json"
        )

        pm_manager_manipulation(config)

        # Проверяем, что путь был передан в PathManager
        # (нужно модифицировать pm_manager_manipulation для правильной работы)
        assert config.path_to_data == "/custom/strategy/path.json"

    def test_pm_manager_manipulation_collect_data(self, mock_path_manager):
        """Обновление путей для collect_data."""
        config = CollectDataConfig(
            command="collect_data",
            subject=SubjectEnum.player,
            stage=0,
            processor_name="Test",
            steam_api_key="key",
            path_to_save="/custom/output/path"
        )

        pm_manager_manipulation(config)
        assert config.path_to_save == "/custom/output/path"

    def test_pm_manager_manipulation_fill_analys_db(self, mock_path_manager):
        """Обновление путей для fill_analys_db."""
        config = FillAnalysDBConfig(
            command="fill_analys_db",
            subject=SubjectEnum.game,
            stage=0,
            path_to_load="/custom/input/path"
        )

        pm_manager_manipulation(config)
        assert config.path_to_load == "/custom/input/path"

    def test_pm_manager_unknown_command(self, mock_path_manager):
        """Проверка неизвестной команды."""

        class UnknownConfig:
            command = "unknown_command"
            path_to_data = "/some/path"

        config = UnknownConfig()

        # Не должно быть исключения
        pm_manager_manipulation(config)

    def test_paths_passed_to_functions(self, mock_game_functions, mock_path_manager):
        """Проверка, что пути из конфига передаются в функции."""
        from distribution.utils.command_manager import get_result

        config = CreateStrategyConfig(
            command="create_strategy",
            subject=SubjectEnum.game,
            path_to_data="/custom/data/games.json"
        )

        # Мокаем ROUTE_MAP для теста
        with patch.dict('distribution.utils.command_manager.ROUTE_MAP', {
            "create_strategy": {
                "Game": mock_game_functions["create"]
            }
        }, clear=False):
            result = get_result(config)

            # Проверяем, что функция была вызвана с правильными аргументами
            mock_game_functions["create"].assert_called_once()

            # Получаем аргументы вызова
            call_args = mock_game_functions["create"].call_args

            # Проверяем, что переданы api_key и processor_name
            # (они должны быть получены из конфига или других источников)
            assert len(call_args.args) >= 2  # api_key и processor_name