# player_relations_creator.py
from typing import List, Dict, Tuple, Optional
from sqlalchemy import and_
from sqlalchemy.orm import Session

from steam_analysis.database.models import (
    User, Game, Friend, UserPlaytime, UserGameOwnership,
    UserAchievement, Review
)
from steam_analysis.core.schemas.player.player import FriendCreate
from steam_analysis.core.schemas.player.playergame import OwnershipHttp, OwnershipCreate, \
    PlaytimeHttp, PlaytimeCreate, AchievementHttp, AchievementCreate, ReviewHttp, ReviewCreate
from steam_analysis.database.models import Achievement
from steam_analysis.core.schemas.player.service import PlayerGameDataAnalysisCreate
from steam_analysis.database.support_models.player_creation import PreparedForPlayerCreation
from steam_analysis.database.repositories import (
    PlayerRepository,
    GameRepository,
    PlayerPlaytimeRepository,
    PlayerGameOwnershipRepository,
    PlayerAchievementRepository,
    ReviewRepository
)


class PlayerGameRelationsCreationService:

    def __init__(self):
        self.player_repos = PlayerRepository()
        self.game_repos = GameRepository()
        self.playtime_repos = PlayerPlaytimeRepository()
        self.ownership_repos = PlayerGameOwnershipRepository()
        self.achievement_repos = PlayerAchievementRepository()
        self.review_repos = ReviewRepository()

    def __check_user_game_created(self, data_list, session) -> \
            Tuple[Dict[str, int], Dict[str, int], List[str], List[str]]:

        unique_steam_ids = list({data.steam_id for data in data_list})
        unique_app_ids = list({data.app_id for data in data_list})

        no_created_players = []
        no_created_games = []
        players_id = {}
        games_id = {}

        for steam_id in unique_steam_ids:
            player = self.player_repos.get_by_steam_id(steam_id=steam_id, session=session)
            if player:
                players_id[steam_id] = player.id
            else:
                no_created_players.append(steam_id)

        for app_id in unique_app_ids:
            game = self.game_repos.get_by_app_id(app_id=app_id, session=session)
            if game:
                games_id[app_id] = game.id
            else:
                no_created_games.append(app_id)

        return players_id, games_id, no_created_players, no_created_games

    def create_connections(self, players_info_chunk: List[Optional[PlayerGameDataAnalysisCreate]], session: Session):
        valid_players_data = [player_data for player_data in players_info_chunk if player_data is not None]

        if not valid_players_data:
            return

        all_owned = []

        for data in valid_players_data:
            if data is None:
                continue
            for owned in data.owned_games:
                all_owned.append(owned)

        players_ids, games_ids, no_created_players, no_created_games = \
            self.__check_user_game_created(all_owned, session)

        no_success_players = []

        ownerships = []
        playtimes = []
        achievements = []

        for player_data in valid_players_data:
            for data in player_data.owned_games:
                if data.steam_id in no_created_players:
                    continue

                if data.app_id in no_created_games:
                    if data.steam_id not in no_success_players:
                        no_success_players.append(data.steam_id)
                    continue

                if data is None:
                    continue

                ownerships.append(OwnershipCreate(
                    user_id=players_ids[data.steam_id],
                    game_id=games_ids[data.app_id]
                ))

            for data in player_data.playtimes:
                if data.steam_id in no_created_players:
                    continue

                if data.app_id in no_created_games:
                    if data.steam_id not in no_success_players:
                        no_success_players.append(data.steam_id)
                    continue
                playtimes.append(PlaytimeCreate(
                    user_id=players_ids[data.steam_id],
                    game_id=games_ids[data.app_id],
                    playtime_forever=data.playtime_forever,
                    playtime_2weeks=data.playtime_2weeks,
                    last_played=data.last_played,
                ))

            # for data in player_data.achievements:
            #     if data.steam_id in no_created_players:
            #         continue
            #
            #     if data.app_id in no_created_games:
            #         if data.steam_id not in no_success_players:
            #             no_success_players.append(data.steam_id)
            #         continue
            #
            #     achievement = session.query(Achievement).filter(
            #         Achievement.game_id == games_ids[data.app_id],
            #         Achievement.name == data.apiname).first()
            #
            #     if achievement is None:
            #         no_success_players.append(player_data.steam_id)
            #         continue
            #
            #     achievements.append(AchievementCreate(
            #         user_id=players_ids[data.steam_id],
            #         game_id=games_ids[data.app_id],
            #         achievement_id=achievement.id,
            #         achieved=data.achieved,
            #         unlock_time=data.unlock_time,
            #         unlock_timestamp=data.unlock_timestamp,
            #     ))

        self.ownership_repos.create_ownerships_bulk(session=session, ownerships_data=ownerships)
        self.playtime_repos.create_playtimes_bulk(session=session, playtimes_data=playtimes)
        # self.achievement_repos.create_achievements_bulk(session=session, achievements_data=achievements)

        return no_created_players, no_created_games, no_success_players

    def create_connections_ownership(self, ownership_data: List[OwnershipHttp], session: Session):
        players_ids, games_ids, no_created_players, no_created_games = \
            self.__check_user_game_created(ownership_data, session)

        no_created = []
        ownerships = []
        for data in ownership_data:
            if data.steam_id in no_created_players or data.app_id in no_created_games:
                no_created.append(data)
                continue
            ownerships.append(OwnershipCreate(
                user_id=players_ids[data.steam_id],
                game_id=games_ids[data.app_id]
            ))

        self.ownership_repos.create_ownerships_bulk(session=session, ownerships_data=ownerships)

        return no_created, no_created_players, no_created_games

    def create_connections_achievements(self, achievements_data: List[AchievementHttp], session: Session):
        players_ids, games_ids, no_created_players, no_created_games = \
            self.__check_user_game_created(achievements_data, session)

        no_created = []
        achievements = []
        for data in achievements_data:
            if data.steam_id in no_created_players or data.app_id in no_created_games:
                no_created.append(data)
                continue

            achievement = session.query(Achievement).filter(
                Achievement.game_id == games_ids[data.app_id],
                Achievement.name == data.apiname).first()

            if achievement is None:
                continue

            achievements.append(AchievementCreate(
                user_id=players_ids[data.steam_id],
                game_id=games_ids[data.app_id],
                achievement_id=achievement.id,
                achieved=data.achieved,
                unlock_time=data.unlock_time,
                unlock_timestamp=data.unlock_timestamp,
            ))

        self.achievement_repos.create_achievements_bulk(session=session, achievements_data=achievements)

        return no_created, no_created_players, no_created_games

    def create_connections_playtimes(self, playtimes_data: List[PlaytimeHttp], session: Session):
        players_ids, games_ids, no_created_players, no_created_games = \
            self.__check_user_game_created(playtimes_data, session)

        no_created = []
        playtimes = []
        for data in playtimes_data:
            if data.steam_id in no_created_players or data.app_id in no_created_games:
                no_created.append(data)
                continue
            playtimes.append(PlaytimeCreate(
                user_id=players_ids[data.steam_id],
                game_id=games_ids[data.app_id],
                playtime_forever=data.playtime_forever,
                playtime_2weeks=data.playtime_2weeks,
                last_played=data.last_played,
            ))

        self.playtime_repos.create_playtimes_bulk(session=session, playtimes_data=playtimes)

        return no_created, no_created_players, no_created_games

    def create_connections_review(self, reviews_data: List[ReviewHttp], session: Session):
        players_ids, games_ids, no_created_players, no_created_games = \
            self.__check_user_game_created(reviews_data, session)

        no_created = []
        reviews = []
        for data in reviews_data:
            if data.steam_id in no_created_players or data.app_id in no_created_games:
                no_created.append(data)
                continue
            reviews.append(ReviewCreate(
                user_id=players_ids[data.steam_id],
                game_id=games_ids[data.app_id],
                recommendation_id=0,  # как взять??
                steam_id=data.steam_id,
                language=data.language,
                review=data.review,
                voted_up=data.voted_up,
                votes_up=data.votes_up,
                votes_funny=data.votes_funny,
                weighted_vote_score=data.weighted_vote_score,
                timestamp_created=data.timestamp_created,
                timestamp_updated=data.timestamp_updated,
                comment_count=data.comment_count,
                steam_purchase=data.steam_purchase,
                received_for_free=data.received_for_free,
                written_during_early_access=data.written_during_early_access,
                primarily_steam_deck=data.primarily_steam_deck,
            ))

        self.review_repos.create_reviews_bulk(session=session, reviews_data=reviews)

        return no_created, no_created_players, no_created_games
