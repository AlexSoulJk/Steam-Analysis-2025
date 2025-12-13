from pathlib import Path


DEFAULT_PATH_TO_STRATEGY = Path("/strategy")
DEFAULT_PATH_TO_DATA_JSONS = Path("/data_jsons")
DEFAULT_PATH_TO_PEAK = Path("/peaks")
DEFAULT_PATH_TO_PEAK_DATA_JSONS = DEFAULT_PATH_TO_PEAK / Path("peak_pages")

# folder name
DEFAULT_FOLDER_GAMES = "games"
DEFAULT_FOLDER_ADD_INFO_GAMES = "add_info_games"
DEFAULT_FOLDR_USERS = "users"
DEFAULT_FOLDER_USERS_GAMES = "users_games"

# file for saving and reading
DEFAULT_FILE_APP_IDS = DEFAULT_PATH_TO_PEAK / "steam_app_ids.json"
DEFAULT_FILE_BATCHES_APP_IDS = DEFAULT_PATH_TO_PEAK / "batches_app_ids.json"

# filename
DEFAULT_FILENAME_GAMES = "games"
DEFAULT_FILENAME_ADD_INFO_GAMES = "add_info_games"
DEFAULT_FILENAME_USERS = "users"
DEFAULT_FILENAME_USERS_GAMES = "users_games"


class PathManager:
    def __init__(self):
        self.path_to_stategy: Path = DEFAULT_PATH_TO_STRATEGY
        self._path_to_data: Path = DEFAULT_PATH_TO_DATA_JSONS

        self._folder_to_games: str = DEFAULT_FOLDER_GAMES
        self._folder_to_games_add_info: str = DEFAULT_FOLDER_ADD_INFO_GAMES
        self._folder_to_users: str = DEFAULT_FOLDR_USERS
        self._folder_to_users_games: str = DEFAULT_FOLDER_USERS_GAMES

        self._path_to_peak_pages: Path = DEFAULT_PATH_TO_PEAK_DATA_JSONS
        self._path_to_peak_folder: Path = DEFAULT_PATH_TO_PEAK
        self._file_peak_app_ids: Path = DEFAULT_FILE_APP_IDS
        # self._file_peak_batches_app_ids: Path = DEFAULT_FILE_BATCHES_APP_IDS

    @property
    def path_to_data(self):
        self.check_exist_folder(self._path_to_data)
        return self._path_to_data

    @property
    def folder_to_games(self):
        # self.check_exist_folder(self._folder_to_games)
        return self._folder_to_games

    @property
    def folder_to_save_add_info(self):
        # self.check_exist_folder(self._folder_to_games_add_info)
        return self._folder_to_games_add_info

    @property
    def folder_to_users(self):
        # self.check_exist_folder(self._folder_to_users)
        return self._folder_to_users

    @property
    def folder_to_users_games(self):
        # self.check_exist_folder(self._folder_to_users_games)
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
        self.check_exist_folder(self._file_peak_app_ids)
        return self._file_peak_app_ids

    # @property
    # def file_peak_batches_app_ids(self):
    #     self.check_exist_folder(self._file_peak_batches_app_ids)
    #     return self._file_peak_batches_app_ids

    def check_exist_folder(self, path: Path):
        pass


pm = PathManager()
