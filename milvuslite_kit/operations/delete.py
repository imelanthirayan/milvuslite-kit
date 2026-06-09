import logging
from typing import Dict

from ..exceptions import CollectionDisabledError, CollectionNotFoundError, DeleteError
from ..logging.logger import log_operation_end, log_operation_error, log_operation_start
from ..models.collection import CollectionModel
from .query import build_filter_expr


class DeleteOperation:
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

    def delete(self, collection: str, filters: Dict) -> int:
        self._get_model(collection)
        start_time = log_operation_start(self.logger, 'delete', collection, filters=filters)
        try:
            filter_expr = build_filter_expr(filters)
            if not filter_expr:
                raise DeleteError('Delete requires at least one filter condition.')
            response = self.client_wrapper.get_client().delete(collection_name=collection, filter=filter_expr)
            if isinstance(response, dict):
                count = response.get('delete_count')
                if count is None:
                    count = len(response.get('primary_keys') or [])
            elif isinstance(response, int):
                count = response
            else:
                count = 0
            log_operation_end(self.logger, 'delete', collection, start_time, result_count=count)
            return int(count)
        except Exception as exc:
            log_operation_error(self.logger, 'delete', collection, start_time, exc)
            if isinstance(exc, (CollectionDisabledError, CollectionNotFoundError, DeleteError)):
                raise
            raise DeleteError(str(exc)) from exc
