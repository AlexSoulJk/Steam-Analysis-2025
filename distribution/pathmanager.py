from pathlib import Path


DEFAULT_PATH_TO_STRATEGY = Path("/strategy")
DEFAULT_PATH_TO_DATA_JSONS = Path("data_jsons")
DEFAULT_PATH_TO_PEAK = DEFAULT_PATH_TO_DATA_JSONS / Path("/peaks")
DEFAULT_PATH_TO_PEAK_DATA_JSONS = DEFAULT_PATH_TO_PEAK / Path("peak_pages")
DEFAULT_PATH_TO_TASKS_DATA_JSON = DEFAULT_PATH_TO_DATA_JSONS / Path("tasks")

# folder name
DEFAULT_FOLDER_GAMES = Path("games")
DEFAULT_FOLDER_ADD_INFO_GAMES = Path("add_info_games")
DEFAULT_FOLDR_USERS = Path("users")
DEFAULT_FOLDER_USERS_GAMES = Path("users_games")

DEFAULT_FOLDER_GEO_TASKS = Path("geo")
DEFAULT_FOLDER_FRIENDS_TASKS = Path("friends")

# file for saving and reading
DEFAULT_FILE_APP_IDS = DEFAULT_PATH_TO_PEAK / "steam_app_ids.json"
DEFAULT_FILE_BATCHES_APP_IDS = DEFAULT_PATH_TO_PEAK / "batches_app_ids.json"

# file for tasks

# filename
DEFAULT_FILENAME_GAMES = "games"
DEFAULT_FILENAME_FRIENDS_BY_GAMES = "friends_by_games"
DEFAULT_FILENAME_ADD_INFO_GAMES = "add_info_games"
DEFAULT_FILENAME_USERS = "users"
DEFAULT_FILENAME_USERS_GAMES = "users_games"
DEFAULT_PATH_TO_GEO_SAVE_GAMES = "geo_games"

class PathManager:
    def __init__(self):
        self._path_to_strategy_game: Path = DEFAULT_PATH_TO_STRATEGY / "strategy_games.json"
        self._path_to_strategy_user: Path = DEFAULT_PATH_TO_STRATEGY / "strategy_users.json"

        self._path_to_strategy_update_game: Path = DEFAULT_PATH_TO_STRATEGY / "strategy_update_games.json"
        self._path_to_strategy_update_user: Path = DEFAULT_PATH_TO_STRATEGY / "strategy_update_users.json"

        self._path_to_data: Path = DEFAULT_PATH_TO_DATA_JSONS

        self._folder_to_games: Path = DEFAULT_FOLDER_GAMES
        self._folder_to_games_add_info: Path = DEFAULT_FOLDER_ADD_INFO_GAMES
        self._folder_to_users: Path = DEFAULT_FOLDR_USERS
        self._folder_to_users_games: Path = DEFAULT_FOLDER_USERS_GAMES
        self._folder_to_task_save : Path = DEFAULT_PATH_TO_TASKS_DATA_JSON

        self._path_to_peak_folder: Path = DEFAULT_PATH_TO_PEAK
        self._path_to_peak_pages: Path = DEFAULT_PATH_TO_PEAK / Path("peak_pages")
        self._file_peak_app_ids: Path = DEFAULT_PATH_TO_PEAK / "steam_app_ids.json"

        self._file_geo_games: Path = DEFAULT_PATH_TO_TASKS_DATA_JSON / DEFAULT_FOLDER_GEO_TASKS / f"{DEFAULT_FILENAME_GAMES}.json"
        self._path_to_google_token = None
        # self._file_peak_batches_app_ids: Path = DEFAULT_FILE_BATCHES_APP_IDS

    @property
    def path_to_strategy_game(self):
        self.check_exist_file(self._path_to_strategy_game)
        return self._path_to_data

    @property
    def path_to_strategy_user(self):
        self.check_exist_file(self._path_to_strategy_user)
        return self._path_to_strategy_user

    @property
    def path_to_strategy_update_game(self):
        self.check_exist_file(self._path_to_strategy_update_game)
        return self._path_to_strategy_update_game

    @property
    def path_to_strategy_update_user(self):
        self.check_exist_file(self._path_to_strategy_update_user)
        return self._path_to_strategy_update_user

    @property
    def path_to_data(self):
        self.check_exist_folder(self._path_to_data)
        return self._path_to_data


    def path_to_google_token(self):
        if self._path_to_google_token == None:
            raise Exception("Can't find token")
        return self._path_to_google_token

    @property
    def folder_to_task_save(self):
        self.check_exist_folder(self._folder_to_task_save)
        return self._folder_to_task_save

    @property
    def file_to_task_geo_games(self):
        self.check_exist_file(self._file_geo_games)
        return self._file_geo_games


    @property
    def folder_to_games(self):
        self.check_exist_folder(self._path_to_data / self._folder_to_games)
        return self._folder_to_games

    @property
    def folder_to_games_add_info(self):
        self.check_exist_folder(self._path_to_data / self._folder_to_games_add_info)
        return self._folder_to_games_add_info

    @property
    def folder_to_users(self):
        self.check_exist_folder(self._path_to_data / self._folder_to_users)
        return self._folder_to_users

    @property
    def folder_to_users_games(self):
        self.check_exist_folder(self._path_to_data / self._folder_to_users_games)
        return self._folder_to_users

    @property
    def path_to_peak_folder(self):
        self.check_exist_folder(self._path_to_peak_folder)
        return self._path_to_peak_folder

    @property
    def path_to_peak_pages(self):
        self.check_exist_folder(self._path_to_peak_pages)
        return self._path_to_peak_pages

    @property
    def file_peak_app_ids(self):
        self.check_exist_file(self._file_peak_app_ids)
        return self._file_peak_app_ids

    # @property
    # def file_peak_batches_app_ids(self):
    #     self.check_exist_folder(self._file_peak_batches_app_ids)
    #     return self._file_peak_batches_app_ids

    def check_exist_folder(self, path: Path):
        try:
            if isinstance(path, str):
                path = Path(path)

            if path.exists():
                if path.is_dir():
                    return True
                else:
                    raise Exception(f"Ошибка: {path.absolute()} существует, но это не папка")

            path.mkdir(parents=True, exist_ok=True)
            print(f"Папка успешно создана: {path.absolute()}")
            return True

        except PermissionError:
            raise Exception(f"Ошибка: Нет прав на создание папки {path}")

        except Exception as e:
            raise Exception(f"Ошибка при создании папки {path}: {e}")

    def check_exist_file(self, path: Path):
        if isinstance(path, str):
            path = Path(path)

        if not path.exists():
            raise Exception(f"Файл не найден: {path}")

        if not path.is_file():
            raise Exception(f"Путь существует, но это не файл: {path}")

        print(f"✓ Файл найден: {path}")
        return True


pm = PathManager()
