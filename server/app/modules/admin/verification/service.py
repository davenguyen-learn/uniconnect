"""Service for managing and reviewing Organization Verification requests."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.exceptions import NotFoundError, ValidationError
from app.modules.admin.audit.service import record_audit_log
from app.modules.admin.models import (
    AdminAuditAction,
    AdminAuditTargetType,
    OrganizationVerificationRequest,
    VerificationStatus,
)
from app.modules.admin.verification.schemas import (
    VerificationItem,
    VerificationList,
    VerificationRequestCreate,
)
from app.modules.users.models import User, UserRole


async def submit_verification_request(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: VerificationRequestCreate,
) -> VerificationItem:
    """Submit a new organization verification request."""
    # Check if there is already an active pending request
    pending_check = await db.execute(
        select(OrganizationVerificationRequest).where(
            OrganizationVerificationRequest.user_id == user_id,
            OrganizationVerificationRequest.status == VerificationStatus.pending,
        )
    )
    if pending_check.scalars().first():
        raise ValidationError("You already have a pending verification request under review.")

    user = await db.get(User, user_id)
    if not user:
        raise NotFoundError("User not found.")

    req = OrganizationVerificationRequest(
        id=uuid.uuid4(),
        user_id=user_id,
        organization_name=data.organization_name,
        faculty=data.faculty,
        document_url=data.document_url,
        description=data.description,
        status=VerificationStatus.pending,
    )
    db.add(req)
    await db.flush()

    return VerificationItem(
        id=req.id,
        user_id=req.user_id,
        organization_name=req.organization_name,
        faculty=req.faculty,
        document_url=req.document_url,
        description=req.description,
        status=req.status.value,
        admin_note=req.admin_note,
        reviewed_by=req.reviewed_by,
        reviewed_at=req.reviewed_at,
        created_at=req.created_at,
        applicant_name=user.full_name or user.username,
        applicant_email=user.email,
    )


async def list_verification_requests(
    db: AsyncSession,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> VerificationList:
    """List paginated organization verification requests."""
    base = select(OrganizationVerificationRequest).options(
        joinedload(OrganizationVerificationRequest.user)
    )
    count_base = select(func.count()).select_from(OrganizationVerificationRequest)

    if status:
        base = base.where(OrganizationVerificationRequest.status == status)
        count_base = count_base.where(OrganizationVerificationRequest.status == status)

    total = (await db.execute(count_base)).scalar() or 0
    stmt = (
        base.order_by(OrganizationVerificationRequest.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    requests = result.unique().scalars().all()

    items = [
        VerificationItem(
            id=r.id,
            user_id=r.user_id,
            organization_name=r.organization_name,
            faculty=r.faculty,
            document_url=r.document_url,
            description=r.description,
            status=r.status.value if hasattr(r.status, "value") else str(r.status),
            admin_note=r.admin_note,
            reviewed_by=r.reviewed_by,
            reviewed_at=r.reviewed_at,
            created_at=r.created_at,
            applicant_name=r.user.full_name or r.user.username if r.user else None,
            applicant_email=r.user.email if r.user else None,
        )
        for r in requests
    ]

    return VerificationList(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


async def review_verification_request(
    db: AsyncSession,
    request_id: uuid.UUID,
    admin_id: uuid.UUID,
    action: str,
    admin_note: str | None = None,
) -> VerificationItem:
    """Atomic state machine transition with terminal-state protection and audit logging."""
    req = await db.get(OrganizationVerificationRequest, request_id)
    if not req:
        raise NotFoundError("Verification request not found.")

    # Terminal state check
    current_status = req.status.value if hasattr(req.status, "value") else str(req.status)
    if current_status != VerificationStatus.pending.value:
        raise ValidationError(
            f"Cannot review request already in terminal state '{current_status}'."
        )

    now = datetime.now(timezone.utc)
    target_user = await db.get(User, req.user_id)

    if action == "approve":
        req.status = VerificationStatus.approved
        if target_user:
            target_user.is_verified = True
            if target_user.role == UserRole.student:
                target_user.role = UserRole.edu_org
        audit_act = AdminAuditAction.verify_organization
    elif action == "reject":
        req.status = VerificationStatus.rejected
        audit_act = AdminAuditAction.reject_organization
    else:
        raise ValidationError(f"Invalid review action '{action}'.")

    req.admin_note = admin_note
    req.reviewed_by = admin_id
    req.reviewed_at = now

    # Write audit log within same transaction
    await record_audit_log(
        db=db,
        actor_id=admin_id,
        action=audit_act,
        target_type=AdminAuditTargetType.verification,
        target_id=req.id,
        metadata_json={
            "user_id": str(req.user_id),
            "organization_name": req.organization_name,
            "action": action,
            "admin_note_provided": bool(admin_note),
        },
    )

    await db.flush()

    return VerificationItem(
        id=req.id,
        user_id=req.user_id,
        organization_name=req.organization_name,
        faculty=req.faculty,
        document_url=req.document_url,
        description=req.description,
        status=req.status.value if hasattr(req.status, "value") else str(req.status),
        admin_note=req.admin_note,
        reviewed_by=req.reviewed_by,
        reviewed_at=req.reviewed_at,
        created_at=req.created_at,
        applicant_name=target_user.full_name or target_user.username if target_user else None,
        applicant_email=target_user.email if target_user else None,
    )
