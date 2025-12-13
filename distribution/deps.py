from functools import wraps
from typing import Callable, List




def validate_json_strategy(**kwargs):
    return


def get_app_mediator(api_key: str, processor_name: str):
    from steam_analysis.app.application import AppMediator
    return AppMediator(api_key, processor_name)


def validation(handlers: List[Callable]):
    """
    Декоратор для валидации аргументов функции.

    Args:
        handlers: Список функций-валидаторов
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            error_messages = []

            # Для простоты валидируем все аргументы
            for handler in handlers:
                try:
                    # Передаем все аргументы в валидатор
                    result = handler(*args, **kwargs)
                    if isinstance(result, tuple) and result[0] != "OK":
                        error_messages.append(result[1])
                except Exception as e:
                    error_messages.append(str(e))

            if error_messages:
                raise ValueError("\n".join(error_messages))

            return func(*args, **kwargs)

        return wrapper

    return decorator
