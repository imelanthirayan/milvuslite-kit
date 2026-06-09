from unittest.mock import Mock

import pytest

from milvuslite_kit.exceptions import CollectionDisabledError
from milvuslite_kit.models.collection import CollectionModel
from milvuslite_kit.models.column import ColumnModel
from milvuslite_kit.operations.query import QueryOperation, build_filter_expr


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
            columns=[ColumnModel('department', 'text', False, None, None, False, None, {}, '', '')],
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


def test_build_filter_expr_with_all_operators():
    filters = {
        'department': {'eq': 'Finance'},
        'country': {'ne': 'US'},
        'age': {'gt': 25},
        'min_age': {'gte': 18},
        'score': {'lt': 99.5},
        'rating': {'lte': 5},
        'status': {'in': ['draft', 'published']},
        'active': {'eq': True},
    }
    expr = build_filter_expr(filters)
    assert expr == (
        'department == "Finance" && country != "US" && age > 25 && min_age >= 18 && '
        'score < 99.5 && rating <= 5 && status in ["draft", "published"] && active == true'
    )


def test_query_returns_normalized_results(collection_models):
    client = Mock()
    client.query.return_value = [{'id': 1, 'department': 'Finance', 'title': 'Budget'}]
    wrapper = Mock(get_client=Mock(return_value=client))
    operation = QueryOperation(wrapper, Mock(), collection_models)

    result = operation.query('documents', {'department': {'eq': 'Finance'}}, ['department', 'title'])

    client.query.assert_called_once_with(
        collection_name='documents',
        filter='department == "Finance"',
        output_fields=['department', 'title'],
    )
    assert result == [{'id': '1', 'collection': 'documents', 'data': {'department': 'Finance', 'title': 'Budget'}}]


def test_querying_disabled_collection_raises(collection_models):
    operation = QueryOperation(Mock(), Mock(), collection_models)
    with pytest.raises(CollectionDisabledError):
        operation.query('archived', {'department': {'eq': 'Finance'}}, ['department'])
