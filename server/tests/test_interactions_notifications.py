import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import pytest

from app.core.exceptions import ValidationError, NotFoundError
from app.modules.interactions.models import Comment, ContentLike
from app.modules.interactions.schemas import CommentCreate, CommentResponse
from app.modules.interactions.service import create_comment, toggle_like
from app.modules.notifications.models import Notification
from app.modules.notifications.schemas import NotificationResponse
from app.modules.notifications.service import create_interaction_notification


def test_comment_model_properties_and_backward_compatibility():
    """Verify Comment model stores activity_id and aliases target_id/target_type."""
    act_id = uuid.uuid4()
    user_id = uuid.uuid4()
    c = Comment(activity_id=act_id, user_id=user_id, content="Great activity!")
    
    assert c.activity_id == act_id
    assert c.target_id == act_id
    assert c.target_type == "activity"


def test_content_like_model_properties():
    """Verify ContentLike model stores activity_id and aliases target_id/target_type."""
    act_id = uuid.uuid4()
    user_id = uuid.uuid4()
    like = ContentLike(activity_id=act_id, user_id=user_id)
    
    assert like.activity_id == act_id
    assert like.target_id == act_id
    assert like.target_type == "activity"


def test_notification_model_properties():
    """Verify Notification model stores nullable activity_id and aliases target_id/target_type."""
    act_id = uuid.uuid4()
    user_id = uuid.uuid4()
    notif = Notification(user_id=user_id, type="new_comment", message="New comment", activity_id=act_id)
    
    assert notif.activity_id == act_id
    assert notif.target_id == act_id
    assert notif.target_type == "activity"

    # Also test null activity_id (system or non-activity notification)
    notif_no_act = Notification(user_id=user_id, type="system", message="Welcome!")
    assert notif_no_act.activity_id is None
    assert notif_no_act.target_id is None


def test_schemas_backward_compatibility():
    """Verify Pydantic schemas serialize activity_id and provide target_id."""
    act_id = uuid.uuid4()
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # CommentResponse
    c_resp = CommentResponse(
        id=uuid.uuid4(),
        activity_id=act_id,
        user_id=user_id,
        parent_id=None,
        content="Hello",
        is_deleted=False,
        created_at=now,
        updated_at=now,
    )
    assert c_resp.activity_id == act_id
    assert c_resp.target_id == act_id
    assert c_resp.target_type == "activity"

    # NotificationResponse
    n_resp = NotificationResponse(
        id=uuid.uuid4(),
        user_id=user_id,
        actor_id=None,
        activity_id=act_id,
        type="new_like",
        message="Someone liked your activity",
        is_read=False,
        created_at=now,
    )
    assert n_resp.activity_id == act_id
    assert n_resp.target_id == act_id


@pytest.mark.asyncio
async def test_create_comment_service_success():
    """Verify create_comment service validates activity and invokes repository."""
    mock_db = AsyncMock()
    act_id = uuid.uuid4()
    user_id = uuid.uuid4()
    host_id = uuid.uuid4()

    mock_activity = AsyncMock()
    mock_activity.id = act_id
    mock_activity.host_id = host_id
    mock_activity.title = "Tech Workshop"

    mock_created_comment = Comment(
        id=uuid.uuid4(),
        activity_id=act_id,
        user_id=user_id,
        content="Awesome event!",
        parent_id=None,
        is_deleted=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    with patch("app.modules.interactions.service._validate_target", return_value=mock_activity), \
         patch("app.modules.interactions.repository.create_comment", return_value=mock_created_comment) as mock_repo_create, \
         patch("app.modules.notifications.service.create_interaction_notification", new_callable=AsyncMock) as mock_notify:

        dto = CommentCreate(content="Awesome event!")
        res = await create_comment(mock_db, "activities", act_id, user_id, dto)

        assert res.activity_id == act_id
        assert res.content == "Awesome event!"
        mock_repo_create.assert_awaited_once_with(
            mock_db,
            activity_id=act_id,
            user_id=user_id,
            content="Awesome event!",
            parent_id=None,
        )
        mock_notify.assert_awaited_once_with(mock_db, user_id, host_id, "comment", act_id, "Tech Workshop")


@pytest.mark.asyncio
async def test_create_comment_parent_belonging_to_other_activity():
    """Verify reply comment on different activity throws ValidationError."""
    mock_db = AsyncMock()
    act_id = uuid.uuid4()
    other_act_id = uuid.uuid4()
    user_id = uuid.uuid4()
    parent_id = uuid.uuid4()

    mock_activity = AsyncMock()
    mock_activity.id = act_id

    mock_parent = Comment(
        id=parent_id,
        activity_id=other_act_id,  # different activity!
        user_id=user_id,
        content="Parent comment",
        parent_id=None,
        is_deleted=False,
    )

    with patch("app.modules.interactions.service._validate_target", return_value=mock_activity), \
         patch("app.modules.interactions.repository.get_comment_by_id", return_value=mock_parent):

        dto = CommentCreate(content="Reply", parent_id=parent_id)
        with pytest.raises(ValidationError, match="Parent comment does not belong to this activity"):
            await create_comment(mock_db, "activities", act_id, user_id, dto)


@pytest.mark.asyncio
async def test_create_interaction_notification_service():
    """Verify create_interaction_notification helper dispatches with activity_id."""
    mock_db = AsyncMock()
    actor_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    act_id = uuid.uuid4()

    with patch("app.modules.notifications.repository.create_notification", new_callable=AsyncMock) as mock_create:
        await create_interaction_notification(
            db=mock_db,
            actor_id=actor_id,
            owner_id=owner_id,
            interaction_type="like",
            activity_id=act_id,
            title="Clean Up Campus",
        )

        mock_create.assert_awaited_once_with(
            db=mock_db,
            user_id=owner_id,
            actor_id=actor_id,
            type="new_like",
            activity_id=act_id,
            message="Someone liked your activity Clean Up Campus",
        )
