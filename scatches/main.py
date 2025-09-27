import os
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

    steam = SteamAnalysisFacade(api_key)

    # Работа с игроками - чистые CRUD операции
    player = steam.get_player("76561197960435530")
    print(f"Игрок: {player.get('personaname')}")

    # Полный анализ игрока
    profile = steam.get_player_full_profile("76561197960435530")
    print(f"Игр в библиотеке: {profile['games_count']}")
    print(f"Всего друзей: {profile['friends_count']}")

    # Анализ предпочтений
    analysis = steam.analyze_player("76561197960287966")
    print(f"Общее время в играх: {analysis['total_playtime_hours']} часов")

    # Работа с играми
    game = steam.get_game(730)  # CS:GO
    print(f"Игра: {game.get('name')}")

    game_analysis = steam.analyze_game(730)
    print(f"Положительных отзывов: {game_analysis['review_analysis']['positive_rate']:.1%}")


if __name__ == "__main__":
    main()
