from datetime import datetime
from typing import Dict, Any, Optional, List

from steam_analysis.core.schemas.game.dictionaries import GenreCreate, CategoryCreate, PlatformCreate
from steam_analysis.core.schemas.game.game import GameCreate


class GameParser:

    # region Extraction methods for filling database model GameDataAnalysisCreate
    @staticmethod
    def extract_game_create_info(app_id: int, raw_data: Dict[str, Any]) -> GameCreate:
        """Парсим основную информацию об игре используя существующую GameCreate"""
        release_date = GameParser._parse_release_date(raw_data.get('release_date', {}).get('date'))
        return GameCreate(
            app_id=app_id,
            name=raw_data.get('name', 'Unknown'),
            type=raw_data.get('type', 'unknown'),
            is_free=raw_data.get('is_free', False),
            release_date=release_date,
            coming_soon=raw_data.get('release_date', {}).get('coming_soon', False),
            controller_support=raw_data.get('controller_support', 'none'),
        )

    @staticmethod
    def extract_game_genres(raw_data: Dict[str, Any]) -> List[GenreCreate]:
        return list(map(lambda x: GenreCreate(**x), raw_data.get('genres', [])))

    @staticmethod
    def extract_categories(raw_data: Dict[str, Any]) -> List[CategoryCreate]:
        return list(map(lambda x: CategoryCreate(**x), raw_data.get('categories', [])))

    @staticmethod
    def extract_platforms(raw_data: Dict[str, Any]) -> List[PlatformCreate]:
        data = raw_data.get("platforms", {})
        return list(map(lambda x: PlatformCreate(description=x[0]), filter(lambda x: x[1], data.items())))

    # endregion
    # region Support Private Parse methods
    @staticmethod
    def _parse_release_date(date_string: str) -> Optional[datetime]:
        """Парсинг даты релиза из строки"""
        if not date_string:
            return None

        try:
            from dateutil import parser
            return parser.parse(date_string)
        except:
            # Fallback для простых форматов
            try:
                return datetime.strptime(date_string, '%d %b, %Y')
            except:
                return None

    @staticmethod
    def _parse_localisations(data: Dict[str, Any]) -> Dict[str, Any]:
        """Извлечение информации о локализации"""
        # Парсинг строки supported_languages в список
        lang_string = data.get('supported_languages', '')
        languages = [lang.strip() for lang in lang_string.split(',')] if lang_string else []

        # Определение типов локализации по наличию языков
        language_options = {
            'interface': any('russian' in lang.lower() for lang in languages),
            'full_audio': any('audio' in lang.lower() for lang in languages),
            'subtitles': any('subtitles' in lang.lower() for lang in languages),
        }

        return {
            'supported_languages': languages,
            'language_options': language_options,
        }

    # endregion
