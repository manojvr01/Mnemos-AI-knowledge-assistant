import os
import aiofiles
from pathlib import Path
from app.storage.base import StorageBackend
from app.core.config import settings


class LocalStorage(StorageBackend):
    def __init__(self, root_dir: str | None = None):
        self.root_dir = Path(root_dir or settings.STORAGE_LOCAL_ROOT).resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, storage_key: str) -> Path:
        # Prevent directory traversal attacks by resolving against root
        clean_key = storage_key.lstrip("/\\")
        full_path = (self.root_dir / clean_key).resolve()
        if not str(full_path).startswith(str(self.root_dir)):
            raise ValueError(f"Security error: Invalid storage key traversal attempt: {storage_key}")
        return full_path

    async def save_file(self, storage_key: str, content: bytes) -> str:
        full_path = self._get_full_path(storage_key)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(content)
        return storage_key

    async def read_file(self, storage_key: str) -> bytes:
        full_path = self._get_full_path(storage_key)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found in storage: {storage_key}")
        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete_file(self, storage_key: str) -> bool:
        full_path = self._get_full_path(storage_key)
        if full_path.exists():
            full_path.unlink()
            return True
        return False

    async def file_exists(self, storage_key: str) -> bool:
        full_path = self._get_full_path(storage_key)
        return full_path.exists()
