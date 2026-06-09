from typing import Dict, Iterable

from ..exceptions import ConfigValidationError

SUPPORTED_COLUMN_TYPES = {'text', 'int', 'float', 'bool', 'json', 'vector'}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ConfigValidationError(message)


def _iter_enabled_collections(collections: Dict) -> Iterable:
    for name, coll_cfg in (collections or {}).items():
        if not isinstance(coll_cfg, dict):
            raise ConfigValidationError(f"Collection '{name}' configuration must be a mapping.")
        if coll_cfg.get('enabled', True):
            yield name, coll_cfg


def validate_config(config: Dict) -> None:
    """Validate plugin configuration and raise ConfigValidationError on failure."""
    _require(isinstance(config, dict), 'Configuration must be a mapping.')

    database_cfg = config.get('database') or {}
    db_path = database_cfg.get('path')
    _require(isinstance(db_path, str) and db_path.strip(), 'database.path is required and must be non-empty.')

    collections_cfg = config.get('collections') or {}
    _require(isinstance(collections_cfg, dict), 'collections must be a mapping.')

    for name, coll_cfg in _iter_enabled_collections(collections_cfg):
        primary_key = coll_cfg.get('primary_key')
        _require(isinstance(primary_key, dict), f"Collection '{name}' must define a primary_key mapping.")
        pk_field = primary_key.get('field')
        _require(isinstance(pk_field, str) and pk_field.strip(), f"Collection '{name}' must define primary_key.field.")

        columns = coll_cfg.get('columns') or []
        _require(isinstance(columns, list), f"Collection '{name}' columns must be a list.")

        seen_names = {pk_field}
        for column in columns:
            _require(isinstance(column, dict), f"Collection '{name}' has a column entry that is not a mapping.")
            col_name = column.get('name')
            _require(isinstance(col_name, str) and col_name.strip(), f"Collection '{name}' contains a column without a valid name.")
            if col_name in seen_names:
                raise ConfigValidationError(f"Collection '{name}' contains duplicate column name '{col_name}'.")
            seen_names.add(col_name)

            col_type = column.get('type')
            if col_type not in SUPPORTED_COLUMN_TYPES:
                raise ConfigValidationError(
                    f"Collection '{name}' column '{col_name}' has unsupported type '{col_type}'."
                )
            if col_type == 'vector':
                dimension = column.get('dimension')
                if not isinstance(dimension, int) or dimension <= 0:
                    raise ConfigValidationError(
                        f"Collection '{name}' column '{col_name}' must define a positive integer dimension."
                    )
