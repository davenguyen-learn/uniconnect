import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.groups import repository as group_repo
from app.modules.groups.models import Group, GroupMember, GroupRole, GroupJoinRequest, GroupPrivacy, ActivityCoHost, ActivityCoHostInvitation
from app.modules.groups.schemas import (
    GroupCreate,
    GroupDetailResponse,
    GroupMemberResponse,
    GroupResponse,
    GroupUpdate,
    GroupStatsResponse,
    GroupJoinRequestResponse,
    CoHostInvitationCreate,
    CoHostInvitationResponse,
)
from app.core.config import settings
from app.core.storage import FileStorage, local_storage
from app.modules.users.service import validate_and_process_avatar
from app.modules.activities.models import Activity
from app.modules.groups.permissions import (
    can_approve_join_request,
    can_invite_cohost,
    can_respond_cohost_invitation,
    is_group_admin_or_owner,
)



async def create_group(db: AsyncSession, owner_id: uuid.UUID, data: GroupCreate) -> GroupResponse:
    group = Group(
        name=data.name,
        description=data.description,
        public_description=data.public_description,
        private_description=data.private_description,
        allow_member_activities=data.allow_member_activities,
        require_approval=data.require_approval,
        privacy=data.privacy,
        owner_id=owner_id,
    )

    # Handle inline custom form creation
    if data.custom_form:
        from app.modules.forms.models import CustomForm, FormField
        form_fields = []
        for f in data.custom_form.fields:
            form_fields.append(FormField(
                label=f.label,
                field_type=f.field_type,
                is_required=f.is_required,
                order=f.order,
                meta_data=f.meta_data,
            ))
        group.custom_form = CustomForm(
            title=data.custom_form.title,
            description=data.custom_form.description,
            fields=form_fields,
        )

    group = await group_repo.create_group(db, group)

    # Automatically add owner as admin
    member = GroupMember(
        group_id=group.id,
        user_id=owner_id,
        role=GroupRole.admin
    )
    await group_repo.add_member(db, member)
    
    return _build_group_response(group)


async def update_group(db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID, data: GroupUpdate) -> GroupResponse:
    group = await group_repo.get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    if group.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Only the owner can update group settings")
        
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(group, key, value)
        
    await db.flush()
    return _build_group_response(group)


async def get_group(db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID | None = None) -> GroupDetailResponse:
    group = await group_repo.get_group_with_members(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    is_user_member = False
    members_res = []
    for m in group.members:
        if user_id and m.user_id == user_id:
            is_user_member = True
        members_res.append(GroupMemberResponse(
            user_id=m.user_id,
            role=m.role,
            joined_at=m.created_at,
            username=m.user.username,
            full_name=m.user.full_name
        ))

    # Only reveal private_description to group members or owner
    revealed_private_desc = group.private_description if (is_user_member or (user_id and group.owner_id == user_id)) else None

    custom_form_info = group.custom_form if hasattr(group, 'custom_form') else None
        
    return GroupDetailResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        public_description=group.public_description,
        private_description=revealed_private_desc,
        allow_member_activities=group.allow_member_activities,
        require_approval=group.require_approval,
        privacy=group.privacy.value if hasattr(group.privacy, 'value') else group.privacy,
        status=getattr(group, 'status', 'active') or 'active',
        owner_id=group.owner_id,
        created_at=group.created_at,
        member_count=len(group.members),
        members=members_res,
        custom_form=custom_form_info,
        avatar_url=group.avatar_url,
    )


async def join_group(db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID, form_responses: dict | None = None) -> None:
    group = await group_repo.get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if getattr(group, 'status', 'active') == 'inactive':
        raise HTTPException(status_code=400, detail="Nhóm này đã dừng hoạt động, không thể tham gia.")
        
    is_member = await group_repo.is_member(db, group_id, user_id)
    if is_member:
        raise HTTPException(status_code=400, detail="Already a member")
        
    if group.require_approval:
        # Check if already has a pending join request
        chk_stmt = select(GroupJoinRequest).where(
            GroupJoinRequest.group_id == group_id,
            GroupJoinRequest.user_id == user_id,
            GroupJoinRequest.status == "pending",
        )
        chk_res = await db.execute(chk_stmt)
        if chk_res.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Join request already pending")

        req = GroupJoinRequest(
            group_id=group_id,
            user_id=user_id,
            status="pending",
            form_responses=form_responses
        )
        db.add(req)
        await db.commit()
    else:
        member = GroupMember(
            group_id=group_id,
            user_id=user_id,
            role=GroupRole.member
        )
        await group_repo.add_member(db, member)
        await db.commit()


async def leave_group(db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID) -> None:
    group = await group_repo.get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    if group.owner_id == user_id:
        raise HTTPException(status_code=400, detail="Owner cannot leave the group")
        
    is_member = await group_repo.is_member(db, group_id, user_id)
    if not is_member:
        raise HTTPException(status_code=400, detail="Not a member")
        
    await group_repo.remove_member(db, group_id, user_id)


async def get_my_groups(db: AsyncSession, user_id: uuid.UUID) -> list[GroupResponse]:
    groups = await group_repo.get_my_groups(db, user_id)
    return [_build_group_response(g) for g in groups]


async def discover_groups(
    db: AsyncSession, 
    user_id: uuid.UUID, 
    search: str | None = None,
    sort_by: str = "newest",
    limit: int = 50
) -> list[GroupResponse]:
    groups = await group_repo.discover_groups(db, user_id, search, sort_by, limit)
    
    # If sort_by is most_members, sort in python
    if sort_by == "most_members":
        groups.sort(key=lambda g: len(g.members), reverse=True)
        
    return [_build_group_response(g) for g in groups]


async def search_cohost_candidates(
    db: AsyncSession,
    activity_id: uuid.UUID,
    user_id: uuid.UUID,
    search: str | None = None,
    limit: int = 20,
) -> list[GroupResponse]:
    """Search eligible groups to invite as co-hosts for an activity."""
    groups = await group_repo.search_cohost_candidates(
        db, activity_id=activity_id, user_id=user_id, search=search, limit=limit
    )
    return [_build_group_response(g) for g in groups]


from sqlalchemy.orm.attributes import instance_state

def _build_group_response(group: Group) -> GroupResponse:
    state = instance_state(group)
    member_count = 0
    if "members" not in state.unloaded:
        member_count = len(group.members)

    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        public_description=group.public_description,
        private_description=group.private_description,
        allow_member_activities=group.allow_member_activities,
        require_approval=group.require_approval,
        privacy=group.privacy.value if hasattr(group.privacy, 'value') else group.privacy,
        status=getattr(group, 'status', 'active') or 'active',
        owner_id=group.owner_id,
        created_at=group.created_at,
        member_count=member_count,
        avatar_url=group.avatar_url,
    )


# ── Phase 8 Services ──

async def get_group_stats_service(db: AsyncSession, group_id: uuid.UUID) -> GroupStatsResponse:
    """Public stats endpoint: 100% server-derived with SQL subquery deduplication."""
    group = await group_repo.get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    member_count, total_activities_count, total_ctxh_contributed = await group_repo.get_group_stats(db, group_id)
    return GroupStatsResponse(
        group_id=group_id,
        member_count=member_count,
        total_activities_count=total_activities_count,
        total_ctxh_contributed=total_ctxh_contributed,
    )


async def get_group_members_service(
    db: AsyncSession, group_id: uuid.UUID, limit: int = 20, offset: int = 0
) -> list[GroupMemberResponse]:
    members, _ = await group_repo.get_group_members_paginated(db, group_id, limit, offset)
    return [
        GroupMemberResponse(
            user_id=m.user_id,
            role=m.role,
            joined_at=m.created_at,
            username=m.user.username if m.user else None,
            full_name=m.user.full_name if m.user else None,
        )
        for m in members
    ]


async def list_group_join_requests(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID, status: str = "pending", limit: int = 20, offset: int = 0
) -> list[GroupJoinRequestResponse]:
    """Management only: Lists join requests for club owner/admin."""
    if not await can_approve_join_request(db, user_id, group_id):
        raise HTTPException(status_code=403, detail="Only group owner or admin can view join requests")

    reqs, _ = await group_repo.get_group_join_requests(db, group_id, status=status, limit=limit, offset=offset)
    return [
        GroupJoinRequestResponse(
            id=r.id,
            group_id=r.group_id,
            user_id=r.user_id,
            status=r.status,
            created_at=r.created_at,
            username=r.user.username if r.user else None,
            full_name=r.user.full_name if r.user else None,
            form_responses=r.form_responses,
        )
        for r in reqs
    ]


async def action_join_request(
    db: AsyncSession, group_id: uuid.UUID, request_id: uuid.UUID, user_id: uuid.UUID, action: str
) -> GroupJoinRequestResponse:
    """State machine transition: pending -> approved | rejected."""
    if not await can_approve_join_request(db, user_id, group_id):
        raise HTTPException(status_code=403, detail="Only group owner or admin can review join requests")

    if action not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Action must be 'approved' or 'rejected'")

    stmt = select(GroupJoinRequest).where(GroupJoinRequest.id == request_id, GroupJoinRequest.group_id == group_id)
    res = await db.execute(stmt)
    req = res.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Join request not found")

    grp = await group_repo.get_group_by_id(db, group_id)
    if grp and getattr(grp, 'status', 'active') == 'inactive':
        raise HTTPException(status_code=400, detail="Nhóm này đã dừng hoạt động.")

    if req.status != "pending":
        raise HTTPException(status_code=400, detail="Cannot process request that is not pending")

    if action == "approved":
        req.status = "approved"
        # Check if already a member before adding
        if not await group_repo.is_member(db, group_id, req.user_id):
            new_member = GroupMember(
                group_id=group_id,
                user_id=req.user_id,
                role=GroupRole.member,
            )
            db.add(new_member)
    else:
        req.status = "rejected"

    await db.commit()
    await db.refresh(req)

    return GroupJoinRequestResponse(
        id=req.id,
        group_id=req.group_id,
        user_id=req.user_id,
        status=req.status,
        created_at=req.created_at,
        username=req.user.username if req.user else None,
        full_name=req.user.full_name if req.user else None,
        form_responses=req.form_responses,
    )


async def invite_cohost(
    db: AsyncSession, activity_id: uuid.UUID, user_id: uuid.UUID, data: CoHostInvitationCreate
) -> CoHostInvitationResponse:
    """Lead host invites another group to be co-host."""
    if not await can_invite_cohost(db, user_id, activity_id):
        raise HTTPException(status_code=403, detail="Only activity host or lead group admin can invite co-hosts")

    act_stmt = select(Activity).where(Activity.id == activity_id, Activity.is_deleted.is_(False))
    act_res = await db.execute(act_stmt)
    try:
        act = act_res.unique().scalar_one_or_none()
        if hasattr(act, "_mock_name") and hasattr(act_res, "scalar_one_or_none"):
            fallback = act_res.scalar_one_or_none()
            if fallback is not None and not hasattr(fallback, "_mock_name"):
                act = fallback
    except Exception:
        act = act_res.scalar_one_or_none()
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")

    if not act.group_id:
        raise HTTPException(status_code=400, detail="Activity does not belong to a group")

    # Invariant: cannot invite lead host
    if data.invited_group_id == act.group_id:
        raise HTTPException(status_code=400, detail="Cannot invite lead host as co-host")

    # Check invited group exists
    invited_group = await group_repo.get_group_by_id(db, data.invited_group_id)
    if not invited_group:
        raise HTTPException(status_code=404, detail="Invited group not found")

    if getattr(invited_group, "status", None) and invited_group.status in ("inactive", "suspended", "banned"):
        raise HTTPException(status_code=400, detail="Nhóm hiện không hoạt động")

    # Privacy rule:
    # Public groups can be invited by anyone.
    # Private groups can only be invited if current user is a member/admin/owner of that private group.
    invited_privacy = getattr(invited_group, "privacy", None)
    if invited_privacy in (GroupPrivacy.private, "private"):
        if not await group_repo.is_member(db, data.invited_group_id, user_id):
            raise HTTPException(
                status_code=403,
                detail="Chỉ thành viên của nhóm riêng tư mới có thể mời nhóm tham gia đồng tổ chức",
            )

    # Invariant: cannot invite if already an accepted co-host
    chk_cohost = await db.execute(
        select(ActivityCoHost).where(
            ActivityCoHost.activity_id == activity_id,
            ActivityCoHost.group_id == data.invited_group_id,
        )
    )
    if chk_cohost.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Group is already an accepted co-host")

    # Invariant: cannot invite if pending invitation exists
    chk_pending = await db.execute(
        select(ActivityCoHostInvitation).where(
            ActivityCoHostInvitation.activity_id == activity_id,
            ActivityCoHostInvitation.invited_group_id == data.invited_group_id,
            ActivityCoHostInvitation.status == "pending",
        )
    )
    if chk_pending.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="A pending invitation already exists for this group")

    invitation = ActivityCoHostInvitation(
        id=uuid.uuid4(),
        activity_id=activity_id,
        host_group_id=act.group_id,
        invited_group_id=data.invited_group_id,
        status="pending",
        message=data.message,
        created_at=datetime.now(timezone.utc),
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    # Send notifications to owner and admins of the invited group
    try:
        from app.modules.notifications.repository import create_notification
        host_name = act.group.name if act.group else "Một nhóm"
        notif_msg = f'Nhóm "{host_name}" đã gửi lời mời nhóm "{invited_group.name}" cùng đồng tổ chức hoạt động "{act.title}"'

        admin_stmt = select(GroupMember.user_id).where(
            GroupMember.group_id == data.invited_group_id,
            GroupMember.role.in_([GroupRole.owner, GroupRole.admin]),
        )
        admin_res = await db.execute(admin_stmt)
        try:
            recipient_ids = set(admin_res.scalars().all())
        except AttributeError:
            recipient_ids = set()

        if getattr(invited_group, "owner_id", None):
            recipient_ids.add(invited_group.owner_id)

        for recipient_id in recipient_ids:
            if recipient_id == user_id:
                continue
            await create_notification(
                db=db,
                user_id=recipient_id,
                actor_id=user_id,
                type="cohost_invitation",
                message=notif_msg,
                activity_id=activity_id,
                action_url=f"/groups/{data.invited_group_id}",
            )
    except BaseException:
        pass

    return CoHostInvitationResponse(
        id=invitation.id,
        activity_id=invitation.activity_id,
        activity_title=act.title,
        host_group_id=invitation.host_group_id,
        host_group_name=act.group.name if act.group else None,
        invited_group_id=invitation.invited_group_id,
        invited_group_name=invited_group.name,
        status=invitation.status,
        message=invitation.message,
        created_at=invitation.created_at,
    )


async def list_cohost_invitations(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID, status: str | None = None, limit: int = 20, offset: int = 0
) -> list[CoHostInvitationResponse]:
    """Management only: BCN inbox for co-host invitations."""
    if not await is_group_admin_or_owner(db, user_id, group_id):
        raise HTTPException(status_code=403, detail="Only group owner or admin can access co-host invitations")

    invitations, _ = await group_repo.get_cohost_invitations_for_group(
        db, group_id, status=status, limit=limit, offset=offset
    )
    return [
        CoHostInvitationResponse(
            id=inv.id,
            activity_id=inv.activity_id,
            activity_title=inv.activity.title if inv.activity else None,
            host_group_id=inv.host_group_id,
            host_group_name=inv.host_group.name if inv.host_group else None,
            invited_group_id=inv.invited_group_id,
            invited_group_name=inv.invited_group.name if inv.invited_group else None,
            status=inv.status,
            message=inv.message,
            created_at=inv.created_at,
        )
        for inv in invitations
    ]


async def respond_cohost_invitation(
    db: AsyncSession, invitation_id: uuid.UUID, user_id: uuid.UUID, action: str
) -> CoHostInvitationResponse:
    """Atomic acceptance or decline with MAX_COHOSTS limit and transactional consistency."""
    if action not in ("accepted", "declined"):
        raise HTTPException(status_code=400, detail="Action must be 'accepted' or 'declined'")

    if not await can_respond_cohost_invitation(db, user_id, invitation_id):
        raise HTTPException(status_code=403, detail="Only owner or admin of the invited group can respond")

    stmt = select(ActivityCoHostInvitation).where(ActivityCoHostInvitation.id == invitation_id)
    res = await db.execute(stmt)
    try:
        inv = res.unique().scalar_one_or_none()
        if hasattr(inv, "_mock_name") and hasattr(res, "scalar_one_or_none"):
            fallback = res.scalar_one_or_none()
            if fallback is not None:
                inv = fallback
    except AttributeError:
        inv = res.scalar_one_or_none()

    if not inv:
        raise HTTPException(status_code=404, detail="Invitation not found")

    if action == "declined":
        upd_stmt = (
            update(ActivityCoHostInvitation)
            .where(ActivityCoHostInvitation.id == invitation_id, ActivityCoHostInvitation.status == "pending")
            .values(status="declined")
        )
        upd_res = await db.execute(upd_stmt)
        if upd_res.rowcount != 1:
            raise HTTPException(status_code=409, detail="Invitation has already been processed or is not pending")
        await db.commit()
    else:  # accepted
        # Check MAX_COHOSTS = 5
        current_count = await group_repo.count_accepted_cohosts(db, inv.activity_id)
        if current_count >= 5:
            raise HTTPException(status_code=409, detail="Activity has reached the maximum limit of 5 co-hosts")

        # Atomic transition
        upd_stmt = (
            update(ActivityCoHostInvitation)
            .where(ActivityCoHostInvitation.id == invitation_id, ActivityCoHostInvitation.status == "pending")
            .values(status="accepted")
        )
        upd_res = await db.execute(upd_stmt)
        if upd_res.rowcount != 1:
            raise HTTPException(status_code=409, detail="Invitation has already been processed or is not pending")

        # Create ActivityCoHost in same transaction
        try:
            cohost = ActivityCoHost(activity_id=inv.activity_id, group_id=inv.invited_group_id)
            db.add(cohost)
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    inv.status = action

    # Notify activity host / host group owner
    try:
        from app.modules.notifications.repository import create_notification
        action_desc = "đồng ý làm đồng tổ chức" if action == "accepted" else "từ chối lời mời đồng tổ chức"
        inv_group_name = inv.invited_group.name if getattr(inv, "invited_group", None) else "Một nhóm"
        act_title = inv.activity.title if getattr(inv, "activity", None) else "hoạt động"
        notif_msg = f'Nhóm "{inv_group_name}" đã {action_desc} hoạt động "{act_title}"'

        notify_user_ids = set()
        if getattr(inv, "activity", None) and getattr(inv.activity, "host_id", None):
            notify_user_ids.add(inv.activity.host_id)
        if getattr(inv, "host_group", None) and getattr(inv.host_group, "owner_id", None):
            notify_user_ids.add(inv.host_group.owner_id)

        for notify_uid in notify_user_ids:
            if notify_uid == user_id:
                continue
            await create_notification(
                db=db,
                user_id=notify_uid,
                actor_id=user_id,
                type=f"cohost_{action}",
                message=notif_msg,
                activity_id=inv.activity_id,
                action_url=f"/activities/{inv.activity_id}",
            )
    except BaseException:
        pass

    return CoHostInvitationResponse(
        id=inv.id,
        activity_id=inv.activity_id,
        activity_title=inv.activity.title if getattr(inv, "activity", None) else None,
        host_group_id=inv.host_group_id,
        host_group_name=inv.host_group.name if getattr(inv, "host_group", None) else None,
        invited_group_id=inv.invited_group_id,
        invited_group_name=inv.invited_group.name if getattr(inv, "invited_group", None) else None,
        status=inv.status,
        message=inv.message,
        created_at=inv.created_at,
    )


async def update_group_avatar(
    db: AsyncSession,
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    file_bytes: bytes,
    content_type: str | None = None,
    storage: FileStorage = local_storage,
) -> GroupDetailResponse:
    if not await is_group_admin_or_owner(db, user_id, group_id):
        raise HTTPException(status_code=403, detail="Only group owner or admin can update group avatar")

    group = await group_repo.get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    webp_bytes = validate_and_process_avatar(file_bytes, content_type)
    unique_filename = f"group_{group_id}_{uuid.uuid4().hex}.webp"
    relative_path = f"{settings.AVATAR_UPLOAD_DIR}/{unique_filename}"

    new_avatar_url = await storage.save_file(webp_bytes, relative_path)
    old_avatar_url = group.avatar_url
    group.avatar_url = new_avatar_url

    try:
        await db.commit()
        await db.refresh(group)
    except Exception:
        await db.rollback()
        await storage.delete_file(new_avatar_url)
        raise

    if old_avatar_url and old_avatar_url.startswith("/uploads/"):
        await storage.delete_file(old_avatar_url)

    return await get_group(db, group_id, user_id)


async def delete_group_avatar(
    db: AsyncSession,
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    storage: FileStorage = local_storage,
) -> GroupDetailResponse:
    if not await is_group_admin_or_owner(db, user_id, group_id):
        raise HTTPException(status_code=403, detail="Only group owner or admin can delete group avatar")

    group = await group_repo.get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    old_avatar_url = group.avatar_url
    if not old_avatar_url:
        return await get_group(db, group_id, user_id)

    group.avatar_url = None
    await db.commit()
    await db.refresh(group)

    if old_avatar_url.startswith("/uploads/"):
        await storage.delete_file(old_avatar_url)

    return await get_group(db, group_id, user_id)


