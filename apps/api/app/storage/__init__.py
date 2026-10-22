from app.storage.base import StorageBackend
from app.storage.local import LocalStorage
from app.core.config import settings

_storage_instance: StorageBackend | None = None


def get_storage() -> StorageBackend:
    """Return singleton storage backend instance."""
    global _storage_instance
    if _storage_instance is None:
        if settings.STORAGE_BACKEND == "local":
            _storage_instance = LocalStorage()
        else:
            # Default fallback to local storage
            _storage_instance = LocalStorage()
    return _storage_instance
