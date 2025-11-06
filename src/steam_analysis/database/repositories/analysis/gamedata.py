from typing import Optional, List, Dict, Tuple

from sqlalchemy import select
from sqlalchemy.orm import joinedload, Session

from steam_analysis.core.schemas.analysis.game import GameAnalysisCreate, GameAnalysisUpdate
from ..base.baseanalisis import BaseAnalysisRepository
from ...models.servicemodels import GameDataAnalysis


class GameAnalysisRepository(BaseAnalysisRepository[GameDataAnalysis, GameAnalysisCreate, GameAnalysisUpdate]):
    """Репозиторий для работы с играми"""

    def __init__(self):
        super().__init__(model=GameDataAnalysis)

    def get_by_app_id(self, app_id: int, session: Session) -> Optional[GameDataAnalysis]:
        return self.get_by_field("app_id",
                                 app_id,
                                 session=session)

    def get_existing_by_app_ids(self, app_ids: List[int], session: Session) -> Dict[int, GameDataAnalysis]:
        """
        Получить существующие игры по списку app_ids одним запросом
        Возвращает словарь {app_id: game_object}
        """
        if not app_ids:
            return {}

        query = select(self.model).where(self.model.app_id.in_(app_ids))
        result = session.execute(query)
        existing_games = result.scalars().all()

        return {game.app_id: game for game in existing_games}

    def get_last_uploaded_game(self, session: Session) -> Optional[GameDataAnalysis]:
        return session.query(GameDataAnalysis). \
            order_by(GameDataAnalysis.app_id.desc()). \
            first()

    def mark_list_as_in_progress(self, games_to_mark: List[GameDataAnalysis], session: Session):

        for game in games_to_mark:
            game.status = "in_progress"

        session.flush(games_to_mark)

        return games_to_mark