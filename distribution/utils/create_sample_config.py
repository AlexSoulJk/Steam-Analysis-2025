# ========== ПРИМЕРЫ КОНФИГУРАЦИОННЫХ ФАЙЛОВ ==========
import json
from pathlib import Path


def create_example_configs():
    """Создает примеры конфигурационных файлов для тестирования."""
    examples_dir = Path("config_examples")
    examples_dir.mkdir(exist_ok=True)

    # Пример 1: create_strategy
    create_config = {
        "command": "create_strategy",
        "subject": "Game",
        "path_to_data": "/data/new_games.json"
    }

    # Пример 2: collect_data
    collect_config = {
        "command": "collect_data",
        "subject": "Player",
        "stage": 0,
        "steam_api_key": "asafdsfsdfaaf",
        "processor_name": "FastCollector",
        "path_to_save": "/output/players_stage0"
    }

    # Пример 3: calculate
    calculate_config = {
        "command": "calculate",
        "task": [1, 2, 3],
        "graph": "all",
        "path_to_save": "/output/calculations"
    }

    # Пример 4: visualize
    visualize_config = {
        "command": "visualize",
        "task": "all",
        "graph": [0, 1, 2],
        "path_to_save": "/output/charts",
        "path_to_data": "/data/for_viz"
    }

    # Сохраняем примеры
    configs = {
        "create_strategy.json": create_config,
        "collect_data.json": collect_config,
        "calculate.json": calculate_config,
        "visualize.json": visualize_config
    }

    for filename, config in configs.items():
        path = examples_dir / filename
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"Создан пример конфига: {path}")