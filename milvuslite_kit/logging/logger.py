import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

LOGGER_NAME = 'milvuslite_kit'
DEFAULT_OPTIONS = {
    'enabled': True,
    'log_duration_ms': False,
    'log_operations': True,
    'redact_vectors': False,
}


def setup_logger(config: Dict) -> logging.Logger:
    """Configure and return the package logger."""
    logging_cfg = (config or {}).get('logging', {}) if isinstance(config, dict) else {}
    logger = logging.getLogger(LOGGER_NAME)
    level_name = str(logging_cfg.get('level', 'INFO')).upper()
    logger.setLevel(getattr(logging, level_name, logging.INFO))
    logger.propagate = False
    logger.handlers.clear()

    options = {
        'enabled': bool(logging_cfg.get('enabled', True)),
        'log_duration_ms': bool(logging_cfg.get('log_duration_ms', False)),
        'log_operations': bool(logging_cfg.get('log_operations', True)),
        'redact_vectors': bool(logging_cfg.get('redact_vectors', False)),
    }
    setattr(logger, '_milvuslite_kit_options', options)

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    if options['enabled']:
        if logging_cfg.get('log_to_console', True):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        if logging_cfg.get('log_to_file'):
            file_path = logging_cfg.get('file_path')
            if file_path:
                target = Path(file_path)
                target.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(target)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    return logger


def get_logger_options(logger: logging.Logger) -> Dict[str, Any]:
    raw_options = getattr(logger, '_milvuslite_kit_options', {})
    if not isinstance(raw_options, dict):
        raw_options = {}
    return {**DEFAULT_OPTIONS, **raw_options}


def _format_value(value: Any, logger: logging.Logger) -> Any:
    options = get_logger_options(logger)
    if isinstance(value, dict):
        return {key: _format_value(item, logger) for key, item in value.items()}
    if options.get('redact_vectors') and isinstance(value, (list, tuple)):
        if all(isinstance(item, (int, float)) for item in value):
            return f'[REDACTED, dim={len(value)}]'
        return [_format_value(item, logger) for item in value]
    return value


def log_operation_start(logger: logging.Logger, operation: str, collection: str, **details: Any) -> float:
    start_time = time.perf_counter()
    options = get_logger_options(logger)
    if options.get('log_operations', True):
        parts = [f'operation={operation}', f'collection={collection}', 'status=start']
        for key, value in details.items():
            if value is not None:
                parts.append(f'{key}={_format_value(value, logger)}')
        logger.info(' '.join(parts))
    return start_time


def log_operation_end(
    logger: logging.Logger,
    operation: str,
    collection: str,
    start_time: float,
    result_count: Optional[int] = None,
) -> None:
    options = get_logger_options(logger)
    if not options.get('log_operations', True):
        return
    parts = [f'operation={operation}', f'collection={collection}', 'status=end']
    if result_count is not None:
        parts.append(f'result_count={result_count}')
    if options.get('log_duration_ms'):
        parts.append(f'duration_ms={(time.perf_counter() - start_time) * 1000:.2f}')
    logger.info(' '.join(parts))


def log_operation_error(
    logger: logging.Logger,
    operation: str,
    collection: str,
    start_time: float,
    error: Exception,
) -> None:
    options = get_logger_options(logger)
    parts = [f'operation={operation}', f'collection={collection}', 'status=error', f'error={error}']
    if options.get('log_duration_ms'):
        parts.append(f'duration_ms={(time.perf_counter() - start_time) * 1000:.2f}')
    logger.error(' '.join(parts))
