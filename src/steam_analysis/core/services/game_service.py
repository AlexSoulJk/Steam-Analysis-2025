from typing import List, Dict, Any, Optional
from ..repositories.game_repository import GameRepository


class GameService:
    def __init__(self, game_repo: GameRepository):
        self.game_repo = game_repo

    def get_game_analysis(self, app_id: int) -> Optional[Dict[str, Any]]:
        """Полный анализ игры"""
        game_data = self.game_repo.get_by_id(app_id)
        if not game_data:
            return None

        reviews = self.game_repo.get_reviews(app_id, limit=50)
        schema = self.game_repo.get_schema(app_id)

        # Анализ отзывов
        positive_reviews = [r for r in reviews if r.get('voted_up')]
        review_score = len(positive_reviews) / len(reviews) if reviews else 0

        return {
            'game_info': game_data,
            'review_analysis': {
                'total_reviews': len(reviews),
                'positive_rate': review_score,
                'average_playtime': self._calculate_avg_playtime(reviews)
            },
            'achievements_count': len(schema.get('availableGameStats', {}).get('achievements', [])) if schema else 0
        }

    def _calculate_avg_playtime(self, reviews: List[Dict[str, Any]]) -> float:
        playtimes = [r.get('author', {}).get('playtime_forever', 0) for r in reviews]
        valid_playtimes = [p for p in playtimes if p > 0]
        return sum(valid_playtimes) / len(valid_playtimes) if valid_playtimes else 0