import argparse


def create_arg_parser() -> argparse.ArgumentParser:
    """Создает парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Аналитическая система: обработка игроков и игр",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s --create_strategy --config strategy_config.json
  %(prog)s --update_strategy --config update_config.json -g
  %(prog)s --collect_data --config collect_config.json
  %(prog)s --calculate --config calc_config.json --task 1 2 3
  %(prog)s --visualize --config viz_config.json --path_save ./output
        """
    )

    # Группа для взаимно исключающихся команд (основные действия)
    action_group = parser.add_mutually_exclusive_group(required=True)

    action_group.add_argument(
        "--create_strategy",
        action="store_true",
        help="Создание новой стратегии (сущности со статусом pending)"
    )

    action_group.add_argument(
        "--update_strategy",
        action="store_true",
        help="Обновление существующей стратегии"
    )

    action_group.add_argument(
        "--collect_data",
        action="store_true",
        help="Сбор данных для сущностей со статусом pending/partial"
    )

    action_group.add_argument(
        "--collect_data_peeks",
        action="store_true",
        help="Сбор данных пиков пользователей с сайта SteamCharts"
    )

    action_group.add_argument(
        "--fill_analys_db_peeks",
        action="store_true",
        help="Загрузка пиков пользователей из JSON"
    )

    action_group.add_argument(
        "--fill_analys_db",
        action="store_true",
        help="Добавление данных в аналитическую БД"
    )

    action_group.add_argument(
        "--calculate",
        action="store_true",
        help="Решение аналитической задачи"
    )

    action_group.add_argument(
        "--google_load",
        action="store_true",
        help="Выгрузка данных в Google Таблицы"
    )

    action_group.add_argument(
        "--visualize",
        action="store_true",
        help="Визуализация графиков"
    )

    # # Общие аргументы
    # parser.add_argument(
    #     "--config",
    #     "-c",
    #     type=str,
    #     required=True,
    #     help="Путь к JSON-файлу с конфигурацией"
    # )

    # parser.add_argument(
    #     "--force_update",
    #     "-g",
    #     action="store_true",
    #     help="Флаг принудительного обновления (для update_strategy)"
    # )

    # # Аргументы, которые могут переопределять конфиг (опционально)
    # parser.add_argument(
    #     "--task",
    #     type=int,
    #     nargs="+",
    #     help="Номера задач (переопределяет конфиг для calculate/google_load/visualize)"
    # )
    #
    # parser.add_argument(
    #     "--graph",
    #     type=int,
    #     nargs="+",
    #     help="Номера графиков (переопределяет конфиг для calculate/google_load/visualize)"
    # )
    #
    # parser.add_argument(
    #     "--path_save",
    #     type=str,
    #     help="Путь для сохранения (переопределяет конфиг)"
    # )
    #
    # parser.add_argument(
    #     "--path_data",
    #     type=str,
    #     help="Путь к данным (переопределяет конфиг)"
    # )
    #
    # parser.add_argument(
    #     "--verbose",
    #     "-v",
    #     action="store_true",
    #     help="Подробный вывод"
    # )

    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Проверить конфиг без выполнения действий"
    )

    return parser