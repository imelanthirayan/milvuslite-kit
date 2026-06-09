from typing import Dict, Optional, Tuple


def _extract_identifier(payload: Dict) -> Tuple[Optional[str], Optional[object]]:
    for key in ('id', 'pk'):
        if key in payload:
            return key, payload[key]
    for key, value in payload.items():
        if key.lower().endswith('id'):
            return key, value
    return None, None


def normalize_search_result(hit: Dict, collection: str) -> Dict:
    entity = hit.get('entity') if isinstance(hit, dict) else None
    data = dict(entity) if isinstance(entity, dict) else {}
    for key, value in hit.items():
        if key not in {'entity', 'distance', 'score'}:
            data.setdefault(key, value)

    id_key, identifier = _extract_identifier(data)
    if identifier is None:
        identifier = hit.get('id')
    if id_key:
        data.pop(id_key, None)

    score = hit.get('score', hit.get('distance'))
    normalized_score = float(score) if score is not None else None
    return {
        'id': str(identifier) if identifier is not None else None,
        'score': normalized_score,
        'collection': collection,
        'data': data,
    }


def normalize_query_result(record: Dict, collection: str) -> Dict:
    data = dict(record)
    id_key, identifier = _extract_identifier(data)
    if id_key:
        data.pop(id_key, None)
    return {
        'id': str(identifier) if identifier is not None else None,
        'collection': collection,
        'data': data,
    }
