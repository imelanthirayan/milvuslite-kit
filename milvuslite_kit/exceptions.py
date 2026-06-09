class MilvusLiteKitError(Exception):
    """Base exception for the milvuslite-kit package."""


class ConfigValidationError(MilvusLiteKitError):
    """Raised when configuration validation fails."""


class CollectionNotFoundError(MilvusLiteKitError):
    """Raised when a requested collection does not exist."""


class CollectionDisabledError(MilvusLiteKitError):
    """Raised when an operation targets a disabled collection."""


class CollectionAlreadyExistsError(MilvusLiteKitError):
    """Raised when attempting to create a collection that already exists."""


class InvalidSchemaError(MilvusLiteKitError):
    """Raised when a schema is invalid or mismatched."""


class InvalidVectorDimensionError(MilvusLiteKitError):
    """Raised when a vector does not match its configured dimension."""


class InsertError(MilvusLiteKitError):
    """Raised when an insert operation fails."""


class QueryError(MilvusLiteKitError):
    """Raised when a query operation fails."""


class SearchError(MilvusLiteKitError):
    """Raised when a search operation fails."""


class DeleteError(MilvusLiteKitError):
    """Raised when a delete operation fails."""
