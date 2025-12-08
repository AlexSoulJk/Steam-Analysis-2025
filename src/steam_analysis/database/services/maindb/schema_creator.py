from typing import Optional, List, Tuple, Dict
from sqlalchemy import select
from sqlalchemy.orm import Session

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
     ReviewHistoryRepository)

from steam_analysis.database.models import Developer, Publisher, User
from steam_analysis.core.schemas.game.developer import DeveloperCreate, PublisherCreate,\
    GameDeveloperCreate, GamePublisherCreate
from steam_analysis.core.schemas.game.pricehistory import PriceHistoryCreate
from steam_analysis.core.schemas.game.reviewhistory import ReviewHistoryCreate
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
                          session: Session) -> Tuple[List[Developer], List[Publisher]]:
        developers = list(map(lambda x: x.developers, data_without_none))
        publishers = list(map(lambda x: x.publishers, data_without_none))

        devCreates = []
        for dev in developers:
            devCreates.append(DeveloperCreate(name=dev))

        pubCreates = []
        for pub in publishers:
            pubCreates.append(PublisherCreate(name=pub))

        developers = self.developer.create_bulk(devCreates, session)
        publisher = self.publisher.create_bulk(pubCreates, session)
        return developers, publisher

    def __check_game_created(self, data_list, session) -> \
            Tuple[Dict[str, int], List[str]]:
        unique_app_ids = list({data.app_id for data in data_list})

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
                                 prep_info: Tuple[List[Developer], List[Publisher]],
                                 schemas_chunk: List[AddInfo],
                                 session: Session):
        all_details = []
        for data in schemas_chunk:
            for detail in data.add_details:
                if detail is None:
                    continue
                all_details.append(detail)

        games_ids, no_created_games = self.__check_game_created(all_details, session)

        prep_developers, prep_publishers = self.__prepare_developer_publisher(prep_info)
        game_developers = []
        game_publishers = []
        prices = []
        for detail in all_details:
            game_id = games_ids.get(str(detail.game_id))
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
            # TODO: add ratings


        all_reviews_info = []
        for data in schemas_chunk:
            for review in data.review_info:
                if review is None:
                    continue
                all_reviews_info.append(review)

        review_histories = []
        all_reviews = []
        for review_info in all_reviews_info:
            game_id = games_ids.get(str(review_info.game_id))
            if game_id is None:
                continue
            review_histories.append(
                ReviewHistoryCreate(
                    game_id=game_id,
                    review_score=review_info.review_score,
                    review_count=review_info.num_reviews,
                    positive_reviews=review_info.total_positive,
                    negative_reviews=review_info.total_negative
                )
            )
            reviews = review_info.reviews
            for review in review_info.reviews:
                author = review.author
                steam_id = author.steam_id

                # Ищем пользователя в нашей системе
                user_id = None
                if session:
                    query = select(User).where(User.steam_id == steam_id)
                    result = session.execute(query)
                    user = result.scalar_one_or_none()
                    if user:
                        user_id = user.id

                if user_id is None:
                    return

                # Собираем данные
                review_data = {
                    "game_id": game_id,
                    "recommendation_id": review.recommendation_id,
                    "steam_id": steam_id,
                    "user_id": user_id,
                    "language": review.language,
                    "review": review.review,
                    "timestamp_created": review.timestamp_created,
                    "timestamp_updated": review.timestamp_updated,
                    "voted_up": review.voted_up,
                    "votes_up": review.votes_up,
                    "votes_funny": review.votes_funny,
                    "weighted_vote_score": review.weighted_vote_score,
                    "comment_count": review.comment_count,
                    "steam_purchase": False,
                    "received_for_free": review.received_for_free,
                    "written_during_early_access": review.written_during_early_access,
                    "primarily_steam_deck": False
                }

                all_reviews.append(ReviewCreate(**review_data))

        all_achives = []
        for data in schemas_chunk:
            if data.schema is not None:
                game_id = games_ids.get(str(data.schema.game_id))
                if game_id is None:
                    continue
                data.schema.game_id = game_id
                all_achives.append(data.schema)

        self.gameDev.create_bulk(session, game_developers)
        self.gamePub.create_bulk(session, game_publishers)
        self.price.create_bulk(session, prices)
        self.review_history.create_bulk(session, review_histories)
        self.review.create_bulk(session, all_reviews)
        created_achievements = self.achievs.create_bulk(all_achives, session=session)

