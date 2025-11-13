from typing import List, Optional

from sqlalchemy.orm import Session

from steam_analysis.core.schemas.analysis.user import UserAnalysisChunkCreate, UserAnalysisFromJson, UserAnalysisCreate, \
    UserAnalysisChunkForRequest
from steam_analysis.database.models.serviceplayermodels import AnalysisUserChunk, UserDataAnalysis
from steam_analysis.database.repositories.analysis.userchunk import UserChunkRepository
from steam_analysis.database.repositories.analysis.userdata import UserAnalysisRepository


class UserPreparer:

    def __init__(self):
        self.user_model_repo = UserAnalysisRepository()
        self.chunk_repo = UserChunkRepository()

    def _prepare_user_list_for_create(self, created_chunks: List[AnalysisUserChunk],
                                      users: List[List[UserAnalysisFromJson]]) -> List[UserAnalysisCreate]:
        res = []
        for created_chunk, user_in_chunk in zip(created_chunks, users):
            res.extend(list(map(lambda x: UserAnalysisCreate.from_json_model(json_data=x,
                                                                             chunk_id=created_chunk.id),
                                user_in_chunk)))
        return res

    def create_chuncks(self, chuncks: List[UserAnalysisChunkCreate],
                       users: List[List[UserAnalysisFromJson]], session: Session):

        if len(chuncks) != len(users):
            raise Exception("Amount of chunks for create doesn't match with with amount fo users splited by chuncks")

        chunk_without_users = self.chunk_repo.create_bulk(objects_in=chuncks,
                                                          session=session)

        prepared_users = self._prepare_user_list_for_create(chunk_without_users,
                                                            users)

        self.user_model_repo.create_bulk(objects_in=prepared_users,
                                         session=session)
        session.commit()

        pass

    def create_users(self, users: List[UserAnalysisFromJson], session: Session):
        # Тут не оч пока работает. Нужно подумать над тем как будешь передавать схемку на создание пользователя.
        # Возможно стоит написать отдельный балковый метод под CreateFromJson
        user_created = self.user_model_repo.create_bulk(objects_in=users,
                                                        session=session)

        # Добавить бесхозных пользователей, у которых еще нет своих чанков

        # Creating Chunk

        chunk_without_users = self.chunk_repo.create_bulk(objects_in=chuncks,
                                                          session=session)

        prepared_users = self._prepare_user_list_for_create(chunk_without_users,
                                                            users)

    def get_last_uploaded_user(self, session: Session) -> Optional[UserDataAnalysis]:
        return self.user_model_repo.get_last_uploaded_user(session)

    def mark_user_chunk_complete(self, chunk: UserAnalysisChunkForRequest, session):
        self.chunk_repo.update_by_id(chunk.chunk.id, obj_in=chunk.chunk,
                                     session=session, no_commit=True)
        for user in chunk.chunk_users:
            self.user_model_repo.update_by_id(user.id, obj_in=user,
                                              session=session, no_commit=True)
        session.commit()
        pass
