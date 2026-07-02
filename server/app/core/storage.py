import io
import uuid
import logging
from typing import BinaryIO

import aioboto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)

class StorageService:
    """Async S3-compatible storage service for Cloudflare R2 / AWS S3."""

    def __init__(self):
        self.endpoint_url = settings.R2_ENDPOINT_URL
        self.access_key = settings.R2_ACCESS_KEY_ID
        self.secret_key = settings.R2_SECRET_ACCESS_KEY
        self.bucket_name = settings.R2_BUCKET_NAME
        self.public_url = settings.R2_PUBLIC_URL

        # Use boto3 session for async operations
        self.session = aioboto3.Session(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

    def _get_client(self):
        """Helper to get an async s3 client context manager."""
        return self.session.client(
            's3',
            endpoint_url=self.endpoint_url,
        )

    async def upload_file(self, file_obj: BinaryIO, filename: str, content_type: str, folder: str = "documents") -> str:
        """
        Upload a file to the storage bucket.
        Returns the object key (path in bucket).
        """
        # Generate a unique key to prevent overwriting
        file_ext = filename.split('.')[-1] if '.' in filename else ''
        unique_name = f"{uuid.uuid4().hex}.{file_ext}" if file_ext else uuid.uuid4().hex
        object_key = f"{folder}/{unique_name}"

        try:
            async with self._get_client() as s3:
                await s3.upload_fileobj(
                    file_obj,
                    self.bucket_name,
                    object_key,
                    ExtraArgs={'ContentType': content_type}
                )
            return object_key
        except ClientError as e:
            logger.error(f"Failed to upload file to S3/R2: {e}")
            raise Exception("File upload failed") from e

    async def delete_file(self, object_key: str) -> None:
        """Delete a file from the storage bucket."""
        try:
            async with self._get_client() as s3:
                await s3.delete_object(Bucket=self.bucket_name, Key=object_key)
        except ClientError as e:
            logger.error(f"Failed to delete file from S3/R2: {e}")
            # We log but don't strictly fail if it's already deleted or we can't delete it
            pass

    async def get_presigned_url(self, object_key: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL to share the file temporarily.
        Use this for private documents.
        """
        try:
            async with self._get_client() as s3:
                url = await s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': object_key},
                    ExpiresIn=expiration
                )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise Exception("Could not generate download link") from e

    def get_public_url(self, object_key: str) -> str:
        """
        Get the direct public URL for a file.
        Only works if the bucket or the object is public.
        """
        if self.public_url:
            base = self.public_url.rstrip('/')
            return f"{base}/{object_key}"
        return f"{self.endpoint_url}/{self.bucket_name}/{object_key}"

storage_service = StorageService()
