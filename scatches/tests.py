import os

import requests
from dotenv import load_dotenv

from steam_analysis.resourcemanager.manager import ResourceManager
from steam_analysis.resourcemanager.resources.codes import ResourceCodes

load_dotenv()

def test_store_api():
    """Тестируем Store API напрямую"""
    print("🔍 Testing Store API directly...")

    # Тест 1: Детали игры (должно работать)
    url1 = "https://store.steampowered.com/api/appdetails"
    params1 = {'appids': 730}

    try:
        response1 = requests.get(url1, params=params1, timeout=10)
        print(f"🎮 Game details - Status: {response1.status_code}")
        if response1.status_code == 200:
            data = response1.json()
            game_name = data.get('730', {}).get('data', {}).get('name', 'Unknown')
            print(f"   Game: {game_name}")
    except Exception as e:
        print(f"   Error: {e}")

    # Тест 2: Отзывы (может не работать)
    url2 = "https://store.steampowered.com/appreviews/730"
    params2 = {
        'json': 1,
        # 'filter': 'all',
        # 'language': 'all',
        # 'num_per_page': 10,
        # 'cursor': "*"
    }

    try:
        response2 = requests.get(url2, params=params2, timeout=10)
        print(f"📝 Reviews - Status: {response2.status_code}")
        if response2.status_code == 200:
            data = response2.json()
            reviews_count = len(data.get('reviews', []))
            print(f"   Reviews received: {reviews_count}")
        else:
            print(f"   Response: {response2.text[:200]}...")
    except Exception as e:
        print(f"   Error: {e}")


def test_web_api():
    """Тестируем Web API с ключом"""
    api_key = os.getenv('STEAM_API_KEY')
    if not api_key:
        print("❌ No API key found")
        return

    print(f"\n🔑 Testing Web API with key: {api_key[:10]}...")

    url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
    params = {'key': api_key, 'steamids': '76561197960287966'}

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"👤 Player API - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            player = data['response']['players'][0]
            print(f"   Player: {player.get('personaname')}")
    except Exception as e:
        print(f"   Error: {e}")


def test_resource_system():
    manager = ResourceManager()

    # Теперь с типизацией!
    resource = manager.get_resource(ResourceCodes.GAME_LIST)
    print(f"Resource: {resource.name.value}")
    print(f"File path: {resource.file_path}")


if __name__ == "__main__":
    # test_store_api()
    # test_web_api()
    test_resource_system()