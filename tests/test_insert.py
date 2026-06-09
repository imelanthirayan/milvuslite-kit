from unittest.mock import Mock

import pytest

from milvuslite_kit.exceptions import CollectionDisabledError, InsertError, InvalidVectorDimensionError
from milvuslite_kit.models.collection import CollectionModel
from milvuslite_kit.models.column import ColumnModel
from milvuslite_kit.operations.insert import InsertOperation


@pytest.fixture
def collection_models():
    enabled = CollectionModel(
        name='documents',
        enabled=True,
        description='',
        agent_usage='',
        primary_key_field='id',
        auto_id=True,
        columns=[
            ColumnModel('title', 'text', True, None, None, False, None, {}, '', ''),
            ColumnModel('embedding', 'vector', True, 4, 'COSINE', True, 'FLAT', {}, '', ''),
        ],
    )
    disabled = CollectionModel(
        name='archived',
        enabled=False,
        description='',
        agent_usage='',
        primary_key_field='id',
        auto_id=True,
        columns=[],
    )
    return {'documents': enabled, 'archived': disabled}


@pytest.fixture
def insert_operation(collection_models):
    client = Mock()
    client.insert.return_value = {'ids': [101]}
    wrapper = Mock()
    wrapper.get_client.return_value = client
    logger = Mock()
    return InsertOperation(wrapper, logger, collection_models), client


def test_valid_insert_succeeds(insert_operation):
    operation, client = insert_operation
    result = operation.insert('documents', {'title': 'Doc', 'embedding': [0.1, 0.2, 0.3, 0.4]})
    client.insert.assert_called_once_with(collection_name='documents', data=[{'title': 'Doc', 'embedding': [0.1, 0.2, 0.3, 0.4]}])
    assert result['id'] == '101'
    assert result['collection'] == 'documents'


def test_insert_requires_required_field(insert_operation):
    operation, _ = insert_operation
    with pytest.raises(InsertError, match='title'):
        operation.insert('documents', {'embedding': [0.1, 0.2, 0.3, 0.4]})


def test_insert_rejects_wrong_vector_dimension(insert_operation):
    operation, _ = insert_operation
    with pytest.raises(InvalidVectorDimensionError, match='expected dimension 4'):
        operation.insert('documents', {'title': 'Doc', 'embedding': [0.1, 0.2]})


def test_insert_rejects_disabled_collection(insert_operation):
    operation, _ = insert_operation
    with pytest.raises(CollectionDisabledError):
        operation.insert('archived', {'title': 'Doc'})
