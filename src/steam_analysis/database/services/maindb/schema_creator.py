from typing import Optional, List, Tuple, Dict
from sqlalchemy import select
from sqlalchemy.orm import Session

from steam_analysis.core.schemas.game.dictionaries import AchievCreateDB, AchievPercentCreateDB
from steam_analysis.core.schemas.game.service import SchemaCreate, AddInfo, AddDetails
from steam_analysis.core.services.schema_morpher import SchemaMorpher
from steam_analysis.database.repositories import \
    (GameRepository,
     AchievRepository,
     PublisherRepository,
     PriceHistoryRepository,
     GamePublisherRepository,
     GameDeveloperRepository,
     ReviewRepository,
     DeveloperRepository,
     ReviewHistoryRepository,
     AchievementHistoryRepository,
     RatingRepository,
     RatingNameRepository)

from steam_analysis.database.models import Developer, Publisher, RatingNames
from steam_analysis.core.schemas.game.developer import DeveloperCreate, PublisherCreate,\
    GameDeveloperCreate, GamePublisherCreate
from steam_analysis.core.schemas.game.pricehistory import PriceHistoryCreate
from steam_analysis.core.schemas.game.reviewhistory import ReviewHistoryCreate
from steam_analysis.core.schemas.game.ratings import RatingCreate, RatingNameCreate
from steam_analysis.database.support_models.schema_creation import PreparedForSchemaCreation
from steam_analysis.core.schemas.player.playergame import ReviewCreate


class SchemaCreationService:

    def __init__(self):
        self.game_repos = GameRepository()
        self.achievs = AchievRepository()
        self.developer = DeveloperRepository()
        self.publisher = PublisherRepository()
        self.gameDev = GameDeveloperRepository()
        self.gamePub = GamePublisherRepository()
        self.review = ReviewRepository()
        self.review_history = ReviewHistoryRepository()
        self.price = PriceHistoryRepository()
        self.achievs_history = AchievementHistoryRepository()
        self.rating = RatingRepository()
        self.ratingname = RatingNameRepository()
        # self.stats = StatsRepository()x

    # def create_chunk_schemas(self, schemas_chunk: List[Optional[SchemaCreate]],
    #                        session: Session) -> Tuple[list[Game], PreparedForSchemaCreation,
    #                         Dict[int, SchemaCreate]]:
    #     data_without_none = list(filter(lambda x: x is not None, schemas_chunk))
    #     dict_without_nons = {data_analys_schema.game_id: data_analys_schema for data_analys_schema in
    #                          data_without_none}
    #
    #     created_achievements = self.achievs.create_bulk(dict_without_nons,
    #                                         session=session)

    def prepare_relations(self, data_without_none: List[AddDetails],
                          session: Session) -> Tuple[List[Developer], List[Publisher], List[RatingNames]]:
        developers = []
        publishers = []
        ratings_names = []
        for data in data_without_none:
            if data is None:
                continue
            devs = data.developers
            if not devs:
                continue
            for dev in devs:
                if dev in developers:
                    continue
                developers.append(dev)

            pubs = data.publishers
            if not pubs:
                continue
            for pub in pubs:
                if pub in publishers:
                    continue
                publishers.append(pub)

            ratings = data.ratings
            if not ratings:
                continue
            for rating in ratings:
                if rating.rating_name in ratings_names:
                    continue
                ratings_names.append(rating.rating_name)

        devCreates = []
        for dev in developers:
            devCreates.append(DeveloperCreate(name=dev, description="", website=""))

        pubCreates = []
        for pub in publishers:
            pubCreates.append(PublisherCreate(name=pub, description="", website=""))

        ratingNameCreate = []
        for rating_name in ratings_names:
            ratingNameCreate.append(
                RatingNameCreate
                (
                    description=rating_name
                )
            )

        developers = self.developer.create_bulk(devCreates, session)
        publisher = self.publisher.create_bulk(pubCreates, session)
        ratingnames = self.ratingname.create_bulk(ratingNameCreate, session)
        return developers, publisher, ratingnames

    def __check_game_created(self, data_list, session) -> \
            Tuple[Dict[int, int], List[int]]:
        unique_app_ids = list({data.game_id for data in data_list})

        no_created_games = []
        games_id = {}
        for app_id in unique_app_ids:
            game = self.game_repos.get_by_app_id(app_id=app_id, session=session)
            if game:
                games_id[app_id] = game.id
            else:
                no_created_games.append(app_id)

        return games_id, no_created_games

    def __prepare_developer_publisher(self,
                                      dev_pubs: Tuple[List[Developer], List[Publisher]]):
        dev_dict = {}
        for dev in dev_pubs[0]:
            dev_dict[dev.name] = dev.id

        pub_dict = {}
        for pub in dev_pubs[1]:
            pub_dict[pub.name] = pub.id

        return dev_dict, pub_dict

    def create_chunk_add_schemas(self,
                                 prep_info: Tuple[List[Developer], List[Publisher], List[RatingNames]],
                                 schemas_chunk: List[AddInfo],
                                 session: Session):
        all_details = []
        for data in schemas_chunk:
            if data.add_details is None:
                continue
            all_details.append(data.add_details)

        games_ids, no_created_games = self.__check_game_created(all_details, session)

        prep_developers = {dev.name: dev.id for dev in prep_info[0]}
        prep_publishers = {pub.name: pub.id for pub in prep_info[1]}
        prep_rating_names = {ratingname.description: ratingname.id for ratingname in prep_info[2]}

        game_developers = []
        game_publishers = []
        prices = []
        all_ratings = []
        for detail in all_details:
            game_id = games_ids.get(detail.game_id)
            if game_id is None:
                continue

            developers = detail.developers
            for dev in developers:
                dev_id = prep_developers.get(dev)
                if dev_id is None:
                    continue
                game_developers.append(
                    GameDeveloperCreate(game_id=game_id,
                                        developer_id=dev_id))

            publishers = detail.publishers
            for pub in publishers:
                pub_id = prep_publishers.get(pub)
                if pub_id is None:
                    continue
                game_publishers.append(
                    GamePublisherCreate(game_id=game_id,
                                        publisher_id=pub_id))

            price = detail.price_overview
            if price is None:
                continue
            prices.append(
                PriceHistoryCreate(
                    game_id=game_id,
                    currency=price.currency,
                    price_final=price.final,
                    discount_percent=price.discount_percent,
                    initial=price.initial
                )
            )

            ratings = detail.ratings
            for rating in ratings:
                rating_name_id = prep_rating_names.get(rating.rating_name)
                if rating_name_id is None:
                    continue
                all_ratings.append(
                    RatingCreate(
                        game_id=game_id,
                        rating_name_id=rating_name_id,
                        rating=rating.rating,
                        req_age=rating.req_age,
                        banned=rating.banned
                    )
                )


        all_reviews_info = []
        for data in schemas_chunk:
            if data.review_info is None:
                continue
            all_reviews_info.append(data.review_info)

        review_histories = []
        all_reviews = []
        for review_info in all_reviews_info:
            game_id = games_ids.get(review_info.game_id)
            if game_id is None:
                continue
            review_histories.append(
                ReviewHistoryCreate(
                    game_id=game_id,
                    review_score=review_info.review_score / 10,
                    review_count=review_info.total_reviews,
                    positive_reviews=review_info.total_positive,
                    negative_reviews=review_info.total_negative
                )
            )
            # reviews = review_info.reviews
            # for review in review_info.reviews:
            #     author = review.author
            #     steam_id = author.steam_id
            #
            #     # Ищем пользователя в нашей системе
            #     user_id = None
            #     if session:
            #         query = select(User).where(User.steam_id == steam_id)
            #         result = session.execute(query)
            #         user = result.scalar_one_or_none()
            #         if user:
            #             user_id = user.id
            #
            #     if user_id is None:
            #         return
            #
            #     # Собираем данные
            #     review_data = {
            #         "game_id": game_id,
            #         "recommendation_id": review.recommendation_id,
            #         "steam_id": steam_id,
            #         "user_id": user_id,
            #         "language": review.language,
            #         "review": review.review,
            #         "timestamp_created": review.timestamp_created,
            #         "timestamp_updated": review.timestamp_updated,
            #         "voted_up": review.voted_up,
            #         "votes_up": review.votes_up,
            #         "votes_funny": review.votes_funny,
            #         "weighted_vote_score": review.weighted_vote_score,
            #         "comment_count": review.comment_count,
            #         "steam_purchase": False,
            #         "received_for_free": review.received_for_free,
            #         "written_during_early_access": review.written_during_early_access,
            #         "primarily_steam_deck": False
            #     }
            #
            #     all_reviews.append(ReviewCreate(**review_data))

        all_achives = []
        for data in schemas_chunk:
            if data.schema_data is None:
                continue

            game_id = games_ids.get(data.schema_data.game_id)
            if game_id is None:
                continue

            achives = data.schema_data.achievs
            for ach in achives:
                all_achives.append(
                    AchievCreateDB(
                        game_id=game_id,
                        name=ach.name,
                        hidden=ach.hidden,
                        displayName=ach.displayName,
                        defaultvalue=ach.defaultvalue
                    )
                )

        created_achievements = self.achievs.create_bulk(all_achives, session=session)
        session.flush()

        achieves_ids = {ach.name: ach.id for ach in created_achievements}
        achives_histories = []
        for data in schemas_chunk:
            data_ach = data.achiev_persentage
            if data_ach is None:
                continue
            game_id = games_ids.get(data_ach.game_id)
            if game_id is None:
                continue
            achiv_percents = data_ach.achievs
            for ach in achiv_percents:
                ach_id = achieves_ids.get(ach.achievement_name)
                achives_histories.append(
                    AchievPercentCreateDB
                    (
                        achievement_id=ach_id,
                        percent=ach.percent
                    )
                )

        self.achievs_history.create_bulk(achives_histories, session)

        self.gameDev.create_bulk(session, game_developers)
        self.gamePub.create_bulk(game_publishers, session)
        self.price.create_bulk(prices, session)
        self.review_history.create_bulk(review_histories, session)
        self.rating.create_bulk(all_ratings, session)
        # self.review.create_bulk(session, all_reviews)

