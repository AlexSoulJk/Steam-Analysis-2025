from typing import Optional, List, Dict, Tuple

from sqlalchemy import select
from sqlalchemy.orm import joinedload, Session

from steam_analysis.core.schemas.analysis.user import UserAnalysisCreate, UserAnalysisUpdate, UserAnalysisFromJson
from ..base.baseanalisis import BaseAnalysisRepository
from ...models.serviceplayermodels import UserDataAnalysis


class UserAnalysisRepository(BaseAnalysisRepository[UserDataAnalysis, UserAnalysisCreate, UserAnalysisUpdate]):
    """Репозиторий для работы с юзерами"""

    def __init__(self):
        super().__init__(model=UserDataAnalysis)

    def create_bulk(self, objects_in: List[UserAnalysisCreate],
                    session: Session,
                    no_commit=False) -> List[UserDataAnalysis]:

        app_ids = [obj.app_id for obj in objects_in]
        exists_flags = self.exists_bulk(session, "app_id", app_ids)
        creating_objects = [obj for obj, exists in zip(objects_in, exists_flags) if not exists]
        return super().create_bulk(creating_objects, session, no_commit)

    # def create_bulk_from_json(self, objects_in: List[UserAnalysisFromJson],
    #                           session: Session,
    #                           no_commit=False) -> List[UserDataAnalysis]:
    #     """Создание пользователей из JSON схем"""
    #     create_objects = []
    #     for obj in objects_in:
    #         create_obj = UserAnalysisCreate(
    #             steam_id=obj.steam_id,
    #             name=obj.name,
    #             created_at=obj.created_at,
    #             chunk_id=None
    #         )
    #         create_objects.append(create_obj)
    #
    #     return self.create_bulk(create_objects, session, no_commit)

    def create_bulk_from_json(self, objects_in: List[UserAnalysisFromJson],
                              session: Session,
                              no_commit=False) -> List[UserDataAnalysis]:
        """Создание пользователей из JSON схем"""
        # Получаем steam_id из входящих данных
        steam_ids = [obj.steam_id for obj in objects_in]

        # Проверяем существующих пользователей
        existing_users = self.get_existing_by_steam_ids(steam_ids, session)
        existing_steam_ids = set(existing_users.keys())

        # Фильтруем только новых пользователей
        new_users = [obj for obj in objects_in if obj.steam_id not in existing_steam_ids]

        if not new_users:
            return []  # возвращаем пустой список, если все пользователи уже существуют

        # Создаем только новых пользователей
        db_objects = []
        for obj in new_users:
            db_obj = UserDataAnalysis(
                steam_id=obj.steam_id,
                name=obj.name,
                created_at=obj.created_at,
                chunk_id=None,  # создаем без чанка
                status='pending'  # добавляем статус по умолчанию
            )
            db_objects.append(db_obj)

        session.add_all(db_objects)

        if not no_commit:
            session.commit()
            for db_obj in db_objects:
                session.refresh(db_obj)
        else:
            session.flush()

        return db_objects

    def get_by_steam_id(self, steam_id: int, session: Session) -> Optional[UserDataAnalysis]:
        return self.get_by_field("steam_id",
                                 steam_id,
                                 session=session)

    def get_existing_by_steam_ids(self, steam_ids: List[int], session: Session) -> Dict[int, UserDataAnalysis]:
        """
        Получить существующие игры по списку app_ids одним запросом
        Возвращает словарь {steam_id: user_object}
        """
        if not steam_ids:
            return {}

        query = select(self.model).where(self.model.steam_id.in_(steam_ids))
        result = session.execute(query)
        existing_users = result.scalars().all()

        return {user.steam_id: user for user in existing_users}

    def get_last_uploaded_user(self, session: Session) -> Optional[UserDataAnalysis]:
        return session.query(UserDataAnalysis). \
            order_by(UserDataAnalysis.steam_id.desc()). \
            first()

    def mark_list_as_in_progress(self, users_to_mark: List[UserDataAnalysis], session: Session):

        for user in users_to_mark:
            user.status = "in_progress"

        session.flush(users_to_mark)

        return users_to_mark

    def get_users_by_chunk_id(self, chunk_id: int, session: Session) -> List[UserDataAnalysis]:
        """Получить пользователей по chunk_id"""
        return session.query(self.model).filter(self.model.chunk_id == chunk_id).all()
