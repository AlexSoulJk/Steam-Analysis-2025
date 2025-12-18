import json
import argparse
import os
import sys

from pydantic import ValidationError

# Получаем путь к папке, где лежит этот скрипт (main.py) внутри EXE
if getattr(sys, 'frozen', False):
    # Внутри EXE это будет путь вида .../_MEIPASS/distribution
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Добавляем эту папку в sys.path
    # Теперь Python будет видеть 'utils', 'data_jsons' и всё, что лежит рядом с main.py
    sys.path.insert(0, current_dir)

    # Если нужно видеть модули из корня (например src), добавляем и родителя
    parent_dir = os.path.dirname(current_dir)  # .../_MEIPASS
    sys.path.insert(0, parent_dir)

from distribution.utils.cli_commands import create_arg_parser
from distribution.utils.command_manager import get_result
from distribution.utils.create_sample_config import create_example_configs
from distribution.utils.parse_config import parse_config_file

COMMANDS = [
    "create_strategy", "update_strategy", "collect_data",
    "fill_analys_db", "calculate", "google_load", "visualize",
    "fill_peaks", "create_configs", "config"
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

        # Парсим конфигурационный файл
        if command != "create_configs":
            config_obj = parse_config_file(args.config, command)
            print("[INFO] Конфигурация успешно загружена")
            print(json.dumps(config_obj.model_dump(), indent=2, ensure_ascii=False))

            info = get_result(config_obj)
        else:
            create_example_configs()
            print("[SUCCESS] Конфигурационные файлы сгенерированы.")
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
    # create_example_configs()

    # Запуск парсера
    sys.exit(main())
