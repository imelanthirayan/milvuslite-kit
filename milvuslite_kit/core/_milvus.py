from enum import Enum

try:
    from pymilvus import CollectionSchema, DataType, FieldSchema, MilvusClient
    from pymilvus.milvus_client import IndexParams
except ImportError:  # pragma: no cover - exercised indirectly in tests
    class DataType(Enum):
        VARCHAR = 'VARCHAR'
        INT64 = 'INT64'
        FLOAT = 'FLOAT'
        BOOL = 'BOOL'
        JSON = 'JSON'
        FLOAT_VECTOR = 'FLOAT_VECTOR'


    class FieldSchema:
        def __init__(self, name, dtype, **kwargs):
            self.name = name
            self.dtype = dtype
            self.is_primary = kwargs.get('is_primary', False)
            self.auto_id = kwargs.get('auto_id', False)
            self.description = kwargs.get('description', '')
            self.max_length = kwargs.get('max_length')
            self.dim = kwargs.get('dim')
            self.kwargs = dict(kwargs)


    class CollectionSchema:
        def __init__(self, fields, description='', **kwargs):
            self.fields = fields
            self.description = description
            self.kwargs = dict(kwargs)


    class IndexParams:
        def __init__(self):
            self._indexes = []

        def add_index(self, field_name, index_type, metric_type, params=None):
            self._indexes.append({
                'field_name': field_name,
                'index_type': index_type,
                'metric_type': metric_type,
                'params': params or {},
            })


    class MilvusClient:
        def __init__(self, *args, **kwargs):
            raise RuntimeError(
                'pymilvus is not installed. Install project dependencies to use MilvusClient directly.'
            )


__all__ = ['MilvusClient', 'DataType', 'CollectionSchema', 'FieldSchema', 'IndexParams']
