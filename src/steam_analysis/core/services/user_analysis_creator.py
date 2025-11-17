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
    def __init__(self):
        self.user_list_size = 250

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
