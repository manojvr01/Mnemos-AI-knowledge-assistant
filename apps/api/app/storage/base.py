from abc import ABC, abstractmethod
from typing import BinaryIO, AsyncGenerator


class StorageBackend(ABC):
    @abstractmethod
    async def save_file(self, storage_key: str, content: bytes) -> str:
        """Save bytes to private storage returning the storage key."""
        pass

    @abstractmethod
    async def read_file(self, storage_key: str) -> bytes:
        """Read full bytes from private storage."""
        pass

    @abstractmethod
    async def delete_file(self, storage_key: str) -> bool:
        """Delete file from private storage."""
        pass

    @abstractmethod
    async def file_exists(self, storage_key: str) -> bool:
        """Check if file exists in storage."""
        pass
