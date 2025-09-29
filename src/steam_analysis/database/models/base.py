from sqlalchemy import Column, Integer, DateTime, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class BaseModel(Base):
    """Абстрактная базовая модель с best practices"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    @declared_attr
    def __tablename__(cls):
        """Автоматическое имя таблицы из имени класса"""
        return cls.__name__.lower()

    def to_dict(self):
        """Конвертация в словарь (удобно для JSON API)"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def update(self, **kwargs):
        """Обновление атрибутов модели"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self):
        """Человеко-читаемое представление"""
        attrs = []
        for column in self.__table__.columns:
            if column.primary_key:
                value = getattr(self, column.name)
                attrs.append(f"{column.name}={value}")
        return f"<{self.__class__.__name__}({', '.join(attrs)})>"


class DictionaryModel(BaseModel):
    """Абстрактная модель для справочников"""
    __abstract__ = True

    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255))

    __table_args__ = (
        UniqueConstraint('name', name='uq_{}_name'.format(__tablename__)),
    )

    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}')>"