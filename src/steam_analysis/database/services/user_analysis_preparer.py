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
        # Chunk Creator(chunk_size, strategy_processor)

    def _prepare_user_list_for_create(self, created_chunks: List[AnalysisUserChunk],
                                      users: List[UserAnalysisFromJson]) -> List[UserAnalysisCreate]:
        res = []
        for created_chunk in created_chunks:
            # Туть фильтр для пользователей
            chunk_user_ids = created_chunk.user_ids or []
            chunk_users = [user for user in users if user.id in chunk_user_ids]

            res.extend(list(map(lambda x: UserAnalysisCreate.from_json_model(json_data=x,
                                                                             chunk_id=created_chunk.id),
                                chunk_users)))
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

        user_created = self.user_model_repo.create_bulk_from_json(objects_in=users, session=session)
        # ADD WITHOUT CHUNK
        chunk_data = UserAnalysisChunkCreate(
            processed_by=None,
            user_ids=[user.id for user in user_created]
        )
        # users_for_new_chunk = get_emty_users
        # ChunkCreator ().create_chunk(users_for_new_chunk: ?Schema/Model) -> Chunk Created(model/schemas)

        chunk_created = self.chunk_repo.create_bulk(objects_in=[chunk_data], session=session)

        if not chunk_created:
            raise Exception("Failed to create chunk")

        for user in user_created:
            user.chunk_id = chunk_created[0].id
            session.merge(user)

        session.commit()

        return {
            "chunk": chunk_created[0],
            "users": user_created,
            "users_count": len(user_created)
        }


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
