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

        app_ids = [obj.steam_id for obj in objects_in]
        exists_flags = self.exists_bulk(session, "steam_id", app_ids)
        creating_objects = [obj for obj, exists in zip(objects_in, exists_flags) if not exists]
        return super().create_bulk(creating_objects, session, no_commit)

    def create_bulk_from_json(self, objects_in: List[UserAnalysisFromJson],
                              session: Session,
                              no_commit=False) -> List[UserDataAnalysis]:
        """Создание пользователей из JSON схем"""
        create_objects = []
        for obj in objects_in:
            create_obj = UserAnalysisCreate(
                steam_id=obj.steam_id,
                name=obj.name,
                created_at=obj.created_at,
                chunk_id=0 # Кажется что это не оч правильно лучше писать Null и сделать optional
            )
            create_objects.append(create_obj)

        return self.create_bulk(create_objects, session, no_commit)

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
        existing_games = result.scalars().all()

        return {game.app_id: game for game in existing_games}

    def get_last_uploaded_user(self, session: Session) -> Optional[UserDataAnalysis]:
        return session.query(UserDataAnalysis). \
            order_by(UserDataAnalysis.steam_id.desc()). \
            first()

    def mark_list_as_in_progress(self, users_to_mark: List[UserDataAnalysis], session: Session):

        for user in users_to_mark:
            user.status = "in_progress"

        session.flush(users_to_mark)

        return users_to_mark
