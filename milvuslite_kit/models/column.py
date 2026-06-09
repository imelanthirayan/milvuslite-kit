from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class ColumnModel:
    name: str
    type: str
    required: bool
    dimension: Optional[int]
    metric_type: Optional[str]
    index_enabled: bool
    index_type: Optional[str]
    index_params: Optional[Dict]
    description: str
    agent_usage: str
