import logging
from pathlib import Path

from ._milvus import MilvusClient


class MilvusClientWrapper:
    def __init__(self, db_path: str, logger: logging.Logger):
        self.db_path = db_path
        self.logger = logger
        self._client = None

    def get_client(self) -> MilvusClient:
        if self._client is None:
            db_file = Path(self.db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)
            self.logger.debug('Initializing MilvusClient for %s', self.db_path)
            self._client = MilvusClient(uri=self.db_path)
        return self._client
