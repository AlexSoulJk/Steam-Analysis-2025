# Задача 1: Кластеризация игр и анализ насыщенности ниш

## 📊 Анализ полей данных

### Разделение по динамике изменений

#### 🔒 Статические поля (редко меняются)
**Используются для кластеризации и классификации игр**

**Базовые идентификаторы:**
- `app_id` - уникальный идентификатор игры
- `name` - название игры  
- `type` - тип контента (game/dlc/demo/etc)

**Классификация и метаданные:**
- `genres` - список жанров (Action, RPG, Strategy)
- `categories` - игровые категории (Multi-player, Co-op, Single-player)
- `tags` - пользовательские теги (MOBA, Survival, Horror)
- `developers` - список разработчиков
- `publishers` - список издателей

**Технические характеристики:**
- `platforms` - поддержка платформ (Windows, Mac, Linux)
- `controller_support` - поддержка контроллеров
- `game_features` - особенности геймплея (PvP, PvE, Sandbox)

**Локализация и контент:**
- `supported_languages` - поддерживаемые языки
- `language_options` - типы локализации (интерфейс, озвучка, субтитры)
- `age_ratings` - возрастные рейтинги (ESRB, PEGI)

**Обоснование:** Эти поля описывают фундаментальные характеристики игры, которые практически не меняются после релиза. 
Идеальны для кластеризации - обеспечивают стабильную группировку игр.

**💡 Возможно стоит добавить:**

Ремарка: Эти поля улучшат кластеризацию по "техническому уровню" и визуальному стилю
- technical_requirements  # мин. требования к железу
- art_style: str  # "реалистичный", "стилизованный", "пиксель-арт"
- perspective: str  # "от первого лица", "от третьего лица", "вид сверху"

----

#### 🔄 Условно-статические поля (могут меняться редко)
**Требуют периодического обновления**

**Временные метки:**
- `release_date` - дата релиза (может меняться для early access)
- `coming_soon` - статус "скоро выйдет"

**Контентные обновления:**
- `achievements_count` - количество достижений (может увеличиваться)
- `is_free` - модель монетизации (может измениться на Free-to-Play)

**Обоснование:** Эти поля в основном стабильны, но могут изменяться при значительных обновлениях игры. 
Требуют проверки 1 раза в месяц.

**💡 Возможно стоит добавить:**

social_features: Dict[str, bool]  # лидерборды, мастерская, торговля
gameplay_style: List[str]  # "competitive", "casual", "story_driven"
update_frequency: str  # "частые", "регулярные", "редкие" обновления

----

#### 📈 Динамические поля (часто меняются)
**Используются для метрик насыщенности и трендов**

**Коммерческие показатели:**
- `price_info` - текущая цена и скидки
- `recommendations_count` - количество рекомендаций

**Метрики популярности:**
- `current_players` - текущий онлайн
- `peak_players_24h` - пиковый онлайн за сутки
- `peak_players_all_time` - исторический максимум

**Оценки и отзывы:**
- `review_score` - рейтинг отзывов
- `review_count` - количество отзывов
- `metacritic_score` - оценка Metacritic

**Обоснование:** Эти поля постоянно изменяются и отражают текущее состояние игры на рынке. 
Критически важны для расчета метрик насыщенности ниш и анализа трендов.

**💡 Возможно стоит добавить:**

- player_retention_metrics  отток, время игры, частота сессий
- similar_games похожих игр для анализа конкурентов

----

### Ключевые метрики для анализа насыщенности

**Статические поля → Кластеризация:**
- Группируем игры по жанрам, тегам и особенностям геймплея
- Создаем устойчивые кластеры для долгосрочного анализа

**Динамические поля → Метрики насыщенности:**
- **Коэффициент насыщенности** = (новые игры в кластере) / (средний онлайн)
- **Динамика выпуска** = количество релизов по годам в кластере
- **Успешность ниши** = отношение успешных игр к общему количеству

Такой подход обеспечивает:
- Стабильную кластеризацию на основе неизменяемых характеристик
- Актуальные метрики насыщенности на основе текущих данных
- Минимизацию пересчета кластеров при обновлении динамических полей

## 🔗 Запросы к API для сбора данных

### Базовые запросы (без ключа API)

#### 1. Получение списка всех игр {#get-app-list}

```http request
GET https://api.steampowered.com/ISteamApps/GetAppList/v2/
```
Response: 
```json
{
  "applist": {
    "apps": [
      {"appid": 570, "name": "Dota 2"},
      {"appid": 730, "name": "Counter-Strike: Global Offensive"}
    ]
  }
}
```

#### 2. Получение детали об игре {#get-app-list}

```http request
GET https://store.steampowered.com/api/appdetails?appids={appid}
```
Response: 
```json
{
  "steam_appid": 570,
  "name": "Dota 2",
  "type": "game",
  "genres": [{"id": "1", "description": "Action"}],
  "categories": [{"id": "1", "description": "Multi-player"}],
  "release_date": {"coming_soon": false, "date": "9 июл. 2013"},
  "developers": ["Valve"],
  "publishers": ["Valve"],
  "platforms": {"windows": true, "mac": true, "linux": true},
  "supported_languages": "Русский, English",
  "price_overview": {"currency": "RUB", "final": 0, "discount_percent": 0},
  "metacritic": {"score": 90},
  "recommendations": {"total": 1245678},
  "achievements": {"total": 123}
}
```

#### 3. Получение тегов игры {#get-app-list}
\# TODO: стоит вынести в отдельную подсекцию...
```http request
GET https://store.steampowered.com/app/{appid}/
```

Response: 
```html
<div class="glance_tags popular_tags">
  <a class="app_tag" href="...">MOBA</a>
  <a class="app_tag" href="...">Strategy</a>
</div>
```

### Запросы требующие API ключа

#### 1. Текущий онлайн игроков {#get-current-players}

```http request
GET https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?key={API_KEY}&appid={appid}
```

Response: 
```json 
{
  "response": {
    "player_count": 456123,
    "result": 1
  }
}
```

#### 2. Отзывы и рейтинги {#get-reviews}

```http request
GET https://store.steampowered.com/appreviews/{appid}?json=1&language=russian&purchase_type=all
```

Response:

```json
{
  "query_summary": {
    "total_reviews": 1500000,
    "review_score": 9,
    "review_score_desc": "Very Positive",
    "total_positive": 1350000,
    "total_negative": 150000
  }
}
```

#### 3. Схема достижений {#get-schema}

```http request
GET https://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2/?key={API_KEY}&appid={appid}
```

#### 4. Глобальные проценты достижений {#get-achievement-percentages} 
\# Проверить что это дает
```http request
GET https://api.steampowered.com/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v2/?gameid={appid}
```






