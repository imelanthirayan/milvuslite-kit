# milvuslite-kit

**milvuslite-kit** is a lightweight, configuration-driven Python wrapper for [Milvus Lite](https://milvus.io/docs/milvus_lite.md) — the embedded, file-based flavour of Milvus that runs entirely in-process with no server required.

Instead of writing boilerplate to create collections, build indexes, and wire up insert/search/delete logic, you define everything in a single YAML file and let milvuslite-kit handle the rest.

```python
from milvuslite_kit import MilvusLiteKit

with MilvusLiteKit.from_yaml("config.yaml") as plugin:
    plugin.sync_schema()
    plugin.insert("documents", {"id": "1", "title": "Hello", "embedding": [0.1] * 768})
    results = plugin.search("documents", vector=[0.1] * 768, vector_column="embedding", limit=5)
```

> **Milvus Lite** is one of three Milvus deployment modes — alongside Standalone and Distributed. milvuslite-kit targets Lite specifically: local development, embedded apps, and lightweight production workloads that don't need a running server.

## Install

```bash
pip install -r requirements.txt
```

## Quick start

```python
from milvuslite_kit import MilvusLiteKit

plugin = MilvusLiteKit.from_yaml("config.yaml")
plugin.sync_schema()
```

## Minimal config

```yaml
database:
  path: /path/to/db.db

collections:
  documents:
    enabled: true
    primary_key:
      field: id
      auto_id: false
    columns:
      - name: title
        type: text
        required: true
      - name: embedding
        type: vector
        dimension: 768
        index:
          enabled: true
          type: FLAT
          params: {}
```

## Full config reference

### `database`
| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `path` | str | ✅ | Local `.db` file path |
| `name` | str | | Logical name |

### `logging`
| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | `true` | Enable logging |
| `level` | str | `INFO` | Log level |
| `log_to_console` | bool | `true` | Console output |
| `log_to_file` | bool | `false` | File output |
| `file_path` | str | | Log file path |
| `log_duration_ms` | bool | `false` | Include timing |
| `log_operations` | bool | `true` | Log start/end |
| `redact_vectors` | bool | `false` | Replace vectors with `[REDACTED, dim=N]` |

### `defaults`
| Key | Type | Default |
|-----|------|---------|
| `auto_create_collection` | bool | `true` |
| `auto_create_index` | bool | `true` |
| `auto_load_collection` | bool | `true` |
| `default_metric_type` | str | `COSINE` |
| `default_index_type` | str | `FLAT` |

### `collections`
Each key is a collection name.

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `enabled` | bool | | Defaults to `true` |
| `description` | str | | |
| `agent_usage` | str | | Hint for AI agents on how to use this collection |
| `primary_key.field` | str | ✅ | Primary key field name |
| `primary_key.auto_id` | bool | | Auto-generate IDs |
| `columns` | list | | Column definitions |

### Column fields
| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `name` | str | ✅ | |
| `type` | str | ✅ | `text`, `int`, `float`, `bool`, `json`, `vector` |
| `required` | bool | | Validate on insert |
| `dimension` | int | ✅ for `vector` | Vector size |
| `metric_type` | str | | Override default metric |
| `index.enabled` | bool | | Build index on this field |
| `index.type` | str | | See index types below |
| `agent_usage` | str | | Hint for AI agents on how to use this field |
| `index.params` | dict | | Index params |

## Index types

### Vector index types

| Type | Best for | Notes |
|------|----------|-------|
| `FLAT` | Small datasets (<1M vectors) | Exact search, 100% recall, no params needed |
| `IVF_FLAT` | Medium datasets, balanced speed/recall | Params: `nlist` (cluster count, e.g. `128`) |
| `IVF_SQ8` | Memory-constrained, medium datasets | Quantized variant of IVF_FLAT, ~4x smaller |
| `IVF_PQ` | Large datasets, low memory budget | Params: `nlist`, `m` (subquantizers), `nbits` |
| `HNSW` | Most production use cases | Best speed/recall tradeoff; params: `M`, `efConstruction` |
| `SCANN` | High-throughput similarity search | Params: `nlist`, `with_raw_data` |
| `DISKANN` | Billion-scale datasets that exceed RAM | Disk-based, no in-memory index |

### Metric types

| Metric | Best for |
|--------|----------|
| `COSINE` | Text/NLP embeddings (e.g. sentence transformers) |
| `L2` | Image embeddings, geometric similarity |
| `IP` | Pre-normalised vectors (equivalent to cosine without normalisation cost) |

### Quick pick guide

- **Just getting started / small data** → `FLAT` + `COSINE`
- **General production use** → `HNSW` + `COSINE`, params: `{"M": 16, "efConstruction": 200}`
- **Large dataset, memory matters** → `IVF_PQ` + `L2`, params: `{"nlist": 1024, "m": 8, "nbits": 8}`
- **Image search** → `HNSW` + `L2`

Example config for HNSW:

```yaml
- name: embedding
  type: vector
  dimension: 768
  metric_type: COSINE
  index:
    enabled: true
    type: HNSW
    params:
      M: 16
      efConstruction: 200
```



### Schema

```python
plugin.sync_schema()       # create collections + indexes
plugin.validate_schema()   # check fields/dims match config
plugin.list_collections()  # -> List[str]
plugin.collection_exists("documents")  # -> bool
plugin.describe_collection("documents")
plugin.drop_collection("documents")
plugin.reset_collection("documents")   # drop + recreate
```

### Insert

```python
plugin.insert("documents", {"id": "1", "title": "Hello", "embedding": [0.1] * 768})

plugin.bulk_insert("documents", [
    {"id": "1", "title": "Hello", "embedding": [0.1] * 768},
    {"id": "2", "title": "World", "embedding": [0.2] * 768},
])
```

### Query

```python
results = plugin.query(
    "documents",
    filters={"title": {"eq": "Hello"}},
    output_fields=["title"],
)
```

### Search

```python
results = plugin.search(
    "documents",
    vector=[0.1] * 768,
    vector_column="embedding",
    limit=5,
    filters={"title": {"eq": "Hello"}},
    output_fields=["title"],
)
```

### Delete

```python
count = plugin.delete("documents", filters={"id": {"eq": "1"}})
```

## Filter syntax

| Operator | Meaning |
|----------|---------|
| `eq` | `==` |
| `ne` | `!=` |
| `gt` | `>` |
| `gte` | `>=` |
| `lt` | `<` |
| `lte` | `<=` |
| `in` | `in [...]` |

```python
filters = {
    "status": {"in": ["draft", "published"]},
    "score": {"gte": 0.8},
    "active": {"eq": True},
}
```

Shorthand for equality: `{"field": "value"}` is equivalent to `{"field": {"eq": "value"}}`.

## Result format

```python
# query / insert
{"id": "1", "collection": "documents", "data": {"title": "Hello"}}

# search (includes score)
{"id": "1", "score": 0.97, "collection": "documents", "data": {"title": "Hello"}}
```

## Exceptions

All exceptions inherit from `MilvusLiteKitError`.

| Exception | When |
|-----------|------|
| `ConfigValidationError` | Invalid YAML config |
| `CollectionNotFoundError` | Collection not in config or DB |
| `CollectionDisabledError` | Collection has `enabled: false` |
| `CollectionAlreadyExistsError` | Creating a collection that exists |
| `InvalidSchemaError` | Schema mismatch |
| `InvalidVectorDimensionError` | Vector dim mismatch |
| `InsertError` | Insert failure |
| `QueryError` | Query failure |
| `SearchError` | Search failure |
| `DeleteError` | Delete failure |

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```
