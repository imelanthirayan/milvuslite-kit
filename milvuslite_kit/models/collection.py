from dataclasses import dataclass
from typing import List

from .column import ColumnModel


@dataclass(frozen=True)
class CollectionModel:
    name: str
    enabled: bool
    description: str
    agent_usage: str
    primary_key_field: str
    auto_id: bool
    columns: List[ColumnModel]
