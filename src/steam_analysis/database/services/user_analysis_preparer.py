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

    def _get_empty_chunk_users(self, session: Session) -> List[UserDataAnalysis]:
        return self.user_model_repo.get_users_by_chunk_id(None, session)


    def _prepare_user_list_for_create(self, created_chunks: List[AnalysisUserChunk],
                                      users: List[UserAnalysisFromJson]) -> List[UserAnalysisCreate]:
        res = []
        for created_chunk in created_chunks:
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

    def create_users(self, users: List[UserAnalysisFromJson], session: Session, chunk_size: int = 25):

        user_created = self.user_model_repo.create_bulk_from_json(objects_in=users, session=session)

        empty_chunk_users = self._get_empty_chunk_users(session)

        all_users_for_chunk = list(user_created) + list(empty_chunk_users)
        print(f"Total users available for chunks: {len(all_users_for_chunk)}")

        if not all_users_for_chunk:
            # raise Exception("Users not created: No users to process - all users already exist and have chunks")
            return {
                "chunk": None,
                "users": [],
                "users_count": 0,
                "new_users_count": 0,
                "existing_users_count": 0,
                "message": "No users to process - all users already exist and have chunks"
            }

        users_for_single_chunk = all_users_for_chunk[:chunk_size]

        chunk_data = UserAnalysisChunkCreate(
            processed_by=None,
            chunk_size=chunk_size
        )

        chunk_created = self.chunk_repo.create_bulk(objects_in=[chunk_data], session=session)

        if not chunk_created:
            raise Exception("Failed to create chunk")

        print(f"Created chunk with ID: {chunk_created[0].id}")

        for user in users_for_single_chunk:
            user.chunk_id = chunk_created[0].id
            session.merge(user)

        session.commit()

        return {
            "chunk": chunk_created[0],
            "users": all_users_for_chunk,
            "users_count": len(all_users_for_chunk),
            "new_users_count": len(user_created),
            "existing_users_count": len(empty_chunk_users)
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
