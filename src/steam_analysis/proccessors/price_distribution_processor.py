from enum import Enum
from typing import Dict, List, Any, Optional
from collections import defaultdict

import statistics

from steam_analysis.database.facade import get_db
from steam_analysis.database.repositories import GameRepository
from steam_analysis.database.repositories.game.type import TypeRepository
from steam_analysis.database.repositories.game.category import CategoryRepository

from steam_analysis.proccessors.schemas.games import (AbstractGameBy_, GamesClusteringData,
                                                      TwoDHistogramData, GamesReleaseBySeason,
                                                      EnhancedHistogramData, CharacterByTime, CharacterByPrice,
                                                      GamesByTypes, GamesByCategories, GamesByCountCategoriesWithSubs, \
                                                      GamesByGenres)


class SeasonMode(str, Enum):
    monthly = "monthly"
    quarter = "quarter"


LABELS = {

        "monthly": {
                1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
                5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
                9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
        },

        "quarter": {
                1: "Q1 (Янв-Мар)", 2: "Q2 (Апр-Июн)",
                3: "Q3 (Июл-Сен)", 4: "Q4 (Окт-Дек)"
        }
    }

class PriceDistribProcessor:  # ЭТО СЕРВИС: ПООБЩАЛСЯ С БАЗОЙ И СОБРАЛ ДАННЫЕ ДЛЯ КЛАСТЕРИЗАЦИИ И ОТДАЛ В ПРОВАЙДЕР (ФАСАД)

    def __init__(self):
        self.game_repo = GameRepository()
        self.game_type_repo = TypeRepository()
        self.categories = CategoryRepository()

    def get_price_distribution_by_category(self,
                                           n: int = 10,
                                           price_type: str = 'final',
                                           min_games: int = 5,
                                           type_id: int = 1) -> Optional[CharacterByPrice]:
        """
        Получает распределение цен по топ-N категориям
        """
        try:
            with get_db() as session:
                price_data = self.game_repo.get_prices_by_category(
                    session=session,
                    n=n,
                    price_type=price_type,
                    min_games=min_games,
                    type_id=type_id  # ← Передаем type_id
                )

                print(f"GameProcessor: Анализируем type_id={type_id}")

                return price_data
        except Exception as e:
            print(f"Ошибка при получении распределения цен по категориям: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_category_by_price(self, n_columns: int = 10, convert_to_rub: bool = True, type_id: int = 1):
        """
        Получает данные о ценах по категориям
        """
        try:
            result = self.clustering_game_proccesor.get_price_distribution_by_category(
                n=n_columns,
                price_type='final',
                min_games=5,
                type_id=type_id
            )

            if result:
                print(f"DataProvider: Получены цены для type_id={type_id}")
                print(f"  Количество категорий: {len(result.ticks)}")

            return result

        except Exception as e:
            print(f"DataProvider ошибка: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_games_release_by_season(self, code: SeasonMode = SeasonMode.monthly) -> Optional[GamesReleaseBySeason]:
        values = None

        with get_db() as session:
            values, ticks = self.game_repo.get_games_release_by_season(session=session,
                                                                        season_mode=code)
            values = {LABELS[code][int(value[0])]: value[1] for value in values.items()}
            ticks = list(map(lambda tick: LABELS[code][int(tick)], ticks))
        return GamesReleaseBySeason(values=values, ticks=ticks)


    def get_categories_dinamics(self, categories: List[str] = None,
                                time_period: str = "yearly") -> Optional[CharacterByTime]:

        ret = None
        with get_db() as session:
            results = self.game_repo.get_games_dynamics_by_categories(
                session=session,
                categories=categories,
                time_period=time_period
            )

            if results:
                time_periods = sorted(set(r[0] for r in results))
                category_data = defaultdict(list)

                for time_period_val, category, count in results:
                    category_data[category].append((time_period_val, count))

                all_categories = list(category_data.keys())

                if all_categories:
                    first_category = all_categories[0]
                    values = [count for _, count in sorted(category_data[first_category])]
                    ticks = [period for period, _ in sorted(category_data[first_category])]

                    ret = CharacterByTime(
                        values=values,
                        ticks=ticks
                    )

        return ret

    def get_genres_dinamics(self, genres: List[str] = None,
                            time_period: str = "yearly") -> Optional[CharacterByTime]:
        """
        Динамика выпуска игр по жанрам во времени
        """
        ret = None
        with get_db() as session:
            # Получаем данные о выпуске игр по времени
            results = self.game_repo.get_games_dynamics_by_genres(
                session=session,
                genres=genres,
                time_period=time_period
            )

            if results:
                # Группируем по временным периодам
                time_periods = sorted(set(r[0] for r in results))
                genre_data = defaultdict(list)

                for time_period_val, genre, count in results:
                    genre_data[genre].append((time_period_val, count))

                # Возвращаем данные для первого жанра или агрегируем
                all_genres = list(genre_data.keys())
                if all_genres:
                    first_genre = all_genres[0]
                    values = [count for _, count in sorted(genre_data[first_genre])]
                    ticks = [period for period, _ in sorted(genre_data[first_genre])]

                    ret = CharacterByTime(
                        values=values,
                        ticks=ticks
                    )

        return ret

