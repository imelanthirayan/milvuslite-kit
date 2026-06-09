import logging
from typing import Dict, List

from ..exceptions import CollectionDisabledError, CollectionNotFoundError, QueryError
from ..logging.logger import log_operation_end, log_operation_error, log_operation_start
from ..models.collection import CollectionModel
from ..models.result import normalize_query_result

OPERATOR_MAPPING = {
    'eq': '==',
    'ne': '!=',
    'gt': '>',
    'gte': '>=',
    'lt': '<',
    'lte': '<=',
}


def _format_filter_value(value):
    if isinstance(value, str):
        escaped = value.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (int, float)):
        return str(value)
    raise QueryError(f'Unsupported filter value type: {type(value).__name__}')


def build_filter_expr(filters: Dict) -> str:
    if not filters:
        return ''
    if not isinstance(filters, dict):
        raise QueryError('filters must be a dictionary.')

    clauses = []
    for field, condition in filters.items():
        if not isinstance(condition, dict):
            condition = {'eq': condition}
        if len(condition) != 1:
            raise QueryError(f"Filter for field '{field}' must contain exactly one operator.")
        operator, value = next(iter(condition.items()))
        if operator == 'in':
            if not isinstance(value, (list, tuple, set)) or not value:
                raise QueryError(f"Filter operator 'in' for field '{field}' requires a non-empty list.")
            formatted = ', '.join(_format_filter_value(item) for item in value)
            clauses.append(f'{field} in [{formatted}]')
            continue
        symbol = OPERATOR_MAPPING.get(operator)
        if symbol is None:
            raise QueryError(f"Unsupported operator '{operator}' for field '{field}'.")
        clauses.append(f'{field} {symbol} {_format_filter_value(value)}')
    return ' && '.join(clauses)


class QueryOperation:
    def __init__(self, client_wrapper, logger: logging.Logger, collection_models: Dict[str, CollectionModel]):
        self.client_wrapper = client_wrapper
        self.logger = logger
        self.collection_models = collection_models

    def _get_model(self, collection: str) -> CollectionModel:
        model = self.collection_models.get(collection)
        if model is None:
            raise CollectionNotFoundError(f"Collection '{collection}' is not defined.")
        if not model.enabled:
            raise CollectionDisabledError(f"Collection '{collection}' is disabled.")
        return model

    def query(self, collection: str, filters: Dict, output_fields: List[str]) -> List[Dict]:
        self._get_model(collection)
        start_time = log_operation_start(self.logger, 'query', collection, filters=filters)
        try:
            response = self.client_wrapper.get_client().query(
                collection_name=collection,
                filter=build_filter_expr(filters) or None,
                output_fields=output_fields or None,
            )
            results = [normalize_query_result(record, collection) for record in (response or [])]
            log_operation_end(self.logger, 'query', collection, start_time, result_count=len(results))
            return results
        except Exception as exc:
            log_operation_error(self.logger, 'query', collection, start_time, exc)
            if isinstance(exc, (CollectionDisabledError, CollectionNotFoundError, QueryError)):
                raise
            raise QueryError(str(exc)) from exc
