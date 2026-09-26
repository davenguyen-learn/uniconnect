"""Admin Trophy Grant Request Review Service."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import select, func, insert
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.modules.activities.models import Activity
from app.modules.participation.models import JoinRequest, RequestStatus
from app.modules.trophies.models import TrophyGrantRequest, TrophyGrantStatus, UserTrophy, Trophy


async def list_trophy_requests(
    db: AsyncSession,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """List trophy grant requests with optional status filter."""
    base = select(TrophyGrantRequest).options(
        joinedload(TrophyGrantRequest.activity),
        joinedload(TrophyGrantRequest.trophy),
        joinedload(TrophyGrantRequest.reviewer),
    )
    count_base = select(func.count(TrophyGrantRequest.id))

    if status:
        try:
            status_enum = TrophyGrantStatus(status)
            base = base.where(TrophyGrantRequest.status == status_enum)
            count_base = count_base.where(TrophyGrantRequest.status == status_enum)
        except ValueError:
            raise ValidationError(f"Invalid trophy grant status '{status}'.")

    total = await db.scalar(count_base) or 0
    result = await db.execute(
        base.order_by(TrophyGrantRequest.created_at.desc()).offset(offset).limit(limit)
    )
    items = list(result.unique().scalars().all())

    serialized_items = []
    for r in items:
        serialized_items.append({
            "id": r.id,
            "activity_id": r.activity_id,
            "trophy_id": r.trophy_id,
            "status": r.status.value,
            "min_participants_required": r.min_participants_required,
            "actual_attended_count": r.actual_attended_count,
            "admin_notes": r.admin_notes,
            "reviewed_by": r.reviewed_by,
            "reviewed_at": r.reviewed_at,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
            "activity_title": r.activity.title if r.activity else None,
            "trophy_name": r.trophy.name if r.trophy else None,
            "reviewer_name": r.reviewer.full_name or r.reviewer.username if r.reviewer else None,
        })

    return {
        "items": serialized_items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


async def review_trophy_grant_request(
    db: AsyncSession,
    request_id: uuid.UUID,
    action: str,
    admin_notes: str | None = None,
    admin_id: uuid.UUID | None = None,
) -> dict:
    """
    Review a TrophyGrantRequest: state-transition-safe and side-effect-idempotent.
    Claim with FOR UPDATE -> Grant UserTrophy -> Set approved -> Commit atomically.
    """
    if action not in ["approve", "reject"]:
        raise ValidationError("Action must be either 'approve' or 'reject'.")

    # 1. Claim and lock row with FOR UPDATE
    stmt = (
        select(TrophyGrantRequest)
        .where(TrophyGrantRequest.id == request_id)
        .with_for_update()
    )
    req = await db.scalar(stmt)
    if not req:
        raise NotFoundError("Trophy grant request not found.")

    if req.status != TrophyGrantStatus.eligible_for_review:
        raise ConflictError(
            f"Yêu cầu đang ở trạng thái '{req.status.value}', không thể thực hiện xét duyệt lại."
        )

    now = datetime.now(timezone.utc)

    if action == "reject":
        req.status = TrophyGrantStatus.rejected
        req.reviewed_by = admin_id
        req.reviewed_at = now
        req.admin_notes = admin_notes
        await db.commit()
        await db.refresh(req)
        return {
            "id": str(req.id),
            "status": req.status.value,
            "message": "Đã từ chối yêu cầu cấp Trophy.",
            "granted_count": 0,
        }

    # Action == 'approve'
    # 2. Fetch host_id explicitly from Activity to avoid implicit ORM lazy-load dependency
    host_id = await db.scalar(select(Activity.host_id).where(Activity.id == req.activity_id))

    q_attendees = (
        select(JoinRequest.user_id)
        .where(
            JoinRequest.activity_id == req.activity_id,
            JoinRequest.status == RequestStatus.approved,
            JoinRequest.attendance_confirmed == True,
        )
        .distinct()
    )
    if host_id:
        q_attendees = q_attendees.where(JoinRequest.user_id != host_id)

    attendee_ids = list((await db.execute(q_attendees)).scalars().all())

    # 3. Batch grant UserTrophy with ON CONFLICT DO NOTHING
    granted_count = 0
    for uid in attendee_ids:
        insert_stmt = (
            pg_insert(UserTrophy)
            .values(
                id=uuid.uuid4(),
                user_id=uid,
                trophy_id=req.trophy_id,
                activity_id=req.activity_id,
            )
            .on_conflict_do_nothing(
                constraint="uq_user_trophy_activity_user"
            )
        )
        res = await db.execute(insert_stmt)
        if res.rowcount and res.rowcount > 0:
            granted_count += 1

    # 4. State transition to approved within the exact same atomic transaction boundary
    req.status = TrophyGrantStatus.approved
    req.reviewed_by = admin_id
    req.reviewed_at = now
    req.admin_notes = admin_notes

    # 5. Commit all changes together
    await db.commit()
    await db.refresh(req)

    return {
        "id": str(req.id),
        "status": req.status.value,
        "message": f"Đã phê duyệt cấp Trophy thành công cho {granted_count} sinh viên.",
        "granted_count": granted_count,
    }
