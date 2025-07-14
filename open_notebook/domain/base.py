from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional, Type, TypeVar, cast

from loguru import logger
from pydantic import BaseModel, ValidationError, field_validator, model_validator

from open_notebook.database.repository import (
    repo_create,
    repo_delete,
    repo_query,
    repo_relate,
    repo_update,
    repo_upsert,
)
from open_notebook.exceptions import (
    DatabaseOperationError,
    InvalidInputError,
    NotFoundError,
)

T = TypeVar("T", bound="ObjectModel")


class ObjectModel(BaseModel):
    id: Optional[str] = None
    table_name: ClassVar[str] = ""
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    @classmethod
    def get_all(cls: Type[T], order_by=None) -> List[T]:
        try:
            # If called from a specific subclass, use its table_name
            if cls.table_name:
                target_class = cls
                table_name = cls.table_name
            else:
                # This path is taken if called directly from ObjectModel
                raise InvalidInputError(
                    "get_all() must be called from a specific model class"
                )

            if order_by:
                order = f" ORDER BY {order_by}"
            else:
                order = ""

            result = repo_query(f"SELECT * FROM {table_name} {order}")
            objects = []
            for obj in result:
                try:
                    objects.append(target_class(**obj))
                except Exception as e:
                    logger.critical(f"Error creating object: {str(e)}")

            return objects
        except Exception as e:
            logger.error(f"Error fetching all {cls.table_name}: {str(e)}")
            logger.exception(e)
            raise DatabaseOperationError(e)

    @classmethod
    def get(cls: Type[T], id: str) -> T:
        if not id:
            raise InvalidInputError("ID cannot be empty")
        try:
            # Get the table name from the ID (everything before the first colon)
            table_name = id.split(":")[0] if ":" in id else id

            # If we're calling from a specific subclass and IDs match, use that class
            if cls.table_name and cls.table_name == table_name:
                target_class: Type[T] = cls
            else:
                # Otherwise, find the appropriate subclass based on table_name
                found_class = cls._get_class_by_table_name(table_name)
                if not found_class:
                    raise InvalidInputError(f"No class found for table {table_name}")
                target_class = cast(Type[T], found_class)

            result = repo_query(f"SELECT * FROM {id}")
            if result:
                return target_class(**result[0])
            else:
                raise NotFoundError(f"{table_name} with id {id} not found")
        except Exception as e:
            logger.error(f"Error fetching {cls.table_name} with id {id}: {str(e)}")
            logger.exception(e)
            raise DatabaseOperationError(e)

    @classmethod
    def _get_class_by_table_name(cls, table_name: str) -> Optional[Type["ObjectModel"]]:
        """Find the appropriate subclass based on table_name."""
        for subclass in cls.__subclasses__():
            if hasattr(subclass, 'table_name') and subclass.table_name == table_name:
                return subclass
            # Recursively check subclasses
            found = subclass._get_class_by_table_name(table_name)
            if found:
                return found
        return None

    def needs_embedding(self) -> bool:
        return hasattr(self, 'full_text') and getattr(self, 'full_text') is not None

    def get_embedding_content(self) -> Optional[str]:
        if hasattr(self, 'full_text'):
            return getattr(self, 'full_text')
        return None

    def save(self) -> None:
        try:
            now = datetime.now()
            
            if not self.id:
                self.created = now
                self.updated = now
                data = self._prepare_save_data()
                result = repo_create(self.table_name, data)
                if result:
                    self.id = result[0]["id"]
            else:
                self.updated = now
                data = self._prepare_save_data()
                repo_update(self.id, data)
        except Exception as e:
            logger.error(f"Error saving {self.table_name}: {str(e)}")
            logger.exception(e)
            raise DatabaseOperationError(e)

    def _prepare_save_data(self) -> Dict[str, Any]:
        data = self.model_dump(exclude={"id"})
        return data

    def delete(self) -> bool:
        if not self.id:
            raise InvalidInputError("Cannot delete object without ID")
        try:
            repo_delete(self.id)
            return True
        except Exception as e:
            logger.error(f"Error deleting {self.table_name} with id {self.id}: {str(e)}")
            logger.exception(e)
            raise DatabaseOperationError(e)

    def relate(
        self, relationship: str, target_id: str, data: Optional[Dict] = {}
    ) -> Any:
        if not relationship or not target_id or not self.id:
            raise InvalidInputError("Relationship and target ID must be provided")
        try:
            return repo_relate(
                source=self.id, relationship=relationship, target=target_id, data=data
            )
        except Exception as e:
            logger.error(f"Error creating relationship: {str(e)}")
            logger.exception(e)
            raise DatabaseOperationError(e)

    @field_validator("created", "updated", mode="before")
    @classmethod
    def parse_datetime(cls, value):
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value


class RecordModel(BaseModel):
    """Base class for singleton records like settings."""
    record_id: ClassVar[str] = ""
    
    def save(self) -> None:
        try:
            data = self.model_dump()
            repo_upsert(self.record_id, data)
        except Exception as e:
            logger.error(f"Error saving record {self.record_id}: {str(e)}")
            logger.exception(e)
            raise DatabaseOperationError(e)
    
    def update(self) -> None:
        self.save()
    
    @classmethod
    def load(cls):
        try:
            result = repo_query(f"SELECT * FROM {cls.record_id}")
            if result:
                return cls(**result[0])
            else:
                return cls()
        except Exception as e:
            logger.warning(f"Could not load record {cls.record_id}, using defaults: {str(e)}")
            return cls()
