import logging
from typing import List

from ..exceptions import CollectionAlreadyExistsError, CollectionNotFoundError
from ..models.collection import CollectionModel
from .client import MilvusClientWrapper
from .schema import build_schema


class CollectionManager:
    def __init__(self, client_wrapper: MilvusClientWrapper, logger: logging.Logger):
        self.client_wrapper = client_wrapper
        self.logger = logger

    def create_collection(self, model: CollectionModel) -> None:
        if self.collection_exists(model.name):
            raise CollectionAlreadyExistsError(f"Collection '{model.name}' already exists.")
        client = self.client_wrapper.get_client()
        client.create_collection(collection_name=model.name, schema=build_schema(model))

    def drop_collection(self, name: str) -> None:
        if not self.collection_exists(name):
            raise CollectionNotFoundError(f"Collection '{name}' does not exist.")
        self.client_wrapper.get_client().drop_collection(collection_name=name)

    def collection_exists(self, name: str) -> bool:
        client = self.client_wrapper.get_client()
        if hasattr(client, 'has_collection'):
            return bool(client.has_collection(collection_name=name))
        if hasattr(client, 'list_collections'):
            return name in list(client.list_collections())
        return False

    def list_collections(self) -> List[str]:
        client = self.client_wrapper.get_client()
        if hasattr(client, 'list_collections'):
            return list(client.list_collections())
        return []

    def describe_collection(self, name: str) -> dict:
        if not self.collection_exists(name):
            raise CollectionNotFoundError(f"Collection '{name}' does not exist.")
        return self.client_wrapper.get_client().describe_collection(collection_name=name)

    def load_collection(self, name: str) -> None:
        if not self.collection_exists(name):
            raise CollectionNotFoundError(f"Collection '{name}' does not exist.")
        self.client_wrapper.get_client().load_collection(collection_name=name)

    def reset_collection(self, model: CollectionModel) -> None:
        if self.collection_exists(model.name):
            self.drop_collection(model.name)
        self.create_collection(model)
