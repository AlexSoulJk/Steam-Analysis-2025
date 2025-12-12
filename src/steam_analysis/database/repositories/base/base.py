from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, Union, Tuple
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import Session, DeclarativeBase
from steam_analysis.database.models.base import BaseModel as BaseDBModel
from pydantic import BaseModel

ModelType = TypeVar("ModelType", bound=BaseDBModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


# Базовый класс для моделей SQLAlchemy

class BaseDBRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Базовый синхронный CRUD репозиторий с операциями Create, Read, Update, Delete"""

    def __init__(self, model: Type[ModelType]):
        """
        Инициализация репозитория

        Args:
            model: SQLAlchemy модель
            db_session: Синхронная сессия базы данных
        """
        self.model = model

    def get(self, id: Any, session: Session) -> Optional[ModelType]:
        """
        Получить объект по ID

        Args:
            id: ID объекта

        Returns:
            Объект модели или None если не найден
        """
        return session.get(self.model, id)

    def get_by_field(self, field_name: str, value: Any, session: Session) -> Optional[ModelType]:
        """
        Получить объект по значению поля

        Args:
            field_name: Название поля
            value: Значение поля

        Returns:
            Объект модели или None если не найден
        """
        if not hasattr(self.model, field_name):
            raise AttributeError(f"Model {self.model.__name__} has no field {field_name}")

        query = select(self.model).where(getattr(self.model, field_name) == value)
        result = session.execute(query)
        return result.scalar_one_or_none()

    def get_multi(
            self,
            *,
            skip: int = 0,
            limit: int = 100,
            filters: Optional[Dict] = None,
            order_by: Optional[str] = None,
            session: Session
    ) -> List[ModelType]:
        """
        Получить список объектов с пагинацией и фильтрацией

        Args:
            skip: Количество пропускаемых записей
            limit: Максимальное количество записей
            filters: Словарь фильтров {поле: значение}
            order_by: Поле для сортировки

        Returns:
            Список объектов
        """
        query = select(self.model)

        # Применяем фильтры
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)

        # Применяем сортировку
        if order_by and hasattr(self.model, order_by):
            query = query.order_by(getattr(self.model, order_by))

        # Применяем пагинацию
        query = query.offset(skip).limit(limit)

        result = session.execute(query)
        return result.scalars().all()

    def create(self, obj_in: CreateSchemaType, session: Session) -> ModelType:
        """
        Создать новый объект

        Args:
            obj_in: Pydantic схема с данными для создания

        Returns:
            Созданный объект
        """
        # Конвертируем Pydantic модель в словарь
        obj_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else obj_in.dict()

        # Создаем экземпляр модели
        db_obj = self.model(**obj_data)

        # Добавляем в сессию и коммитим
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)

        return db_obj

    def create_bulk(self, objects_in: List[CreateSchemaType],
                    session: Session,
                    no_commit=False) -> List[ModelType]:
        """
        Массовое создание объектов

        Args:
            objects_in: Список Pydantic схем

        Returns:
            Список созданных объектов
        """
        db_objects = []
        for obj_in in objects_in:
            # Стоит ли так оставлять?? с alias в качестве жестко захоровоженного
            obj_data = obj_in.model_dump(by_alias=True) if hasattr(obj_in, 'model_dump') else obj_in.dict()
            db_obj = self.model(**obj_data)
            db_objects.append(db_obj)

        session.add_all(db_objects)

        if not no_commit:
        # Обновляем объекты, чтобы получить их ID
            session.commit()
            for db_obj in db_objects:
                session.refresh(db_obj)
        else:
            session.flush()

        return db_objects

    def exists_bulk(self, session: Session, field_name: str, values: List[Any]) -> List[bool]:
        """
        Проверить существование объектов по значениям поля (пакетно)
        Возвращает список [True/False] для каждого значения
        """
        if not values:
            return []

        if not hasattr(self.model, field_name):
            raise AttributeError(f"Model {self.model.__name__} has no field {field_name}")

        # Один запрос к базе
        existing = session.query(getattr(self.model, field_name)).filter(
            getattr(self.model, field_name).in_(values)
        ).all()

        existing_set = {row[0] for row in existing}
        return [value in existing_set for value in values]

    def update(
            self,
            *,
            no_commit: bool = False,
            db_obj: ModelType,
            obj_in: Union[UpdateSchemaType, Dict[str, Any]],
            session: Session
    ) -> ModelType:

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                current_value = getattr(db_obj, field)
                if current_value != value:
                    setattr(db_obj, field, value)

        session.add(db_obj)

        if not no_commit:
            session.commit()
            session.refresh(db_obj)

        return db_obj

    def update_by_id(
            self,
            id: Any,
            obj_in: Union[UpdateSchemaType, Dict[str, Any]],
            session: Session,
            no_commit: bool = False,
    ) -> Optional[ModelType]:
        """
        Обновить объект по ID

        Args:
            id: ID объекта для обновления
            obj_in: Pydantic схема или словарь с данными для обновления

        Returns:
            Обновленный объект или None если не найден
        """
        db_obj = self.get(id, session)
        if not db_obj:
            return None

        return self.update(db_obj=db_obj, obj_in=obj_in, session=session, no_commit=no_commit)

    def delete(self, id: Any, session: Session) -> bool:
        """
        Удалить объект по ID

        Args:
            id: ID объекта для удаления

        Returns:
            True если объект удален, False если не найден
        """
        db_obj = self.get(id, session)
        if not db_obj:
            return False

        session.delete(db_obj)
        session.commit()

        return True

    def delete_by_field(self, field_name: str, value: Any, session: Session) -> int:
        """
        Удалить объекты по значению поля

        Args:
            field_name: Название поля
            value: Значение поля

        Returns:
            Количество удаленных объектов
        """
        if not hasattr(self.model, field_name):
            raise AttributeError(f"Model {self.model.__name__} has no field {field_name}")

        query = delete(self.model).where(getattr(self.model, field_name) == value)
        result = session.execute(query)
        session.commit()

        return result.rowcount

    def exists(self, session: Session, **filters) -> bool:
        """
        Проверить существование объекта по фильтрам

        Args:
            **filters: Фильтры для поиска

        Returns:
            True если объект существует, иначе False
        """
        query = select(self.model)
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)

        result = session.execute(query)
        return result.scalar_one_or_none() is not None

    def count(self, session: Session, filters: Optional[Dict] = None) -> int:
        """
        Получить количество объектов по фильтрам

        Args:
            filters: Словарь фильтров

        Returns:
            Количество объектов
        """
        query = select(self.model)

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)

        result = session.execute(query)
        return len(result.scalars().all())

    def get_or_create(
            self,
            session: Session,
            defaults: Optional[Dict] = None,
            **filters
    ) -> tuple[ModelType, bool]:
        """
        Получить объект или создать если не существует

        Args:
            defaults: Значения по умолчанию для создания
            **filters: Фильтры для поиска

        Returns:
            Кортеж (объект, создан_ли_новый)
        """
        db_obj = session.execute(
            select(self.model).filter_by(**filters)
        ).scalar_one_or_none()

        if db_obj:
            return db_obj, False

        # Создаем новый объект
        create_data = filters.copy()
        if defaults:
            create_data.update(defaults)

        db_obj = self.model(**create_data)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)

        return db_obj, True

    def count_with_join_group_by(
            self,
            session: Session,
            join_model: Type,
            join_condition,
            group_by_field: str,
            count_field: str = 'id',
            filters: Optional[Dict] = None,
            additional_joins: Optional[List[Tuple[Type, Any]]] = None
    ) -> List[Tuple[Any, int]]:
        """
        Подсчитать количество объектов с JOIN и GROUP BY

        Args:
            session: SQLAlchemy сессия
            join_model: Модель для JOIN
            join_condition: Условие JOIN
            group_by_field: Поле для группировки
            count_field: Поле для подсчета
            filters: Дополнительные фильтры
            additional_joins: Дополнительные JOIN-ы

        Returns:
            Список кортежей (значение_группы, количество)
        """
        query = (
            select(
                getattr(join_model, group_by_field),
                func.count(getattr(self.model, count_field)).label('count')
            )
            .select_from(self.model)
            .join(join_model, join_condition)
        )

        # Добавляем дополнительные JOIN-ы
        if additional_joins:
            for join_model_extra, join_condition_extra in additional_joins:
                query = query.join(join_model_extra, join_condition_extra)

        # Применяем фильтры
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)

        # Группировка и сортировка
        query = query.group_by(getattr(join_model, group_by_field))
        query = query.order_by(func.count(getattr(self.model, count_field)).desc())

        result = session.execute(query)
        return result.all()

