import io
import uuid
from unittest.mock import AsyncMock, MagicMock
from PIL import Image
import pytest

from app.core.config import settings
from app.core.exceptions import BadRequestError, PayloadTooLargeError
from app.core.storage import LocalFileStorage
from app.modules.users.models import User
from app.modules.users.service import (
    delete_avatar,
    update_avatar,
    validate_and_process_avatar,
)


def _create_sample_image(format="PNG", size=(100, 100), color=(16, 185, 129)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def test_validate_and_process_valid_png():
    """Verify valid PNG is processed and returned as WebP bytes."""
    data = _create_sample_image("PNG")
    out = validate_and_process_avatar(data, "image/png")
    assert isinstance(out, bytes)
    # Check that output is decodable as WebP
    out_img = Image.open(io.BytesIO(out))
    assert out_img.format == "WEBP"


def test_validate_and_process_valid_jpeg():
    """Verify valid JPEG is processed and converted to WebP."""
    data = _create_sample_image("JPEG")
    out = validate_and_process_avatar(data, "image/jpeg")
    assert isinstance(out, bytes)
    out_img = Image.open(io.BytesIO(out))
    assert out_img.format == "WEBP"


def test_validate_and_process_preserve_transparency():
    """Verify PNG with alpha transparency is preserved in output WebP."""
    img = Image.new("RGBA", (80, 80), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    out = validate_and_process_avatar(buf.getvalue(), "image/png")
    out_img = Image.open(io.BytesIO(out))
    assert out_img.mode == "RGBA"


def test_reject_payload_too_large():
    """Verify payload exceeding MAX_AVATAR_SIZE_BYTES raises PayloadTooLargeError (413)."""
    oversized = b"0" * (settings.MAX_AVATAR_SIZE_BYTES + 1024)
    with pytest.raises(PayloadTooLargeError) as exc_info:
        validate_and_process_avatar(oversized, "image/jpeg")
    assert "exceeds" in str(exc_info.value.message)


def test_reject_unsupported_mime():
    """Verify declared MIME not in allowed list raises BadRequestError (400)."""
    data = _create_sample_image("PNG")
    with pytest.raises(BadRequestError) as exc_info:
        validate_and_process_avatar(data, "text/html")
    assert "Unsupported file type" in str(exc_info.value.message)


def test_reject_fake_image_content():
    """Verify fake file (e.g. text file disguised as PNG) raises BadRequestError (400)."""
    fake_data = b"<?php echo 'malicious script'; ?>"
    with pytest.raises(BadRequestError) as exc_info:
        validate_and_process_avatar(fake_data, "image/png")
    assert "not a valid or readable image" in str(exc_info.value.message)


def test_reject_oversized_dimensions():
    """Verify dimensions exceeding MAX_AVATAR_DIMENSION raise BadRequestError (400)."""
    oversized_img = _create_sample_image("PNG", size=(5000, 100))
    with pytest.raises(BadRequestError) as exc_info:
        validate_and_process_avatar(oversized_img, "image/png")
    assert "exceed maximum allowed" in str(exc_info.value.message)


from datetime import datetime, timezone

def _make_mock_user(user_id: uuid.UUID, avatar_url: str | None = None) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = user_id
    user.email = "test@example.com"
    user.username = "testuser"
    user.full_name = "Test User"
    user.bio = "A sample bio"
    user.university = "HCMUT"
    user.avatar_url = avatar_url
    user.interests = []
    user.role = "student"
    user.is_verified = False
    user.created_at = datetime.now(timezone.utc)
    return user


@pytest.mark.asyncio
async def test_update_avatar_success_replaces_old_file():
    """Verify update_avatar saves new file, commits DB, and deletes old file."""
    db = AsyncMock()
    user_id = uuid.uuid4()
    mock_user = _make_mock_user(user_id, avatar_url="/uploads/avatars/old_avatar.webp")

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    db.execute.return_value = mock_result

    mock_storage = AsyncMock(spec=LocalFileStorage)
    mock_storage.save_file.return_value = f"/uploads/avatars/{user_id}_new.webp"

    sample_bytes = _create_sample_image("PNG")
    await update_avatar(db, user_id, sample_bytes, "image/png", storage=mock_storage)

    # DB updated and committed
    assert mock_user.avatar_url == f"/uploads/avatars/{user_id}_new.webp"
    db.commit.assert_awaited_once()

    # Old avatar deleted from storage
    mock_storage.delete_file.assert_awaited_once_with("/uploads/avatars/old_avatar.webp")


@pytest.mark.asyncio
async def test_update_avatar_db_failure_cleans_up_new_orphan_file():
    """Verify that if DB commit fails, the newly created file is deleted to prevent orphans."""
    db = AsyncMock()
    user_id = uuid.uuid4()
    mock_user = _make_mock_user(user_id, avatar_url="/uploads/avatars/original.webp")

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    db.execute.return_value = mock_result
    db.commit.side_effect = RuntimeError("Database connection lost")

    mock_storage = AsyncMock(spec=LocalFileStorage)
    mock_storage.save_file.return_value = f"/uploads/avatars/{user_id}_new.webp"

    sample_bytes = _create_sample_image("PNG")
    with pytest.raises(RuntimeError):
        await update_avatar(db, user_id, sample_bytes, "image/png", storage=mock_storage)

    # Rollback invoked
    db.rollback.assert_awaited_once()

    # Newly uploaded file deleted
    mock_storage.delete_file.assert_awaited_once_with(f"/uploads/avatars/{user_id}_new.webp")


@pytest.mark.asyncio
async def test_delete_avatar_safe_order():
    """Verify delete_avatar commits DB first, then deletes file from storage."""
    db = AsyncMock()
    user_id = uuid.uuid4()
    mock_user = _make_mock_user(user_id, avatar_url="/uploads/avatars/target_to_delete.webp")

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    db.execute.return_value = mock_result

    mock_storage = AsyncMock(spec=LocalFileStorage)

    await delete_avatar(db, user_id, storage=mock_storage)

    assert mock_user.avatar_url is None
    db.commit.assert_awaited_once()
    mock_storage.delete_file.assert_awaited_once_with("/uploads/avatars/target_to_delete.webp")


@pytest.mark.asyncio
async def test_delete_avatar_db_failure_retains_file():
    """Verify that if DB commit fails during delete_avatar, old file is NOT deleted."""
    db = AsyncMock()
    user_id = uuid.uuid4()
    mock_user = _make_mock_user(user_id, avatar_url="/uploads/avatars/must_keep.webp")

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    db.execute.return_value = mock_result
    db.commit.side_effect = RuntimeError("Disk full / DB failure")

    mock_storage = AsyncMock(spec=LocalFileStorage)

    with pytest.raises(RuntimeError):
        await delete_avatar(db, user_id, storage=mock_storage)

    # File was NOT deleted because DB commit failed
    mock_storage.delete_file.assert_not_awaited()
