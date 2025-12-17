import pytest
import json
from pathlib import Path
from pydantic import ValidationError

from distribution.utils.parse_config import parse_config_file
from distribution.utils.command_schemas import (
    CreateStrategyConfig,
    UpdateStrategyConfig,
    CollectDataConfig,
    FillAnalysDBConfig,
    SubjectEnum
)


class TestParseConfig:
    """Тесты для парсинга конфигурационных файлов."""

    def test_parse_create_strategy_game(self, config_file_create_strategy_game, temp_dir):
        """Парсинг конфига create_strategy для игр."""
        config = parse_config_file(str(config_file_create_strategy_game), "create_strategy")

        assert isinstance(config, CreateStrategyConfig)
        assert config.command == "create_strategy"
        assert config.subject == SubjectEnum.game
        assert config.path_to_data == str(temp_dir / "new_games.json")
        assert config.path_to_data != ""  # Проверяем, что путь установлен

    def test_parse_update_strategy_player(self, config_file_update_strategy_player, temp_dir):
        """Парсинг конфига update_strategy для игроков."""
        config = parse_config_file(str(config_file_update_strategy_player), "update_strategy")

        assert isinstance(config, UpdateStrategyConfig)
        assert config.command == "update_strategy"
        assert config.subject == SubjectEnum.player
        assert config.path_to_data == str(temp_dir / "update_players.json")

    def test_parse_collect_data(self, config_file_collect_data, temp_dir):
        """Парсинг конфига collect_data."""
        config = parse_config_file(str(config_file_collect_data), "collect_data")

        assert isinstance(config, CollectDataConfig)
        assert config.command == "collect_data"
        assert config.subject == SubjectEnum.player
        assert config.stage == 0
        assert config.processor_name == "TestProcessor"
        assert config.steam_api_key == "test_api_key_12345"
        assert config.path_to_save == str(temp_dir / "output")

    def test_parse_fill_analys_db(self, config_file_fill_analys_db, temp_dir):
        """Парсинг конфига fill_analys_db."""
        config = parse_config_file(str(config_file_fill_analys_db), "fill_analys_db")

        assert isinstance(config, FillAnalysDBConfig)
        assert config.command == "fill_analys_db"
        assert config.subject == SubjectEnum.game
        assert config.stage == 0
        assert config.path_to_load == str(temp_dir / "input_data")

    def test_missing_config_file(self):
        """Ошибка при отсутствии файла конфига."""
        with pytest.raises(FileNotFoundError) as exc_info:
            parse_config_file("/nonexistent/path/config.json", "create_strategy")
        assert "не найден" in str(exc_info.value)

    def test_invalid_json(self, temp_dir):
        """Ошибка при невалидном JSON."""
        config_path = temp_dir / "invalid.json"
        with open(config_path, 'w') as f:
            f.write("{ invalid json }")

        with pytest.raises(ValidationError) as exc_info:
            parse_config_file(str(config_path), "create_strategy")

    def test_command_mismatch(self, temp_dir):
        """Ошибка при несовпадении команд."""
        config_path = temp_dir / "mismatch.json"
        config = {
            "command": "create_strategy",  # В конфиге create_strategy
            "subject": "Game"
        }

        with open(config_path, 'w') as f:
            json.dump(config, f)

        # Передаем другую команду
        with pytest.raises(ValueError) as exc_info:
            parse_config_file(str(config_path), "update_strategy")

        assert "не соответствует" in str(exc_info.value)

    def test_command_added_if_missing(self, temp_dir):
        """Команда добавляется, если отсутствует в конфиге."""
        config_path = temp_dir / "no_command.json"
        config = {
            "subject": "Game",
            "path_to_data": "/some/path"
        }

        with open(config_path, 'w') as f:
            json.dump(config, f)

        config_obj = parse_config_file(str(config_path), "create_strategy")
        assert config_obj.command == "create_strategy"