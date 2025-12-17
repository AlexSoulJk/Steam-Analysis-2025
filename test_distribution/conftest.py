import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import sys

from distribution.utils.command_schemas import (
    CreateStrategyConfig,
    UpdateStrategyConfig,
    CollectDataConfig,
    FillAnalysDBConfig,
    SubjectEnum
)
from distribution.utils.parse_config import parse_config_file
from distribution.utils.command_manager import get_result, pm_manager_manipulation
from distribution.pathmanager import pm


@pytest.fixture
def temp_dir():
    """Создает временную директорию для тестовых файлов."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_games_data():
    """Пример данных игр для стратегии."""
    return {
        "games": [
            {"app_id": 730, "name": "Counter-Strike: Global Offensive"},
            {"app_id": 570, "name": "Dota 2"},
            {"app_id": 578080, "name": "PUBG"}
        ]
    }


@pytest.fixture
def sample_players_data():
    """Пример данных игроков для стратегии."""
    return {
        "players": [
            {"steam_id": "76561197960435530", "name": "Player1"},
            {"steam_id": "76561197960435531", "name": "Player2"}
        ]
    }


@pytest.fixture
def config_file_create_strategy_game(temp_dir, sample_games_data):
    """Создает тестовый конфиг для create_strategy с играми."""
    config_path = temp_dir / "create_strategy_game.json"
    config = {
        "command": "create_strategy",
        "subject": "Game",
        "path_to_data": str(temp_dir / "new_games.json")
    }

    # Создаем файл с данными
    data_path = Path(config["path_to_data"])
    with open(data_path, 'w') as f:
        json.dump(sample_games_data, f)

    with open(config_path, 'w') as f:
        json.dump(config, f)

    return config_path


@pytest.fixture
def config_file_update_strategy_player(temp_dir, sample_players_data):
    """Создает тестовый конфиг для update_strategy с игроками."""
    config_path = temp_dir / "update_strategy_player.json"
    config = {
        "command": "update_strategy",
        "subject": "Player",
        "path_to_data": str(temp_dir / "update_players.json")
    }

    # Создаем файл с данными для обновления
    data_path = Path(config["path_to_data"])
    with open(data_path, 'w') as f:
        json.dump(sample_players_data, f)

    with open(config_path, 'w') as f:
        json.dump(config, f)

    return config_path


@pytest.fixture
def config_file_collect_data(temp_dir):
    """Создает тестовый конфиг для collect_data."""
    config_path = temp_dir / "collect_data.json"
    config = {
        "command": "collect_data",
        "subject": "Player",
        "stage": 0,
        "processor_name": "TestProcessor",
        "steam_api_key": "test_api_key_12345",
        "path_to_save": str(temp_dir / "output")
    }

    with open(config_path, 'w') as f:
        json.dump(config, f)

    return config_path


@pytest.fixture
def config_file_fill_analys_db(temp_dir):
    """Создает тестовый конфиг для fill_analys_db."""
    config_path = temp_dir / "fill_analys_db.json"
    config = {
        "command": "fill_analys_db",
        "subject": "Game",
        "stage": 0,
        "path_to_load": str(temp_dir / "input_data")
    }

    # Создаем тестовую директорию с данными
    data_dir = Path(config["path_to_load"])
    data_dir.mkdir(parents=True, exist_ok=True)

    # Создаем тестовый файл данных
    test_data = {"test": "data"}
    with open(data_dir / "test_game.json", 'w') as f:
        json.dump(test_data, f)

    with open(config_path, 'w') as f:
        json.dump(config, f)

    return config_path


@pytest.fixture
def mock_path_manager():
    """Мок для PathManager."""
    with patch('distribution.utils.command_manager.pm') as mock_pm:
        mock_pm.path_to_strategy = Mock(return_value=Path("/mock/strategy"))
        mock_pm.path_to_data = Mock(return_value=Path("/mock/data"))
        mock_pm.path_to_peak_pages = Mock(return_value=Path("/mock/peaks"))
        mock_pm.credentials_path = Mock(return_value=Path("/mock/credentials.json"))
        mock_pm.path_to_save = Mock(return_value=Path("/mock/save"))
        yield mock_pm


@pytest.fixture
def mock_game_functions():
    """Мок функций для работы с играми."""
    with patch('distribution.utils.command_manager.create_games_for_strategy') as mock_create, \
            patch('distribution.utils.command_manager.games_update_strategy') as mock_update, \
            patch('distribution.utils.command_manager.games_create_games_json') as mock_collect, \
            patch('distribution.utils.command_manager.games_create_fill_database') as mock_fill:
        mock_create.return_value = "games_create_strategy_called"
        mock_update.return_value = "games_update_strategy_called"
        mock_collect.return_value = "games_collect_data_called"
        mock_fill.return_value = "games_fill_database_called"

        yield {
            "create": mock_create,
            "update": mock_update,
            "collect": mock_collect,
            "fill": mock_fill
        }


@pytest.fixture
def mock_user_functions():
    """Мок функций для работы с игроками."""
    with patch('distribution.utils.command_manager.user_create_strategy') as mock_create, \
            patch('distribution.utils.command_manager.user_update_strategy') as mock_update, \
            patch('distribution.utils.command_manager.user_create_to_json') as mock_collect, \
            patch('distribution.utils.command_manager.user_create_fill_database') as mock_fill:
        mock_create.return_value = "user_create_strategy_called"
        mock_update.return_value = "user_update_strategy_called"
        mock_collect.return_value = "user_collect_data_called"
        mock_fill.return_value = "user_fill_database_called"

        yield {
            "create": mock_create,
            "update": mock_update,
            "collect": mock_collect,
            "fill": mock_fill
        }