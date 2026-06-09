import logging

from ._milvus import IndexParams
from .client import MilvusClientWrapper


class IndexManager:
    def __init__(self, client_wrapper: MilvusClientWrapper, logger: logging.Logger):
        self.client_wrapper = client_wrapper
        self.logger = logger

    def create_index(
        self,
        collection_name: str,
        field_name: str,
        index_type: str,
        metric_type: str,
        params: dict,
    ) -> None:
        client = self.client_wrapper.get_client()
        if self.index_exists(collection_name, field_name):
            return
        index_params = IndexParams()
        index_params.add_index(
            field_name=field_name,
            index_type=index_type,
            metric_type=metric_type,
            params=params or {},
        )
        client.create_index(
            collection_name=collection_name,
            index_params=index_params,
        )

    def index_exists(self, collection_name: str, field_name: str) -> bool:
        client = self.client_wrapper.get_client()
        try:
            if hasattr(client, 'list_indexes'):
                return field_name in list(client.list_indexes(collection_name=collection_name))
            if hasattr(client, 'describe_index'):
                return bool(client.describe_index(collection_name=collection_name, field_name=field_name))
        except Exception:
            return False
        return False
