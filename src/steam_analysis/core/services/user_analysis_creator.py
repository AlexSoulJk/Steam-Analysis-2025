import datetime
from typing import List, Tuple, Optional

from steam_analysis.core.schemas.analysis.user import UserAnalysisChunkCreate, UserAnalysisFromJson
from steam_analysis.resourcemanager.manager import ResourceManager
from steam_analysis.resourcemanager.resources.codes import ResourceCodes
from steam_analysis.resourcemanager.resources.game_list import GameList

PROCESSOR_NAME = ["AlexSoulJK",
                  "baru1ina",
                  "Ekaterina Lips",
                  "Lo-Lap"]


class UserAnalysisCreator:

    @staticmethod
    def default_name_strategy(chunk_number: int):
        return PROCESSOR_NAME[chunk_number % 4]

    def __init__(self,
                 chunk_size: int = 25,
                 butch_chunck_size: int = 10):
        self.resource_manager = ResourceManager()
        self.chunk_size = chunk_size
        self.butch_chunck_size = butch_chunck_size

    def _split_for_user_chunck(self, game_list: List[UserAnalysisFromJson]) -> List[List[UserAnalysisFromJson]]:
        res = []
        start_idx = 0
        for i in range(self.butch_chunck_size):
            res.append(game_list[start_idx + i * self.chunk_size:start_idx + self.chunk_size * (i + 1)])
        return res

    def _prepare_chunck_for_create(self, processor_name_strategy) -> List[UserAnalysisChunkCreate]:
        res = []
        for i in range(self.butch_chunck_size):
            res.append(UserAnalysisChunkCreate(processed_by=processor_name_strategy(i)))
        return res

    def get_game_analysis_data_for_create_from_resource(self, last_steam_id: Optional[int],
                                                        processor_name_strategy=default_name_strategy) -> Tuple[
        List[UserAnalysisChunkCreate],
        List[List[UserAnalysisFromJson]]]:
        resource: GameList = self.resource_manager.get_resource(ResourceCodes.GAME_LIST)
        last_steam_id = resource.get_first_app_id() if last_steam_id is None else last_steam_id
        start_creation = datetime.datetime.now()
        created_chuncks = self._prepare_chunck_for_create(processor_name_strategy)
        game_list = list(map(lambda x: UserAnalysisFromJson.from_json_resource(x, start_creation),
                             resource.get_app_list(last_steam_id,
                                                   self.chunk_size * self.butch_chunck_size)))
        game_res = self._split_for_user_chunck(game_list)
        return (created_chuncks, game_res)
