# test_fill_update_methods.py
import pytest

from distribution.utils.command_manager import get_result
from distribution.utils.command_schemas import (
    CreateStrategyConfig,
    UpdateStrategyConfig,
    FillAnalysDBConfig,
    SubjectEnum
)


class TestFillUpdateMethods:
    """Тесты методов fill и update."""

    def test_create_strategy_game(self, mock_game_functions, mock_path_manager):
        """Тест create_strategy для игр."""
        config = CreateStrategyConfig(
            command="create_strategy",
            subject=SubjectEnum.game,
            path_to_data="/test/games.json"
        )

        # Временно заменяем ROUTE_MAP для теста
        with patch.dict('distribution.utils.command_manager.ROUTE_MAP', {
            "create_strategy": {
                "Game": mock_game_functions["create"]
            }
        }, clear=False):
            result = get_result(config)

            # Проверяем вызов правильной функции
            mock_game_functions["create"].assert_called_once()
            assert result == "games_create_strategy_called"

            # Проверяем аргументы вызова
            call_args = mock_game_functions["create"].call_args
            assert len(call_args.args) == 2  # api_key и processor_name

    def test_update_strategy_player(self, mock_user_functions, mock_path_manager):
        """Тест update_strategy для игроков."""
        config = UpdateStrategyConfig(
            command="update_strategy",
            subject=SubjectEnum.player,
            path_to_data="/test/update_players.json"
        )

        with patch.dict('distribution.utils.command_manager.ROUTE_MAP', {
            "update_strategy": {
                "Player": mock_user_functions["update"]
            }
        }, clear=False):
            result = get_result(config)

            mock_user_functions["update"].assert_called_once()
            assert result == "user_update_strategy_called"

    def test_fill_analys_db_game_stage0(self, mock_game_functions, mock_path_manager):
        """Тест fill_analys_db для игр, stage 0."""
        config = FillAnalysDBConfig(
            command="fill_analys_db",
            subject=SubjectEnum.game,
            stage=0,
            path_to_load="/test/input"
        )

        with patch.dict('distribution.utils.command_manager.ROUTE_MAP', {
            "fill_analys_db": {
                "Game": {
                    0: mock_game_functions["fill"]
                }
            }
        }, clear=False):
            result = get_result(config)

            mock_game_functions["fill"].assert_called_once()
            assert result == "games_fill_database_called"

    def test_fill_analys_db_player_stage1(self, mock_user_functions, mock_path_manager):
        """Тест fill_analys_db для игроков, stage 1."""
        config = FillAnalysDBConfig(
            command="fill_analys_db",
            subject=SubjectEnum.player,
            stage=1,
            path_to_load="/test/input"
        )

        with patch.dict('distribution.utils.command_manager.ROUTE_MAP', {
            "fill_analys_db": {
                "Player": {
                    0: Mock(),  # Stage 0
                    1: mock_user_functions["fill"]  # Stage 1
                }
            }
        }, clear=False):
            result = get_result(config)

            mock_user_functions["fill"].assert_called_once()
            assert result == "user_fill_database_called"

    def test_collect_data_player_stage0(self, mock_user_functions, mock_path_manager):
        """Тест collect_data для игроков, stage 0."""
        from distribution.utils.command_schemas import CollectDataConfig

        config = CollectDataConfig(
            command="collect_data",
            subject=SubjectEnum.player,
            stage=0,
            processor_name="TestProcessor",
            steam_api_key="test_key",
            path_to_save="/test/output"
        )

        with patch.dict('distribution.utils.command_manager.ROUTE_MAP', {
            "collect_data": {
                "Player": {
                    0: mock_user_functions["collect"]
                }
            }
        }, clear=False):
            result = get_result(config)

            mock_user_functions["collect"].assert_called_once()
            assert result == "user_collect_data_called"

            # Проверяем передачу аргументов
            call_args = mock_user_functions["collect"].call_args
            assert call_args.args[0] == "test_key"  # api_key
            assert call_args.args[1] == "TestProcessor"  # processor_name

    def test_invalid_stage(self, mock_path_manager):
        """Тест невалидного stage."""
        from distribution.utils.command_schemas import CollectDataConfig

        config = CollectDataConfig(
            command="collect_data",
            subject=SubjectEnum.player,
            stage=99,  # Невалидный stage
            processor_name="Test"
        )

        # Мокаем только необходимую часть ROUTE_MAP
        with patch.dict('distribution.utils.command_manager.ROUTE_MAP', {
            "collect_data": {
                "Player": {
                    0: Mock(),
                    1: Mock()
                }
            }
        }, clear=False):
            # Stage 99 не существует в ROUTE_MAP
            with pytest.raises(KeyError):
                get_result(config)

    def test_missing_subject_in_route(self, mock_path_manager):
        """Тест отсутствующего subject в ROUTE_MAP."""
        config = CreateStrategyConfig(
            command="create_strategy",
            subject=SubjectEnum.game  # Но в ROUTE_MAP нет "Game"
        )

        # ROUTE_MAP без ключа "Game"
        with patch.dict('distribution.utils.command_manager.ROUTE_MAP', {
            "create_strategy": {
                "Player": Mock()  # Только Player, нет Game
            }
        }, clear=True):  # clear=True заменяет весь словарь

            with pytest.raises(KeyError):
                get_result(config)

    def test_path_overrides_from_config(self, mock_user_functions, mock_path_manager, temp_dir):
        """Проверка, что пути из конфига переопределяют значения по умолчанию."""
        from distribution.utils.command_schemas import CollectDataConfig

        custom_path = str(temp_dir / "custom_output")

        config = CollectDataConfig(
            command="collect_data",
            subject=SubjectEnum.player,
            stage=0,
            processor_name="Test",
            steam_api_key="key",
            path_to_save=custom_path  # Кастомный путь
        )

        with patch.dict('distribution.utils.command_manager.ROUTE_MAP', {
            "collect_data": {
                "Player": {
                    0: mock_user_functions["collect"]
                }
            }
        }, clear=False):
            # Мокаем pm_manager_manipulation для проверки вызова
            with patch('distribution.utils.command_manager.pm_manager_manipulation') as mock_pm_manip:
                get_result(config)

                # Проверяем, что pm_manager_manipulation был вызван с нашим конфигом
                mock_pm_manip.assert_called_once_with(config)