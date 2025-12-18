import json
from pathlib import Path
from typing import Dict, Any, List

TASK_NAMES = {
    1: "clustering",
  2: "analyze_dynamic",
  3: "regression",
  4: "location_distribution",
  5: "graph_friend"
              }

# ==========================================
# 1. ГЕНЕРАТОРЫ КОНТЕНТА (Твой код)
# ==========================================

def gen_create_strategy(subject) -> Dict[str, Any]:
    return {
        "command": "create_strategy",
        "subject": subject,
        "path_to_data": "/data/new_games.json"
    }


def gen_update_strategy(subject) -> Dict[str, Any]:
    return {
        "command": "update_strategy",
        "subject": subject,
        "path_to_data": "/data/update_pack.json"
    }


def gen_collect_data(subject, stage) -> Dict[str, Any]:
    return {
        "command": "collect_data",
        "subject": subject,
        "stage": stage,
        "processor_name": "FastCollector",
        "amount_of_butch": 10,
        "steam_api_key": "",
        "path_to_save": ""
    }


def gen_collect_data_peeks() -> Dict[str, Any]:
    return {
        "command": "collect_data_peeks",
        "path_to_save": ""
    }


def gen_fill_analys_db(subject, stage) -> Dict[str, Any]:
    return {
        "command": "fill_analys_db",
        "subject": subject,
        "stage": stage,
        "path_to_load": ""
    }


def gen_fill_analys_db_peeks() -> Dict[str, Any]:
    return {
        "command": "fill_analys_db_peeks",
        "path_to_load": ""
    }


def gen_google_load(task_number, graph) -> Dict[str, Any]:
    return {
        "command": "google_load",
        "task": task_number,
        "graph": graph,
        "spreadsheet_url": "",
        "credentials_path": ""
    }


def gen_visualize(task_number, graphs) -> Dict[str, Any]:
    return {
        "command": "visualize",
        "task": task_number,
        "graph": graphs,
        "path_to_save": "",
        "path_to_data": ""
    }


def gen_calculate_template(task_ids: int, graphs) -> Dict[str, Any]:
    return {
        "command": "calculate",
        "task": task_ids,
        "graph": graphs,
        "path_to_save": ""
    }


# ==========================================
# 2. ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ СОХРАНЕНИЯ
# ==========================================

def save_json(full_path: Path, data: Dict[str, Any]):
    """Создает папки по пути и сохраняет JSON."""
    try:
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  [OK] {full_path.name}")
    except Exception as e:
        print(f"  [ERR] Не удалось создать {full_path}: {e}")


# ==========================================
# 3. ОРКЕСТРАТОРЫ (СЛОЖНЫЕ ШАБЛОНЫ)
# ==========================================

def process_create_strategy(base_dir: Path):
    """Генерирует варианты для create_strategy (Game/Player)."""
    folder = base_dir / "create_strategy"
    print(f"\n--- Генерация: {folder.name} ---")

    for subject in ["Game", "Player"]:
        filename = f"create_strategy_{subject}.json"
        data = gen_create_strategy(subject)
        save_json(folder / filename, data)


def process_update_strategy(base_dir: Path):
    """Генерирует варианты для update_strategy (Game/Player)."""
    folder = base_dir / "update_strategy"
    print(f"\n--- Генерация: {folder.name} ---")

    for subject in ["Game", "Player"]:
        filename = f"update_strategy_{subject}.json"
        data = gen_update_strategy(subject)
        save_json(folder / filename, data)


def process_collect_data(base_dir: Path):
    """Генерирует варианты для collect_data (Game/Player x Stage 0/1)."""
    folder = base_dir / "collect_data"
    print(f"\n--- Генерация: {folder.name} ---")

    for subject in ["Game", "Player"]:
        for stage in [0, 1]:
            filename = f"collect_{subject}_stage{stage}.json"
            data = gen_collect_data(subject, stage)
            save_json(folder / filename, data)

    # Отдельно для peeks (синглтон)
    folder_peeks = base_dir / "collect_data_peeks"
    save_json(folder_peeks / "collect_peeks.json", gen_collect_data_peeks())


def process_fill_analys_db(base_dir: Path):
    """Генерирует варианты для fill_analys_db."""
    folder = base_dir / "fill_analys_db"
    print(f"\n--- Генерация: {folder.name} ---")

    for subject in ["Game", "Player"]:
        for stage in [0, 1]:
            filename = f"fill_db_{subject}_stage{stage}.json"
            data = gen_fill_analys_db(subject, stage)
            save_json(folder / filename, data)

    # Отдельно для peeks
    folder_peeks = base_dir / "fill_analys_db_peeks"
    save_json(folder_peeks / "fill_db_peeks.json", gen_fill_analys_db_peeks())


def process_calculate(base_dir: Path):
    """
    Сложная структура для calculate.
    Создает подпапки task_1 ... task_5.
    """
    root_folder = base_dir / "calculate"
    print(f"\n--- Генерация: {root_folder.name} ---")

    # Генерируем 5 разных задач
    for i in range(1, 6):

        filename = f"calculate_task_{TASK_NAMES[i]}.json"
        # Для примера: graph='all' для всех, кроме task 3 (там конкретные графики)
        graphs = "all"
        data = gen_calculate_template(task_ids=i, graphs=graphs)
        save_json(root_folder / filename, data)



def process_visualize(base_dir: Path):
    """Варианты для visualize по таскам."""
    folder = base_dir / "visualize"
    print(f"\n--- Генерация: {folder.name} ---")

    for i in range(1, 4):  # Примеры для первых 3 тасок
        filename = f"visualize_task_{TASK_NAMES[i]}.json"
        data = gen_visualize(task_number=i, graphs="all")
        save_json(folder / filename, data)


def process_google_load(base_dir: Path):
    """Варианты для google_load."""
    folder = base_dir / "google_load"
    print(f"\n--- Генерация: {folder.name} ---")

    for i in range(4, 6):  # Примеры для первых 3 тасок
        filename = f"google_load_{TASK_NAMES[i]}.json"
        data = gen_google_load(task_number=i, graph="all")
        save_json(folder / filename, data)



# ==========================================
# 4. ГЛАВНАЯ ТОЧКА ВХОДА
# ==========================================

def create_example_configs():
    """Запускает генерацию всех шаблонов."""
    base_dir = Path("config_examples")
    print(f"=== Начало генерации конфигов в: {base_dir.absolute()} ===")

    process_create_strategy(base_dir)
    process_update_strategy(base_dir)
    process_collect_data(base_dir)
    process_fill_analys_db(base_dir)
    process_calculate(base_dir)  # Самая сложная структура
    process_visualize(base_dir)
    process_google_load(base_dir)

    print("\n=== [SUCCESS] Все примеры созданы! ===")