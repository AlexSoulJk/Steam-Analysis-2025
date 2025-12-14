from functools import wraps
from typing import Dict, Callable
import inspect


class DepContainer:
    """Простой DI контейнер в стиле FastAPI"""

    def __init__(self):
        self._dependencies: Dict[str, Callable] = {}

    def register(self, name: str, factory: Callable):
        """Регистрируем фабрику зависимости"""
        self._dependencies[name] = factory

    def Dep(self, factory_name: str, *factory_args, **factory_kwargs):
        """Аналог Dep() из FastAPI"""

        def dependency():
            if factory_name not in self._dependencies:
                raise ValueError(f"Зависимость '{factory_name}' не зарегистрирована")

            factory = self._dependencies[factory_name]
            return factory(*factory_args, **factory_kwargs)

        return dependency

    def inject(self, func: Callable):
        """Декоратор для инъекции зависимостей"""
        sig = inspect.signature(func)

        bound = None

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Собираем все аргументы
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()

        new_kwargs = dict(bound.arguments)
        for param_name, param in sig.parameters.items():
            if hasattr(param.default, '__call__') and hasattr(param.default, '__name__'):
                if param.default.__name__ == 'dependency':
                    # Это зависимость, резолвим ее
                    dependency_value = param.default()
                    new_kwargs[param_name] = dependency_value

        return func(**new_kwargs)

conteiner = DepContainer()