from typing import Optional, Dict, List, Tuple, Any

from sqlalchemy import select, and_, or_
from sqlalchemy.orm import joinedload, Session

from steam_analysis.core.schemas.game.service import SchemaCreate
from steam_analysis.database.models.timeseries import PlayerCountHistory
from steam_analysis.database.repositories.base import DictionaryRepository
from .game import GameRepository

from steam_analysis.database.repositories.base.base import ModelType, CreateSchemaType, UpdateSchemaType, \
    BaseDBRepository


class PeakRepository(DictionaryRepository[PlayerCountHistory, Any, Any]):

    def __init__(self):
        super().__init__(PlayerCountHistory)
        self.game_repos = GameRepository()

    def get_existing_pairs(self, pairs: List[Tuple[int, str]],
                           session: Session,
                           batch_size: int = 500) -> List[PlayerCountHistory]:
        """
        Получить существующие достижения по парам (game_id, name) с батчингом

        Args:
            session: Сессия SQLAlchemy
            pairs: Список кортежей (game_id, name)
            batch_size: Размер батча (если None, используется self._batch_size)

        Returns:
            Список существующих достижений
        """
        if not pairs:
            return []

        all_existing = []

        # Обрабатываем пары батчами
        for i in range(0, len(pairs), batch_size):
            batch = pairs[i:i + batch_size]

            # Создаем OR-условия для текущего батча
            conditions = []
            for game_id, date in batch:
                conditions.append(
                    and_(
                        self.model.game_id == game_id,
                        self.model.date == date
                    )
                )

            # Выполняем запрос для текущего батча
            if conditions:
                stmt = select(self.model).where(or_(*conditions))
                result = session.execute(stmt)
                batch_existing = list(result.scalars().all())
                all_existing.extend(batch_existing)

        return all_existing

    def create_bulk_from_json(self, games: Dict[str, Any], session: Session):

        app_ids = [int(app_id) for app_id in games.keys()]
        exist_games = self.game_repos.get_existing_by_app_ids(app_ids, session)

        game_ids = {str(app_id): game.id for app_id, game in exist_games.items()}

        pair_games_date = []

        for app_id in games.keys():
            game_id = game_ids.get(app_id, None)
            if game_id is None:
                continue

            table = games[app_id].get("months", {})
            if not table:
                continue

            for month in table.keys():
                pair_games_date.append((game_id, month))

        exist_tables = self.get_existing_pairs(pair_games_date, session)

        existing_pairs = {
            (peak.game_id, peak.date): peak for peak in exist_tables
        }

        all_tables = []
        for app_id in games.keys():
            if exist_games.get(int(app_id), None) is None:
                continue

            game = games[app_id]
            exist_games[int(app_id)].all_time_peak = game.get("all-time peak", 0)

            table = game.get("months", {})
            if not table:
                continue

            for month in table.keys():
                percent_gain = table[month].get("% Gain", 0.0)
                if percent_gain == "inf" or percent_gain == "-inf" or percent_gain == "nan":
                    percent_gain = float(percent_gain)

                gain = table[month].get("Gain", 0.0)
                if gain == "inf" or gain == "-inf" or gain == "nan":
                    gain = float(gain)

                pair = (game_ids[app_id], month)
                if pair in existing_pairs.keys():
                    if month == "Last 30 Days":
                        # обновляем Last
                        peak = existing_pairs.get(pair, ())
                        peak.player_count = table[month].get("Peak Players", 0)
                        peak.avg_players = table[month].get("Avg. Players", 0.0)
                        peak.percent_gain = percent_gain
                        peak.gain = gain
                else:
                    all_tables.append(
                        PlayerCountHistory(
                            game_id=game_ids[app_id],
                            player_count=table[month].get("Peak Players", 0),
                            date=month,
                            avg_players=table[month].get("Avg. Players", 0.0),
                            percent_gain=percent_gain,
                            gain=gain
                        )
                    )

        if all_tables:
            session.add_all(all_tables)

        return all_tables + exist_tables
