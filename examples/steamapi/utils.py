import os
from dotenv import load_dotenv

load_dotenv()

def load_api_key():
    api_key = os.getenv('STEAM_API_KEY')

    if not api_key:
        print("❌ STEAM_API_KEY не найден в .env файле!")
        print("Добавь в .env: STEAM_API_KEY=твой_ключ_здесь")
        return

    print(f"✅ API ключ загружен: {api_key[:10]}...")
    return api_key


def load_api_keys():
    api_key = os.getenv('STEAM_API_KEY')
    api_key_1 = os.getenv('STEAM_API_KEY_1', default=None)
    api_key_2 = os.getenv('STEAM_API_KEY_2', default=None)

    if not api_key:
        print("❌ STEAM_API_KEY не найден в .env файле!")
        print("Добавь в .env: STEAM_API_KEY=твой_ключ_здесь")
        return

    print(f"✅ API ключ загружен: {api_key[:10]}...")
    ret_keys = [api_key, api_key_1, api_key_2]
    return list(filter(lambda x: x is not None, ret_keys))
