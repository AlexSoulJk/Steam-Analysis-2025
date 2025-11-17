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
    def __init__(self,
                 chunk_size: int = 25,
                 butch_chunck_size: int = 10):
        self.chunk_size = chunk_size
        self.butch_chunck_size = butch_chunck_size
        self.user_list_size = 250

    def _split_for_game_chunck(self, game_list: List[UserAnalysisFromJson]) -> List[List[UserAnalysisFromJson]]:
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

    def get_user_analysis_data_for_create_from_resource(self,
                                                        last_steam_id: Optional[int],
                                                        user_resource: UserList) -> List[UserAnalysisFromJson]:
        # MayBe NeedToRefactor
        last_steam_id = user_resource.get_first_steam_id() if last_steam_id is None else last_steam_id
        start_creation = datetime.datetime.now()

        user_list = list(map(lambda x: UserAnalysisFromJson.from_json_resource(x, start_creation),
                             user_resource.get_user_list_for_analysis_creation(str(last_steam_id),
                                                                               self.user_list_size)))
        if len(user_list) != self.user_list_size:
            print(
                f"Need to fill user list current {len(user_list)}. Need add {self.user_list_size}")
            return []

        return user_list
