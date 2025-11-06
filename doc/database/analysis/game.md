# AnalysisChunk

Отражает диапазон (чанк) app_ids для обработки.

## Поля:

**status** = Column(String(50), default="pending")
- `pending` - по умолчанию при создании или если все игры завершились с `failed`
- `in_progress` - при начале обработки любой игры в чанке  
- `partial_success` - после обработки, если есть игры со статусом `partial`
- `success` - после обработки, когда ВСЕ игры в `success` или `null_state`

**processed_by** = Column(String(100), nullable=True)
- Исполнитель для обработки чанка (может меняться)

**response_time** = Column(Float)
- Суммарное время обработки чанка (аккумулируется при каждом запуске)

**error_log** = Column(Text)
- Агрегированные ошибки: ошибки чанка + конкатенация ошибок всех игр

**started_at** = Column(DateTime)
- Время первого перехода в `in_progress` (валидация: started_at ≤ finished_at)

**finished_at** = Column(DateTime) 
- Время последнего завершения обработки (обновляется при каждом завершении)

# GameDataAnalysis

Статусы обработки конкретной игры.

## Поля:

**status** = Column(String(50), default="pending")
- `pending` - игра добавлена в чанк
- `in_progress` - в процессе обработки
- `success` - все статические поля заполнены
- `partial` - часть статических полей не заполнена
- `failed` - Steam API вернул ошибку (техническая проблема)
- `null_state` - Steam сообщил, что app_id не является игрой

**error_log** = Column(Text, nullable=True)
- Ошибка обработки конкретной игры