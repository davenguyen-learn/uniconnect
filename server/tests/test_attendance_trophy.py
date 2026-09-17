import uuid
import pytest
from app.modules.participation.service import (
    calculate_distance_meters,
    generate_rotating_token,
    get_valid_tokens,
)
from app.modules.activities.models import Activity


def test_calculate_distance_meters():
    # Ben Thanh Market
    lat1, lon1 = 10.7725, 106.6980
    # Notre Dame Cathedral Saigon (approx 850 meters away)
    lat2, lon2 = 10.7798, 106.6990
    
    distance = calculate_distance_meters(lat1, lon1, lat2, lon2)
    assert 750 < distance < 950

    # Same location
    assert calculate_distance_meters(lat1, lon1, lat1, lon1) < 0.01

    # Nearby point (approx 50 meters away)
    nearby_lat = lat1 + 0.0004
    dist_nearby = calculate_distance_meters(lat1, lon1, nearby_lat, lon1)
    assert dist_nearby < 100


def test_rotating_token_generation_and_validation():
    activity_id = uuid.uuid4()
    secret = "TEST_SECRET_CODE"

    token = generate_rotating_token(secret, activity_id, 0)
    assert token == token.upper()
    assert all(c in "0123456789ABCDEF" for c in token)

    valid_tokens = get_valid_tokens(secret, activity_id)
    assert token in valid_tokens

    # Token with different secret should not match
    diff_token = generate_rotating_token("OTHER_SECRET", activity_id, 0)
    assert diff_token not in valid_tokens


def test_certificate_code_format():
    act_id = uuid.uuid4()
    usr_id = uuid.uuid4()
    act_part = str(act_id).replace('-', '')[:6].upper()
    usr_part = str(usr_id).replace('-', '')[:6].upper()
    code = f"UC-{act_part}-{usr_part}"

    assert code.startswith("UC-")
    parts = code.split("-")
    assert len(parts) == 3
    assert len(parts[1]) == 6
    assert len(parts[2]) == 6


@pytest.mark.asyncio
async def test_check_in_idempotency_pre_check():
    from unittest.mock import AsyncMock, MagicMock
    from app.modules.participation.service import check_in_participant
    from app.modules.participation.models import JoinRequest, RequestStatus

    db = AsyncMock()
    act_id = uuid.uuid4()
    usr_id = uuid.uuid4()

    mock_act = MagicMock()
    mock_act.id = act_id
    mock_act.check_in_code = "ABC123"

    mock_jr = MagicMock()
    mock_jr.status = RequestStatus.approved
    mock_jr.attendance_confirmed = True  # Already confirmed!

    import app.modules.activities.repository as act_repo
    import app.modules.participation.repository as part_repo

    orig_get_by_id = act_repo.get_by_id
    orig_get_active = part_repo.get_active_request
    try:
        act_repo.get_by_id = AsyncMock(return_value=mock_act)
        part_repo.get_active_request = AsyncMock(return_value=mock_jr)

        res = await check_in_participant(db, act_id, str(usr_id), "ABC123")
        assert res["attendance_confirmed"] is True
        assert res["already_confirmed"] is True
        assert res["trophy_awarded"] is False
        # db.commit should not even be called
        db.commit.assert_not_called()
    finally:
        act_repo.get_by_id = orig_get_by_id
        part_repo.get_active_request = orig_get_active


@pytest.mark.asyncio
async def test_check_in_untrusted_gps_accuracy_rejected():
    from unittest.mock import AsyncMock, MagicMock
    from app.core.exceptions import ValidationError
    from app.modules.participation.service import check_in_participant
    from app.modules.participation.models import RequestStatus

    db = AsyncMock()
    act_id = uuid.uuid4()
    usr_id = uuid.uuid4()

    mock_act = MagicMock()
    mock_act.id = act_id
    mock_act.start_time = None
    mock_act.end_time = None
    mock_act.check_in_code = "XYZ999"
    mock_act.check_in_radius = 200

    mock_jr = MagicMock()
    mock_jr.status = RequestStatus.approved
    mock_jr.attendance_confirmed = False

    import app.modules.activities.repository as act_repo
    import app.modules.participation.repository as part_repo

    orig_get_by_id = act_repo.get_by_id
    orig_get_active = part_repo.get_active_request
    orig_coords = act_repo.get_coordinates_from_db

    try:
        act_repo.get_by_id = AsyncMock(return_value=mock_act)
        part_repo.get_active_request = AsyncMock(return_value=mock_jr)
        # Activity coordinates: HCM City
        act_repo.get_coordinates_from_db = AsyncMock(return_value=(10.7725, 106.6980))

        # Case 1: accuracy > 100m should be rejected as untrusted/imprecise
        with pytest.raises(ValidationError) as exc:
            await check_in_participant(
                db, act_id, str(usr_id), "XYZ999",
                lat=10.7725, lng=106.6980, accuracy=150.0
            )
        assert "150m > 100m" in str(exc.value)

        # Case 2: missing accuracy should be rejected
        with pytest.raises(ValidationError) as exc2:
            await check_in_participant(
                db, act_id, str(usr_id), "XYZ999",
                lat=10.7725, lng=106.6980, accuracy=None
            )
        assert "độ chính xác GPS" in str(exc2.value)
    finally:
        act_repo.get_by_id = orig_get_by_id
        part_repo.get_active_request = orig_get_active
        act_repo.get_coordinates_from_db = orig_coords


@pytest.mark.asyncio
async def test_check_in_haversine_outside_radius_rejected():
    from unittest.mock import AsyncMock, MagicMock
    from app.core.exceptions import ValidationError
    from app.modules.participation.service import check_in_participant
    from app.modules.participation.models import RequestStatus

    db = AsyncMock()
    act_id = uuid.uuid4()
    usr_id = uuid.uuid4()

    mock_act = MagicMock()
    mock_act.id = act_id
    mock_act.start_time = None
    mock_act.end_time = None
    mock_act.check_in_code = "XYZ999"
    mock_act.check_in_radius = 200  # 200m radius

    mock_jr = MagicMock()
    mock_jr.status = RequestStatus.approved
    mock_jr.attendance_confirmed = False

    import app.modules.activities.repository as act_repo
    import app.modules.participation.repository as part_repo

    orig_get_by_id = act_repo.get_by_id
    orig_get_active = part_repo.get_active_request
    orig_coords = act_repo.get_coordinates_from_db

    try:
        act_repo.get_by_id = AsyncMock(return_value=mock_act)
        part_repo.get_active_request = AsyncMock(return_value=mock_jr)
        # Activity at Ben Thanh
        act_repo.get_coordinates_from_db = AsyncMock(return_value=(10.7725, 106.6980))

        # Client sends Notre Dame coords (~850m away) with fake perfect accuracy (10m)
        with pytest.raises(ValidationError) as exc:
            await check_in_participant(
                db, act_id, str(usr_id), "XYZ999",
                lat=10.7798, lng=106.6990, accuracy=10.0
            )
        assert "vượt quá bán kính cho phép" in str(exc.value)
    finally:
        act_repo.get_by_id = orig_get_by_id
        part_repo.get_active_request = orig_get_active
        act_repo.get_coordinates_from_db = orig_coords

