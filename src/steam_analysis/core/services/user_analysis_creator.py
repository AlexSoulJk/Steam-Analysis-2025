import datetime
from typing import List, Tuple, Optional

from steam_analysis.core.schemas.analysis.user import UserAnalysisChunkCreate, UserAnalysisFromJson
from steam_analysis.resourcemanager.manager import ResourceManager
from steam_analysis.resourcemanager.resources.codes import ResourceCodes
from steam_analysis.resourcemanager.resources.user_list import UserList

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

    def _split_for_user_chunck(self, user_list: List[UserAnalysisFromJson]) -> List[List[UserAnalysisFromJson]]:
        res = []
        start_idx = 0
        for i in range(self.butch_chunck_size):
            res.append(user_list[start_idx + i * self.chunk_size:start_idx + self.chunk_size * (i + 1)])
        return res

    def _prepare_chunck_for_create(self, processor_name_strategy) -> List[UserAnalysisChunkCreate]:
        res = []
        for i in range(self.butch_chunck_size):
            res.append(UserAnalysisChunkCreate(processed_by=processor_name_strategy(i)))
        return res

    def get_user_analysis_data_for_create_from_resource(self, last_steam_id: Optional[int],
                                                        processor_name_strategy=default_name_strategy) -> Tuple[
        List[UserAnalysisChunkCreate],
        List[List[UserAnalysisFromJson]]]:

        resource: UserList = self.resource_manager.get_resource(ResourceCodes.USER_LIST) # aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        last_steam_id = resource.get_first_steam_id() if last_steam_id is None else last_steam_id
        start_creation = datetime.datetime.now()

        user_list = list(map(lambda x: UserAnalysisFromJson.from_json_resource(x, start_creation),
                             resource.get_user_list_for_analysis_creation(last_steam_id,
                                                                          self.chunk_size * self.butch_chunck_size)))
        if len(user_list) != self.chunk_size * self.butch_chunck_size:
            print(f"Need to fill user list current {len(user_list)}. Need add {self.chunk_size * self.butch_chunck_size}")
            return (None, None)

        created_chuncks = self._prepare_chunck_for_create(processor_name_strategy)
        user_res = self._split_for_user_chunck(user_list)
        return (created_chuncks, user_res)
