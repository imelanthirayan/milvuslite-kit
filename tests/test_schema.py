from milvuslite_kit.core._milvus import DataType
from milvuslite_kit.core.schema import build_collection_model, build_schema


COLLECTION_CONFIG = {
    'enabled': True,
    'description': 'test collection',
    'primary_key': {'field': 'id', 'auto_id': True},
    'columns': [
        {'name': 'title', 'type': 'text', 'required': True},
        {'name': 'age', 'type': 'int'},
        {'name': 'score', 'type': 'float'},
        {'name': 'active', 'type': 'bool'},
        {'name': 'meta', 'type': 'json'},
        {'name': 'embedding', 'type': 'vector', 'dimension': 8},
    ],
}


def test_build_collection_model():
    model = build_collection_model('documents', COLLECTION_CONFIG)
    assert model.name == 'documents'
    assert model.primary_key_field == 'id'
    assert model.auto_id is True
    assert len(model.columns) == 6
    assert model.columns[-1].dimension == 8


def test_build_schema_maps_column_types_correctly():
    model = build_collection_model('documents', COLLECTION_CONFIG)
    schema = build_schema(model)
    fields = {field.name: field for field in schema.fields}

    assert fields['id'].is_primary is True
    assert fields['id'].dtype == DataType.INT64
    assert fields['title'].dtype == DataType.VARCHAR
    assert fields['age'].dtype == DataType.INT64
    assert fields['score'].dtype == DataType.FLOAT
    assert fields['active'].dtype == DataType.BOOL
    assert fields['meta'].dtype == DataType.JSON
    assert fields['embedding'].dtype == DataType.FLOAT_VECTOR
    assert getattr(fields['embedding'], 'dim', None) == 8
