from typing import Dict, List

from ..models.collection import CollectionModel
from ..models.column import ColumnModel
from ._milvus import CollectionSchema, DataType, FieldSchema

TYPE_MAPPING = {
    'text': DataType.VARCHAR,
    'int': DataType.INT64,
    'float': DataType.FLOAT,
    'bool': DataType.BOOL,
    'json': DataType.JSON,
    'vector': DataType.FLOAT_VECTOR,
}


def build_collection_model(name: str, coll_cfg: Dict) -> CollectionModel:
    primary_key_cfg = coll_cfg.get('primary_key') or {}
    columns: List[ColumnModel] = []
    for column_cfg in coll_cfg.get('columns', []):
        index_cfg = column_cfg.get('index') or {}
        columns.append(
            ColumnModel(
                name=column_cfg['name'],
                type=column_cfg['type'],
                required=bool(column_cfg.get('required', False)),
                dimension=column_cfg.get('dimension'),
                metric_type=column_cfg.get('metric_type'),
                index_enabled=bool(index_cfg.get('enabled', False)),
                index_type=index_cfg.get('type'),
                index_params=index_cfg.get('params') or {},
                description=column_cfg.get('description', ''),
                agent_usage=column_cfg.get('agent_usage', ''),
            )
        )

    return CollectionModel(
        name=name,
        enabled=bool(coll_cfg.get('enabled', True)),
        description=coll_cfg.get('description', ''),
        agent_usage=coll_cfg.get('agent_usage', ''),
        primary_key_field=primary_key_cfg.get('field', 'id'),
        auto_id=bool(primary_key_cfg.get('auto_id', False)),
        columns=columns,
    )


def build_schema(collection: CollectionModel) -> CollectionSchema:
    fields = []
    if collection.auto_id:
        fields.append(
            FieldSchema(
                name=collection.primary_key_field,
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True,
                description='Primary key',
            )
        )
    else:
        fields.append(
            FieldSchema(
                name=collection.primary_key_field,
                dtype=DataType.VARCHAR,
                is_primary=True,
                auto_id=False,
                max_length=255,
                description='Primary key',
            )
        )

    for column in collection.columns:
        common_kwargs = {'name': column.name, 'dtype': TYPE_MAPPING[column.type], 'description': column.description}
        if column.type == 'text':
            fields.append(FieldSchema(max_length=65535, **common_kwargs))
        elif column.type == 'vector':
            fields.append(FieldSchema(dim=column.dimension, **common_kwargs))
        else:
            fields.append(FieldSchema(**common_kwargs))

    return CollectionSchema(fields=fields, description=collection.description, enable_dynamic_field=False)
