import logging
from typing import Dict, List

from ..exceptions import CollectionDisabledError, CollectionNotFoundError, InsertError, InvalidVectorDimensionError
from ..logging.logger import log_operation_end, log_operation_error, log_operation_start
from ..models.collection import CollectionModel
from ..models.result import normalize_query_result


class InsertOperation:
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

    def _validate_record(self, model: CollectionModel, record: Dict) -> None:
        if not isinstance(record, dict):
            raise InsertError('Record must be a dictionary.')
        if not model.auto_id and record.get(model.primary_key_field) in (None, ''):
            raise InsertError(f"Primary key field '{model.primary_key_field}' is required.")
        for column in model.columns:
            if column.required and (column.name not in record or record[column.name] is None):
                raise InsertError(f"Field '{column.name}' is required for collection '{model.name}'.")
            if column.type == 'vector' and column.name in record and record[column.name] is not None:
                value = record[column.name]
                if not isinstance(value, (list, tuple)):
                    raise InvalidVectorDimensionError(f"Field '{column.name}' must be a list or tuple of floats.")
                if len(value) != column.dimension:
                    raise InvalidVectorDimensionError(
                        f"Field '{column.name}' expected dimension {column.dimension}, got {len(value)}."
                    )

    def insert(self, collection: str, record: Dict) -> Dict:
        model = self._get_model(collection)
        start_time = log_operation_start(self.logger, 'insert', collection, record=record)
        try:
            self._validate_record(model, record)
            response = self.client_wrapper.get_client().insert(collection_name=collection, data=[record])
            insert_id = None
            if isinstance(response, dict):
                ids = response.get('ids') or response.get('insert_ids') or []
                if ids:
                    insert_id = ids[0]
            if insert_id is None:
                insert_id = record.get(model.primary_key_field)
            result = normalize_query_result({model.primary_key_field: insert_id, **record}, collection)
            log_operation_end(self.logger, 'insert', collection, start_time, result_count=1)
            return result
        except Exception as exc:
            log_operation_error(self.logger, 'insert', collection, start_time, exc)
            if isinstance(exc, (CollectionDisabledError, CollectionNotFoundError, InsertError, InvalidVectorDimensionError)):
                raise
            raise InsertError(str(exc)) from exc

    def bulk_insert(self, collection: str, records: List[Dict]) -> List[Dict]:
        model = self._get_model(collection)
        record_count = len(records) if isinstance(records, list) else None
        start_time = log_operation_start(self.logger, 'bulk_insert', collection, record_count=record_count)
        try:
            if not isinstance(records, list) or not records:
                raise InsertError('records must be a non-empty list.')
            for record in records:
                self._validate_record(model, record)
            response = self.client_wrapper.get_client().insert(collection_name=collection, data=records)
            ids = []
            if isinstance(response, dict):
                ids = response.get('ids') or response.get('insert_ids') or []
            results = []
            for index, record in enumerate(records):
                insert_id = ids[index] if index < len(ids) else record.get(model.primary_key_field)
                results.append(normalize_query_result({model.primary_key_field: insert_id, **record}, collection))
            log_operation_end(self.logger, 'bulk_insert', collection, start_time, result_count=len(results))
            return results
        except Exception as exc:
            log_operation_error(self.logger, 'bulk_insert', collection, start_time, exc)
            if isinstance(exc, (CollectionDisabledError, CollectionNotFoundError, InsertError, InvalidVectorDimensionError)):
                raise
            raise InsertError(str(exc)) from exc
