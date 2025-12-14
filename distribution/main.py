import json
import argparse
import sys

from pydantic import ValidationError

from distribution.utils.cli_commands import create_arg_parser
from distribution.utils.command_manager import get_result
from distribution.utils.create_sample_config import create_example_configs
from distribution.utils.parse_config import parse_config_file

COMMANDS = [
    "create_strategy", "update_strategy", "collect_data",
    "fill_analys_db", "calculate", "google_load", "visualize",
    "fill_peaks"
]


def get_current_command(args: argparse.Namespace) -> str:
    """Определяет, какая команда была выбрана."""
    for cmd in COMMANDS:
        if getattr(args, cmd, False):
            return cmd

    raise ValueError("Не определена команда")


def main():
    """Основная функция парсера командной строки."""
    parser = create_arg_parser()
    args = parser.parse_args()

    try:
        # Определяем команду
        command = get_current_command(args)

        if args.verbose:
            print(f"[INFO] Команда: {command}")
            print(f"[INFO] Конфиг файл: {args.config}")
            if args.dry_run:
                print("[INFO] Режим dry_run - только проверка конфига")

        # Парсим конфигурационный файл
        config_obj = parse_config_file(args.config, command)

        if args.verbose:
            print("[INFO] Конфигурация успешно загружена и валидирована:")
            print(json.dumps(config_obj.dict(), indent=2, ensure_ascii=False))

        # Если dry_run - выходим
        if args.dry_run:
            print("[SUCCESS] Конфигурация валидна. Dry run завершен.")
            return 0

        info = get_result(config_obj)

        # Здесь должна быть логика выполнения команд
        # Например:
        # if command == "create_strategy":
        #     run_create_strategy(final_config)
        # elif command == "update_strategy":
        #     run_update_strategy(final_config)
        # ... и т.д.

        print(f"[SUCCESS] Команда '{command}' готова к выполнению с конфигом:")
        print(f"  Subject: {getattr(config_obj, 'subject', 'N/A')}")
        print(f"  Tasks: {getattr(config_obj, 'task', 'N/A')}")
        print(f"  Graphs: {getattr(config_obj, 'graph', 'N/A')}")

        return 0

    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1
    except ValidationError as e:
        print(f"[ERROR] Ошибка валидации конфига:", file=sys.stderr)
        print(e.json(), file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"[ERROR] Неожиданная ошибка: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 4


# !/usr/bin/env python3
"""
Парсер командной строки и JSON-конфигов для аналитической системы.
Использование:
    python cli_parser.py --create_strategy --config config.json
    python cli_parser.py --update_strategy --config config.json -g
    python cli_parser.py --collect_data --config config.json
    python cli_parser.py --fill_analys_db --config config.json
    python cli_parser.py --calculate --config config.json
    python cli_parser.py --google_load --config config.json
    python cli_parser.py --visualize --config config.json
"""

if __name__ == "__main__":
    # Для быстрого тестирования можно создать примеры конфигов:
    create_example_configs()

    # Запуск парсера
    # sys.exit(main())
