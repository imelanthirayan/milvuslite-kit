from pathlib import Path
from typing import Dict

import yaml

from ..exceptions import ConfigValidationError


def load_config(path: str) -> Dict:
    """Read a YAML configuration file and return the parsed mapping."""
    config_path = Path(path)
    try:
        with config_path.open('r', encoding='utf-8') as handle:
            data = yaml.safe_load(handle) or {}
    except FileNotFoundError as exc:
        raise ConfigValidationError(f'Configuration file not found: {path}') from exc
    except yaml.YAMLError as exc:
        raise ConfigValidationError(f'Failed to parse YAML config: {exc}') from exc

    if not isinstance(data, dict):
        raise ConfigValidationError('Configuration root must be a YAML mapping.')
    return data
