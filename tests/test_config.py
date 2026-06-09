import textwrap

import pytest

from milvuslite_kit.config.loader import load_config
from milvuslite_kit.config.validator import validate_config
from milvuslite_kit.exceptions import ConfigValidationError


@pytest.fixture
def valid_config():
    return {
        'database': {'name': 'db', 'path': './data/vector.db'},
        'collections': {
            'documents': {
                'enabled': True,
                'primary_key': {'field': 'id', 'auto_id': True},
                'columns': [
                    {'name': 'title', 'type': 'text', 'required': True},
                    {'name': 'embedding', 'type': 'vector', 'required': True, 'dimension': 4},
                ],
            }
        },
    }


def test_load_config(tmp_path, valid_config):
    config_path = tmp_path / 'config.yaml'
    config_path.write_text(
        textwrap.dedent(
            '''
            database:
              path: ./data/vector.db
            collections:
              documents:
                enabled: true
                primary_key:
                  field: id
                  auto_id: true
                columns:
                  - name: title
                    type: text
                    required: true
                  - name: embedding
                    type: vector
                    required: true
                    dimension: 4
            '''
        ).strip(),
        encoding='utf-8',
    )

    loaded = load_config(str(config_path))
    assert loaded['database']['path'] == './data/vector.db'
    assert loaded['collections']['documents']['columns'][1]['dimension'] == 4


def test_validate_config_accepts_valid_config(valid_config):
    validate_config(valid_config)


def test_validate_config_requires_database_path(valid_config):
    valid_config['database']['path'] = ''
    with pytest.raises(ConfigValidationError, match='database.path'):
        validate_config(valid_config)


def test_validate_config_requires_primary_key(valid_config):
    del valid_config['collections']['documents']['primary_key']
    with pytest.raises(ConfigValidationError, match='primary_key'):
        validate_config(valid_config)


def test_validate_config_rejects_duplicate_columns(valid_config):
    valid_config['collections']['documents']['columns'].append({'name': 'title', 'type': 'text'})
    with pytest.raises(ConfigValidationError, match='duplicate column name'):
        validate_config(valid_config)


def test_validate_config_requires_vector_dimension(valid_config):
    del valid_config['collections']['documents']['columns'][1]['dimension']
    with pytest.raises(ConfigValidationError, match='dimension'):
        validate_config(valid_config)


def test_validate_config_skips_disabled_collection(valid_config):
    valid_config['collections']['archived'] = {
        'enabled': False,
        'columns': [{'name': 'bad', 'type': 'vector'}],
    }
    validate_config(valid_config)
