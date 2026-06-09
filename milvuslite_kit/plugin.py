from typing import Dict, List, Optional

from .config.loader import load_config
from .config.validator import validate_config
from .core.client import MilvusClientWrapper
from .core.collections import CollectionManager
from .core.indexes import IndexManager
from .core.schema import build_collection_model
from .exceptions import CollectionNotFoundError, InvalidSchemaError
from .logging.logger import setup_logger
from .operations.delete import DeleteOperation
from .operations.insert import InsertOperation
from .operations.query import QueryOperation
from .operations.search import SearchOperation


class MilvusLiteKit:
    def __init__(self, config: Dict):
        validate_config(config)
        self.config = config
        self.defaults = config.get('defaults', {}) or {}
        self.logger = setup_logger(config)
        self.collection_models = {
            name: build_collection_model(name, coll_cfg)
            for name, coll_cfg in (config.get('collections') or {}).items()
        }
        self.client_wrapper = MilvusClientWrapper(config['database']['path'], self.logger)
        self.collection_manager = CollectionManager(self.client_wrapper, self.logger)
        self.index_manager = IndexManager(self.client_wrapper, self.logger)
        self.insert_operation = InsertOperation(self.client_wrapper, self.logger, self.collection_models)
        self.query_operation = QueryOperation(self.client_wrapper, self.logger, self.collection_models)
        self.search_operation = SearchOperation(self.client_wrapper, self.logger, self.collection_models)
        self.delete_operation = DeleteOperation(self.client_wrapper, self.logger, self.collection_models)

    def close(self) -> None:
        """Close the underlying MilvusClient connection."""
        client = self.client_wrapper._client
        if client is not None and hasattr(client, 'close'):
            client.close()
        self.client_wrapper._client = None

    def __enter__(self) -> 'MilvusLiteKit':
        return self

    def __exit__(self, *_) -> None:
        self.close()

    @classmethod
    def from_yaml(cls, path: str) -> 'MilvusLiteKit':
        """Load plugin from YAML config file."""
        return cls(load_config(path))

    def sync_schema(self) -> None:
        """Create or update all enabled collections and their indexes."""
        auto_create_collection = bool(self.defaults.get('auto_create_collection', True))
        auto_create_index = bool(self.defaults.get('auto_create_index', True))
        auto_load_collection = bool(self.defaults.get('auto_load_collection', True))
        default_metric = self.defaults.get('default_metric_type', 'COSINE')
        default_index = self.defaults.get('default_index_type', 'FLAT')

        for model in self.collection_models.values():
            if not model.enabled:
                continue
            exists = self.collection_manager.collection_exists(model.name)
            if auto_create_collection and not exists:
                self.collection_manager.create_collection(model)
                exists = True
            if not exists:
                continue
            if auto_create_index:
                for column in model.columns:
                    if column.type != 'vector' or not column.index_enabled:
                        continue
                    self.index_manager.create_index(
                        collection_name=model.name,
                        field_name=column.name,
                        index_type=column.index_type or default_index,
                        metric_type=column.metric_type or default_metric,
                        params=column.index_params or {},
                    )
            if auto_load_collection:
                self.collection_manager.load_collection(model.name)

    def validate_schema(self) -> None:
        """Validate all enabled collection schemas against config."""
        for model in self.collection_models.values():
            if not model.enabled:
                continue
            if not self.collection_manager.collection_exists(model.name):
                raise InvalidSchemaError(f"Collection '{model.name}' does not exist.")
            description = self.collection_manager.describe_collection(model.name)
            fields = self._extract_fields(description)
            if not fields:
                continue
            field_map = {self._field_name(field): field for field in fields if self._field_name(field)}
            expected_names = {model.primary_key_field, *(column.name for column in model.columns)}
            missing = sorted(expected_names - set(field_map))
            if missing:
                raise InvalidSchemaError(f"Collection '{model.name}' is missing fields: {', '.join(missing)}")
            for column in model.columns:
                if column.type != 'vector':
                    continue
                actual_dim = self._field_dim(field_map[column.name])
                if actual_dim is not None and actual_dim != column.dimension:
                    raise InvalidSchemaError(
                        f"Collection '{model.name}' vector field '{column.name}' has dim {actual_dim}, expected {column.dimension}."
                    )

    def list_collections(self) -> List[str]:
        """List all collections in the database."""
        return self.collection_manager.list_collections()

    def describe_collection(self, collection: str) -> dict:
        """Return metadata for a collection."""
        return self.collection_manager.describe_collection(collection)

    def collection_exists(self, collection: str) -> bool:
        """Check if a collection exists."""
        return self.collection_manager.collection_exists(collection)

    def drop_collection(self, collection: str) -> None:
        """Drop a collection."""
        self.collection_manager.drop_collection(collection)

    def reset_collection(self, collection: str) -> None:
        """Drop and recreate a collection."""
        model = self.collection_models.get(collection)
        if model is None:
            raise CollectionNotFoundError(f"Collection '{collection}' is not defined.")
        self.collection_manager.reset_collection(model)

    def insert(self, collection: str, record: dict) -> dict:
        """Insert a single record."""
        return self.insert_operation.insert(collection, record)

    def bulk_insert(self, collection: str, records: List[dict]) -> List[dict]:
        """Insert multiple records."""
        return self.insert_operation.bulk_insert(collection, records)

    def query(self, collection: str, filters: dict, output_fields: List[str]) -> List[dict]:
        """Query records by filter."""
        return self.query_operation.query(collection, filters, output_fields)

    def search(
        self,
        collection: str,
        vector: List[float],
        vector_column: str,
        limit: int = 10,
        filters: Optional[dict] = None,
        output_fields: Optional[List[str]] = None,
    ) -> List[dict]:
        """Semantic vector search."""
        return self.search_operation.search(collection, vector, vector_column, limit, filters or {}, output_fields or [])

    def delete(self, collection: str, filters: dict) -> int:
        """Delete records by filter."""
        return self.delete_operation.delete(collection, filters)

    @staticmethod
    def _extract_fields(description) -> List:
        if isinstance(description, dict):
            if isinstance(description.get('fields'), list):
                return description['fields']
            schema = description.get('schema')
            if isinstance(schema, dict) and isinstance(schema.get('fields'), list):
                return schema['fields']
            if hasattr(schema, 'fields'):
                return list(schema.fields)
        if hasattr(description, 'fields'):
            return list(description.fields)
        return []

    @staticmethod
    def _field_name(field) -> Optional[str]:
        if isinstance(field, dict):
            return field.get('name') or field.get('field_name')
        return getattr(field, 'name', None) or getattr(field, 'field_name', None)

    @staticmethod
    def _field_dim(field) -> Optional[int]:
        if isinstance(field, dict):
            return field.get('dim') or ((field.get('params') or {}).get('dim'))
        return getattr(field, 'dim', None)
