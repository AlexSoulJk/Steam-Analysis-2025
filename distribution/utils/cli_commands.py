import argparse

import argparse


def create_arg_parser() -> argparse.ArgumentParser:
    """Создает парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Аналитическая система: обработка игроков и игр",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s --create_strategy "configs/strategy.json"
  %(prog)s --update_strategy "configs/update.json"
  %(prog)s --create_configs
        """
    )

    # Группа для взаимно исключающихся команд

    # --- КОМАНДЫ, ТРЕБУЮЩИЕ ПУТЬ К КОНФИГУ (type=str) ---
    # nargs='?' означает:
    # 1. Если пути нет (--cmd), вернет значение из const (например, "config.json" по дефолту)
    # 2. Если путь есть (--cmd path), вернет path
    # Если ты хочешь ОБЯЗАТЬ вводить путь, убери nargs и const.

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

    action_group.add_argument(
        "--create_configs",
        action="store_true",
        help="Создание шаблонных конфигов"

    )

    parser.add_argument(
        "--config",
        type=str,
        help="Путь к конфигу (deprecated)",
        default=None
    )

    return parser
