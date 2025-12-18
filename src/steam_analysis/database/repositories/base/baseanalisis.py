from typing import TypeVar

from steam_analysis.database.models.analysisbase import AnalysisBase as BaseAnalysisModel
from pydantic import BaseModel

from steam_analysis.database.repositories.base.base import BaseDBRepository

ModelType = TypeVar("ModelType", bound=BaseAnalysisModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseAnalysisRepository(BaseDBRepository[ModelType, CreateSchemaType, UpdateSchemaType]):
    pass
