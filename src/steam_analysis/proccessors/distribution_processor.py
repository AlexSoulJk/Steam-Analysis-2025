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

class DistribProcessor:  # ЭТО СЕРВИС: ПООБЩАЛСЯ С БАЗОЙ И СОБРАЛ ДАННЫЕ ДЛЯ КЛАСТЕРИЗАЦИИ И ОТДАЛ В ПРОВАЙДЕР (ФАСАД)

    def __init__(self):
        self.game_repo = GameRepository()
        self.game_type_repo = TypeRepository()
        self.categories = CategoryRepository()

    def get_price_distribution_by_genre(self,
                                        n: int = 10,
                                        price_type: str = 'final',
                                        min_games: int = 5) -> Optional[CharacterByPrice]:
        """
        Получает распределение цен по топ-N жанрам

        Args:
            n: количество топ жанров для анализа (по количеству игр)
            price_type: 'final' для финальной цены, 'initial' для начальной
            min_games: минимальное количество игр в жанре для включения в статистику

        Returns:
            CharacterByPrice со средними ценами по жанрам
        """
        try:
            with get_db() as session:
                price_data = self.game_repo.get_prices_by_genre(
                    session=session,
                    n=n,
                    price_type=price_type,
                    min_games=min_games
                )
                return price_data
        except Exception as e:
            print(f"Ошибка при получении распределения цен по жанрам: {e}")
            return None

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

    def get_categories_dynamics(self,
                                n: int = 10,
                                time_period: str = "yearly",
                                years_back: int = 5) -> Optional[CharacterByTime]:
        """
        Получает динамику релизов по категориям

        Args:
            n: количество топ категорий
            time_period: 'yearly' (по годам), 'quarterly' (по кварталам)
            years_back: количество лет для анализа
        """
        try:
            with get_db() as session:
                if time_period == "quarterly":
                    dynamics_data = self.game_repo.get_categories_dynamics(
                        session=session,
                        n=n,
                        years_back=min(years_back, 3)  # Для кварталов берем меньше лет
                    )
                else:
                    dynamics_data = self.game_repo.get_categories_dynamics(
                        session=session,
                        n=n,
                        years_back=years_back
                    )

                if dynamics_data and dynamics_data.values:
                    print(f"Получена динамика по {len(dynamics_data.ticks)} категориям")
                    print(f"Количество временных точек: {len(dynamics_data.values[0]) if dynamics_data.values else 0}")

                return dynamics_data

        except Exception as e:
            print(f"Ошибка при получении динамики по категориям: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_genres_dynamics(self,
                            n: int = 10,
                            time_period: str = "yearly",
                            years_back: int = 5) -> Optional[CharacterByTime]:
        """
        Получает динамику релизов по жанрам
        """
        try:
            with get_db() as session:
                dynamics_data = self.game_repo.get_genres_dynamics(
                    session=session,
                    n=n,
                    years_back=years_back
                )

                if dynamics_data and dynamics_data.values:
                    print(f"Получена динамика по {len(dynamics_data.ticks)} жанрам")
                    # Статистика
                    for i, (genre, values) in enumerate(zip(dynamics_data.ticks, dynamics_data.values)):
                        if i < 3:  # Первые 3 для примера
                            print(f"  {genre}: {sum(values)} игр за период")

                return dynamics_data

        except Exception as e:
            print(f"Ошибка при получении динамики по жанрам: {e}")
            import traceback
            traceback.print_exc()
            return None

