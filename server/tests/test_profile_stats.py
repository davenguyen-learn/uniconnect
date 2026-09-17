import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.modules.users.policy import resolve_rank_title, CTXH_TARGET_DAYS
from app.modules.users.service import get_user_stats


def test_rank_title_boundaries():
    """Verify rank title transitions at exact boundary points (-1, exact, +1)."""
    # Active Member: 0 to 49
    assert resolve_rank_title(0) == "Tân sinh viên Tích cực (Active Member)"
    assert resolve_rank_title(49) == "Tân sinh viên Tích cực (Active Member)"

    # Pioneer: 50 to 199
    assert resolve_rank_title(50) == "Tình nguyện viên Tiên phong (Pioneer)"
    assert resolve_rank_title(199) == "Tình nguyện viên Tiên phong (Pioneer)"

    # Leader: 200 to 499
    assert resolve_rank_title(200) == "Thủ lĩnh Năng động (Leader)"
    assert resolve_rank_title(499) == "Thủ lĩnh Năng động (Leader)"

    # Ambassador: 500+
    assert resolve_rank_title(500) == "Đại sứ Hoạt động (Ambassador)"
    assert resolve_rank_title(1200) == "Đại sứ Hoạt động (Ambassador)"


@pytest.mark.asyncio
async def test_user_stats_ctxh_boundaries():
    """Verify CTXH progress calculation, clamping at 100%, and remaining days."""
    db = AsyncMock()
    user_id = uuid.uuid4()

    mock_user = MagicMock()
    mock_user.id = user_id

    # Test cases: (total_ctxh, expected_completion, expected_remaining, expected_reached)
    test_cases = [
        (0.0, 0.0, 15.0, False),
        (7.5, 50.0, 7.5, False),
        (14.5, 96.7, 0.5, False),
        (15.0, 100.0, 0.0, True),
        (20.0, 100.0, 0.0, True),  # Clamped at 100%
    ]

    for ctxh_val, exp_percent, exp_rem, exp_reached in test_cases:
        # Mock scalar for User
        db.scalar = AsyncMock(return_value=mock_user)

        # Mock execute: first call returns CTXH (ctxh_val, 5 attended), second call returns Trophies (2 trophies, 100 pts)
        mock_ctxh_res = MagicMock()
        mock_ctxh_res.one.return_value = (ctxh_val, 5)

        mock_trophy_res = MagicMock()
        mock_trophy_res.one.return_value = (2, 100)

        db.execute = AsyncMock(side_effect=[mock_ctxh_res, mock_trophy_res])

        stats = await get_user_stats(db, user_id, is_self=True)

        assert stats["total_ctxh_days"] == ctxh_val
        assert stats["target_ctxh_days"] == CTXH_TARGET_DAYS
        assert stats["ctxh_completion_percent"] == exp_percent
        assert stats["remaining_ctxh_days"] == exp_rem
        assert stats["is_target_reached"] == exp_reached
        assert stats["rank_title"] == "Tình nguyện viên Tiên phong (Pioneer)"


@pytest.mark.asyncio
async def test_public_user_stats_privacy():
    """Verify public stats response excludes private progress metrics."""
    db = AsyncMock()
    user_id = uuid.uuid4()

    mock_user = MagicMock()
    mock_user.id = user_id
    db.scalar = AsyncMock(return_value=mock_user)

    mock_ctxh_res = MagicMock()
    mock_ctxh_res.one.return_value = (10.0, 3)

    mock_trophy_res = MagicMock()
    mock_trophy_res.one.return_value = (1, 60)

    db.execute = AsyncMock(side_effect=[mock_ctxh_res, mock_trophy_res])

    public_stats = await get_user_stats(db, user_id, is_self=False)

    # Public fields present
    assert public_stats["user_id"] == str(user_id)
    assert public_stats["total_ctxh_days"] == 10.0
    assert public_stats["total_attended_activities"] == 3
    assert public_stats["total_trophies_count"] == 1
    assert public_stats["total_trophy_points"] == 60
    assert public_stats["rank_title"] == "Tình nguyện viên Tiên phong (Pioneer)"

    # Private fields must NOT be in public response
    assert "target_ctxh_days" not in public_stats
    assert "ctxh_completion_percent" not in public_stats
    assert "remaining_ctxh_days" not in public_stats
    assert "is_target_reached" not in public_stats
