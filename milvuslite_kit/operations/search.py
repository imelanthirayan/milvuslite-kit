import logging
from typing import Dict, List

from ..exceptions import CollectionDisabledError, CollectionNotFoundError, InvalidVectorDimensionError, SearchError
from ..logging.logger import log_operation_end, log_operation_error, log_operation_start
from ..models.collection import CollectionModel
from ..models.result import normalize_search_result
from .query import build_filter_expr


class SearchOperation:
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

    def search(
        self,
        collection: str,
        vector: List[float],
        vector_column: str,
        limit: int,
        filters: Dict,
        output_fields: List[str],
    ) -> List[Dict]:
        model = self._get_model(collection)
        start_time = log_operation_start(self.logger, 'search', collection, vector=vector, limit=limit)
        try:
            column = next((item for item in model.columns if item.name == vector_column), None)
            if column is None or column.type != 'vector':
                raise SearchError(f"Field '{vector_column}' is not a configured vector column for '{collection}'.")
            if not isinstance(vector, (list, tuple)):
                raise InvalidVectorDimensionError('Search vector must be a list or tuple of floats.')
            if len(vector) != column.dimension:
                raise InvalidVectorDimensionError(
                    f"Field '{vector_column}' expected dimension {column.dimension}, got {len(vector)}."
                )
            response = self.client_wrapper.get_client().search(
                collection_name=collection,
                data=[list(vector)],
                anns_field=vector_column,
                limit=limit,
                filter=build_filter_expr(filters) or None,
                output_fields=output_fields or None,
            )
            hits = response[0] if response and isinstance(response[0], list) else (response or [])
            results = [normalize_search_result(hit, collection) for hit in hits]
            log_operation_end(self.logger, 'search', collection, start_time, result_count=len(results))
            return results
        except Exception as exc:
            log_operation_error(self.logger, 'search', collection, start_time, exc)
            if isinstance(exc, (CollectionDisabledError, CollectionNotFoundError, InvalidVectorDimensionError, SearchError)):
                raise
            raise SearchError(str(exc)) from exc
