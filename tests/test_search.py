from unittest.mock import Mock

import pytest

from milvuslite_kit.exceptions import CollectionDisabledError, InvalidVectorDimensionError
from milvuslite_kit.models.collection import CollectionModel
from milvuslite_kit.models.column import ColumnModel
from milvuslite_kit.operations.search import SearchOperation


@pytest.fixture
def collection_models():
    return {
        'documents': CollectionModel(
            name='documents',
            enabled=True,
            description='',
            agent_usage='',
            primary_key_field='id',
            auto_id=True,
            columns=[
                ColumnModel('embedding', 'vector', True, 4, 'COSINE', True, 'FLAT', {}, '', ''),
                ColumnModel('title', 'text', True, None, None, False, None, {}, '', ''),
            ],
        ),
        'archived': CollectionModel(
            name='archived',
            enabled=False,
            description='',
            agent_usage='',
            primary_key_field='id',
            auto_id=True,
            columns=[],
        ),
    }


def test_search_returns_normalized_results(collection_models):
    client = Mock()
    client.search.return_value = [[{'id': 1, 'distance': 0.12, 'title': 'Budget'}]]
    wrapper = Mock(get_client=Mock(return_value=client))
    operation = SearchOperation(wrapper, Mock(), collection_models)

    result = operation.search('documents', [0.1, 0.2, 0.3, 0.4], 'embedding', 2, {}, ['title'])

    client.search.assert_called_once_with(
        collection_name='documents',
        data=[[0.1, 0.2, 0.3, 0.4]],
        anns_field='embedding',
        limit=2,
        filter=None,
        output_fields=['title'],
    )
    assert result == [{'id': '1', 'score': 0.12, 'collection': 'documents', 'data': {'title': 'Budget'}}]


def test_search_rejects_wrong_vector_dimension(collection_models):
    operation = SearchOperation(Mock(), Mock(), collection_models)
    with pytest.raises(InvalidVectorDimensionError, match='expected dimension 4'):
        operation.search('documents', [0.1, 0.2], 'embedding', 2, {}, ['title'])


def test_searching_disabled_collection_raises(collection_models):
    operation = SearchOperation(Mock(), Mock(), collection_models)
    with pytest.raises(CollectionDisabledError):
        operation.search('archived', [0.1, 0.2, 0.3, 0.4], 'embedding', 2, {}, ['title'])
