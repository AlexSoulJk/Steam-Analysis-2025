import os

from steam_analysis.app.application import AppMediator
from steam_analysis.core.client.steamclient import SteamAnalysisFacade
from dotenv import load_dotenv

load_dotenv()


def main():
    # Инициализация

    api_key = os.getenv('STEAM_API_KEY')

    if not api_key:
        print("❌ STEAM_API_KEY не найден в .env файле!")
        print("Добавь в .env: STEAM_API_KEY=твой_ключ_здесь")
        return

    print(f"✅ API ключ загружен: {api_key[:10]}...")

    # steam = SteamAnalysisFacade(api_key)

    # Работа с игроками - чистые CRUD операции
    # player = steam.get_player("76561197960435530")
    # print(f"Игрок: {player.get('personaname')}")
    #
    # players_info = steam.get_players_info(["76561197960435530", "76561197960265731"])
    # if players_info:
    #     for info in players_info:
    #         print(f"Игрок: {info.get('personaname')}")
    #         communityvisibility = info.get('communityvisibilitystate')
    #         visibility_str = ""
    #         match communityvisibility:
    #             case 1:
    #                 visibility_str = "Приватный"
    #             case 2:
    #                 visibility_str = "Открыт только друзьям"
    #             case 3:
    #                 visibility_str = "Публичный"
    #         print(f"Видимость профиля Steam: {visibility_str}")

    # Получаем достижения игрока из его списков игр
    # player_id = "76561197960265731"
    # game_ids = ["10", "730", "646570", "632360"]
    # for game_id in game_ids:
    #     achievements = steam.get_player_achievements_by_one_game(player_id, game_id)
    #     print(f"appid = {game_id}")
    #     if achievements:
    #         print(f"count achievements = {len(achievements)}")
    #     stats = steam.get_player_game_stats(player_id, game_id)
    #     if stats:
    #         print(f"count all stats = {len(stats)}")
    #         print(f"count stats with value > 0 = "
    #               f"{len([stat for stat in stats if stat.get('value') > 0])}\n")
    #
    # # Полный анализ игрока
    # profile = steam.get_player_full_profile("76561197960435530")
    # print(f"Уровень Steam игрока: {profile['steam_level']}")
    # print(f"Игр в библиотеке: {profile['games_count']}")
    # print(f"Всего друзей: {profile['friends_count']}")
    # print(f"Список steam id друзей: {profile['friends_ids']}")

    # Анализ предпочтений
    # analysis = steam.analyze_player("76561197960287966")
    # print(f"Общее время в играх: {analysis['total_playtime_hours']} часов")

    # Работа с играми
    # game = steam.get_game(730)  # CS:GO
    # # steam.game_service.collect_categories((5, 10))
    # # print(f"Игры: {steam.game_service.get_game_list()}")
    # print(f"{game=}")
    # mediator = AppMediator(api_key)
    # mediator.create_game()
    # game_analysis = steam.analyze_game(730)
    # print(f"Положительных отзывов: {game_analysis['review_analysis']['positive_rate']:.1%}")


if __name__ == "__main__":
    main()
