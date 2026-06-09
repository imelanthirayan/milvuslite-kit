from unittest.mock import Mock

import pytest

from milvuslite_kit.exceptions import CollectionDisabledError
from milvuslite_kit.models.collection import CollectionModel
from milvuslite_kit.models.column import ColumnModel
from milvuslite_kit.operations.delete import DeleteOperation


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


def test_delete_calls_client_with_correct_filter(collection_models):
    client = Mock()
    client.delete.return_value = {'delete_count': 3}
    wrapper = Mock(get_client=Mock(return_value=client))
    operation = DeleteOperation(wrapper, Mock(), collection_models)

    deleted = operation.delete('documents', {'department': {'eq': 'Finance'}})

    client.delete.assert_called_once_with(collection_name='documents', filter='department == "Finance"')
    assert deleted == 3


def test_deleting_from_disabled_collection_raises(collection_models):
    operation = DeleteOperation(Mock(), Mock(), collection_models)
    with pytest.raises(CollectionDisabledError):
        operation.delete('archived', {'department': {'eq': 'Finance'}})
