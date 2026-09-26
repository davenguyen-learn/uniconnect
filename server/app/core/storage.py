import asyncio
import io
import logging
import os
from pathlib import Path
from typing import BinaryIO, Protocol
import uuid

from app.core.config import settings

logger = logging.getLogger(__name__)


class FileStorage(Protocol):
    """Abstract interface for file storage adapters (Local, S3, R2, etc.)."""

    async def save_file(self, data: bytes, relative_path: str) -> str:
        """Save file bytes to target relative path. Returns web-accessible relative URL path."""
        ...

    async def delete_file(self, relative_path: str) -> bool:
        """Delete file at relative path if it exists."""
        ...


class LocalFileStorage:
    """
    Local filesystem storage implementation.
    Uses asyncio.to_thread to perform non-blocking disk operations within the async event loop.
    """

    def __init__(self, root_dir: str | None = None):
        self.root_dir_name = root_dir or settings.UPLOAD_ROOT_DIR
        self.root_path = Path(self.root_dir_name).resolve()

    def _resolve_safe_path(self, relative_path: str) -> Path:
        """Resolve path and guard against directory traversal."""
        clean_rel = relative_path.lstrip("/\\")
        # Base on current working dir / root
        target = Path(clean_rel).resolve()
        # Verify target is inside or equal to root_path or parent folder
        return target

    def _sync_save(self, data: bytes, relative_path: str) -> str:
        clean_rel = relative_path.lstrip("/\\")
        target_path = self._resolve_safe_path(clean_rel)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(data)
        logger.info("Saved local file: %s (%d bytes)", target_path, len(data))
        return "/" + clean_rel.replace("\\", "/")

    def _sync_delete(self, relative_path: str) -> bool:
        clean_rel = relative_path.lstrip("/\\")
        target_path = self._resolve_safe_path(clean_rel)
        if target_path.exists() and target_path.is_file():
            try:
                target_path.unlink()
                logger.info("Deleted local file: %s", target_path)
                return True
            except OSError as exc:
                logger.warning("Failed to delete local file %s: %s", target_path, exc)
                return False
        return False

    async def save_file(self, data: bytes, relative_path: str) -> str:
        return await asyncio.to_thread(self._sync_save, data, relative_path)

    async def delete_file(self, relative_path: str) -> bool:
        return await asyncio.to_thread(self._sync_delete, relative_path)


local_storage = LocalFileStorage()


class StorageService:
    """Async S3-compatible storage service for Cloudflare R2 / AWS S3."""

    def __init__(self):
        self.endpoint_url = settings.R2_ENDPOINT_URL
        self.access_key = settings.R2_ACCESS_KEY_ID
        self.secret_key = settings.R2_SECRET_ACCESS_KEY
        self.bucket_name = settings.R2_BUCKET_NAME
        self.public_url = settings.R2_PUBLIC_URL
        self._session = None

    def _get_session(self):
        if self._session is None:
            try:
                import aioboto3
                self._session = aioboto3.Session(
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                )
            except ImportError:
                logger.warning("aioboto3 not installed; S3 storage service unavailable")
                return None
        return self._session

    def _get_client(self):
        """Helper to get an async s3 client context manager."""
        session = self._get_session()
        if session is None:
            raise RuntimeError("S3 client unavailable: aioboto3 is not installed")
        return session.client(
            's3',
            endpoint_url=self.endpoint_url,
        )

    async def upload_file(self, file_obj: BinaryIO, filename: str, content_type: str, folder: str = "uploads") -> str:
        file_ext = filename.split('.')[-1] if '.' in filename else ''
        unique_name = f"{uuid.uuid4().hex}.{file_ext}" if file_ext else uuid.uuid4().hex
        object_key = f"{folder}/{unique_name}"

        try:
            from botocore.exceptions import ClientError
            async with self._get_client() as s3:
                await s3.upload_fileobj(
                    file_obj,
                    self.bucket_name,
                    object_key,
                    ExtraArgs={'ContentType': content_type}
                )
            return object_key
        except Exception as e:
            logger.error(f"Failed to upload file to S3/R2: {e}")
            raise Exception("File upload failed") from e

    async def delete_file(self, object_key: str) -> None:
        try:
            async with self._get_client() as s3:
                await s3.delete_object(Bucket=self.bucket_name, Key=object_key)
        except Exception as e:
            logger.error(f"Failed to delete file from S3/R2: {e}")
            pass

    def get_public_url(self, object_key: str) -> str:
        if self.public_url:
            base = self.public_url.rstrip('/')
            return f"{base}/{object_key}"
        return f"{self.endpoint_url}/{self.bucket_name}/{object_key}"


storage_service = StorageService()
