from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.sql import func

AnalysisBase = declarative_base()


class AnalysisBaseModel(AnalysisBase):
    """Базовая модель для аналитической БД (analysis-db)"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    @declared_attr
    def __tablename__(cls):
        """Автоматическое имя таблицы — snake_case от имени класса"""
        return cls.__name__.lower()

    def to_dict(self):
        """Преобразовать объект в словарь (для JSON / отладки)"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def update(self, **kwargs):
        """Универсальный апдейт полей модели"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self):
        """Компактное представление экземпляра"""
        attrs = []
        for column in self.__table__.columns:
            if column.primary_key:
                value = getattr(self, column.name)
                attrs.append(f"{column.name}={value}")
        return f"<{self.__class__.__name__}({', '.join(attrs)})>"
