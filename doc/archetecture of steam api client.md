# Архитектура Steam Analysis Toolkit

## Текущие задачи по этой части артефактов

+ Для схемы (steamapi-arc-sc.png) [+ обсудить что в ней будет отражено]: 
  - Добавить в схемку codes.steamservices.SteamService
  - Отразить что Repos layer общается с помощью dataschemas
+ Добавить ещё диаграммы последовательности (возможно)
+ Добавить список dataschemas схем

## 🏗️ Обзор архитектуры

Steam Analysis Toolkit построен по принципам **многослойной архитектуры** с четким разделением ответственности между компонентами. Основная цель - предоставить простой и мощный интерфейс для работы с Steam API.

## 📊 Диаграмма архитектуры

![Архитектура Steam API Client](/assets/steamapi-arc-sc.png)

## 🎯 Основные компоненты

### 1. HTTP Layer (Слой HTTP клиентов)

**Назначение**: Абстракция над HTTP запросами с поддержкой rate limiting и обработкой ошибок.

```python
# Базовый интерфейс HTTP клиента
class HTTPClient(Protocol):
    def get(self, url: str, params: dict = None) -> dict: ...
    def post(self, url: str, data: dict = None) -> dict: ...

# Конкретные реализации
class RequestsClient: ...          # Простой синхронный клиент
class RequestsWithDelayClient: ... # Клиент с ограничением частоты запросов
```