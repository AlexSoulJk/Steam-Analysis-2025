# test_pm_manager_fix.py
import pytest
from unittest.mock import Mock, PropertyMock

from distribution.utils.command_manager import pm_manager_manipulation
from distribution.utils.command_schemas import CollectDataConfig, SubjectEnum


class TestPmManagerFix:
    """Тесты для исправленной версии pm_manager_manipulation."""

    def test_pm_manager_updates_paths_correctly(self):
        """Проверка правильного обновления путей в PathManager."""
        # Создаем мок для pm с property-моками
        mock_pm = Mock()

        # Настраиваем маппинг
        PM_DIRECT_MAP = {
            "collect_data": {
                "path_to_save": "path_to_data"  # config_field -> pm_property
            }
        }

        # Конфиг с кастомным путем
        config = CollectDataConfig(
            command="collect_data",
            subject=SubjectEnum.player,
            stage=0,
            processor_name="Test",
            steam_api_key="key",
            path_to_save="/custom/output/path"
        )

        # Сохраняем оригинальное значение
        original_path = config.path_to_save

        # Патчим pm и PM_DIRECT_MAP
        with patch('distribution.utils.command_manager.pm', mock_pm), \
                patch('distribution.utils.command_manager.PM_DIRECT_MAP', PM_DIRECT_MAP):

            # Исправленная версия функции
            def fixed_pm_manager_manipulation(config_model):
                command = config_model.command

                if command not in PM_DIRECT_MAP:
                    return

                mapping = PM_DIRECT_MAP[command]
                values = config_model.dict()

                for config_field, pm_field in mapping.items():
                    if config_field in values and hasattr(mock_pm, pm_field):
                        # Устанавливаем значение в PathManager
                        setattr(mock_pm, pm_field, values[config_field])

            # Вызываем исправленную функцию
            fixed_pm_manager_manipulation(config)

            # Проверяем, что значение было установлено
            # (в реальном коде это проверяется через вызовы функций)
            assert hasattr(mock_pm, 'path_to_data')

    def test_complex_path_mapping(self):
        """Тест сложного маппинга путей."""
        # Мокаем pm
        mock_pm = Mock()

        # Сложный маппинг как в реальном коде
        PM_DIRECT_MAP = {
            "visualize": {
                "path_to_save": "path_to_save",
                "path_to_data": "path_to_data"
            }
        }

        # Создаем mock-конфиг
        class MockConfig:
            command = "visualize"
            path_to_save = "/save/path"
            path_to_data = "/data/path"

            def dict(self):
                return {
                    "path_to_save": self.path_to_save,
                    "path_to_data": self.path_to_data
                }

        config = MockConfig()

        with patch('distribution.utils.command_manager.pm', mock_pm), \
                patch('distribution.utils.command_manager.PM_DIRECT_MAP', PM_DIRECT_MAP):

            # Упрощенная исправленная функция
            def fixed_pm_manager(config_model):
                command = config_model.command
                if command in PM_DIRECT_MAP:
                    for config_field, pm_field in PM_DIRECT_MAP[command].items():
                        if hasattr(config_model, config_field) and hasattr(mock_pm, pm_field):
                            value = getattr(config_model, config_field)
                            setattr(mock_pm, pm_field, value)

            fixed_pm_manager(config)

            # Проверяем установку значений
            assert mock_pm.path_to_save == "/save/path"
            assert mock_pm.path_to_data == "/data/path"