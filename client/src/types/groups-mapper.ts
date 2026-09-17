import type { 
  GroupStatsResponse, 
  GroupMemberResponse, 
  GroupJoinRequestResponse, 
  CoHostInvitationResponse
} from '../api/groups';

export interface GroupStatsViewModel {
  memberCountFormatted: string;
  activitiesCountFormatted: string;
  ctxhContributedFormatted: string;
  memberCount: number;
  totalActivitiesCount: number;
  totalCtxhContributed: number;
}

export interface GroupMemberViewModel {
  userId: string;
  displayName: string;
  username: string;
  role: 'owner' | 'admin' | 'member';
  roleBadge: {
    label: string;
    variant: 'gold' | 'blue' | 'gray';
    isLeadership: boolean;
  };
  joinedDateFormatted: string;
}

export interface GroupJoinRequestViewModel {
  id: string;
  userId: string;
  applicantName: string;
  applicantUsername: string;
  status: 'pending' | 'approved' | 'rejected';
  requestedDateFormatted: string;
  formResponses?: Record<string, any>;
}

export interface CoHostInvitationViewModel {
  id: string;
  activityId: string;
  activityTitle: string;
  hostGroupId: string;
  hostGroupName: string;
  invitedGroupId: string;
  invitedGroupName: string;
  status: 'pending' | 'accepted' | 'declined';
  statusBadge: {
    label: string;
    variant: 'warning' | 'success' | 'danger';
  };
  message?: string;
  createdDateFormatted: string;
}

export function mapGroupStatsToViewModel(stats: GroupStatsResponse): GroupStatsViewModel {
  return {
    memberCountFormatted: `${stats.member_count} thành viên`,
    activitiesCountFormatted: `${stats.total_activities_count} hoạt động`,
    ctxhContributedFormatted: `${stats.total_ctxh_contributed.toFixed(1)} ngày CTXH`,
    memberCount: stats.member_count,
    totalActivitiesCount: stats.total_activities_count,
    totalCtxhContributed: stats.total_ctxh_contributed,
  };
}

export function mapGroupMemberToViewModel(member: GroupMemberResponse): GroupMemberViewModel {
  const isOwner = member.role === 'owner';
  const isAdmin = member.role === 'admin';

  let roleBadge: GroupMemberViewModel['roleBadge'] = {
    label: 'Thành viên',
    variant: 'gray',
    isLeadership: false,
  };

  if (isOwner) {
    roleBadge = {
      label: 'Trưởng CLB',
      variant: 'gold',
      isLeadership: true,
    };
  } else if (isAdmin) {
    roleBadge = {
      label: 'Ban Chủ Nhiệm',
      variant: 'blue',
      isLeadership: true,
    };
  }

  const joinedDate = new Date(member.joined_at);
  const formattedDate = isNaN(joinedDate.getTime()) 
    ? '—' 
    : joinedDate.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });

  return {
    userId: member.user_id,
    displayName: member.full_name || member.username || 'Thành viên',
    username: member.username ? `@${member.username}` : '',
    role: member.role,
    roleBadge,
    joinedDateFormatted: formattedDate,
  };
}

export function mapGroupJoinRequestToViewModel(req: GroupJoinRequestResponse): GroupJoinRequestViewModel {
  const reqDate = new Date(req.created_at);
  const formattedDate = isNaN(reqDate.getTime())
    ? '—'
    : reqDate.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });

  return {
    id: req.id,
    userId: req.user_id,
    applicantName: req.full_name || req.username || 'Sinh viên',
    applicantUsername: req.username ? `@${req.username}` : '',
    status: req.status,
    requestedDateFormatted: formattedDate,
    formResponses: req.form_responses,
  };
}

export function mapCoHostInvitationToViewModel(inv: CoHostInvitationResponse): CoHostInvitationViewModel {
  const invDate = new Date(inv.created_at);
  const formattedDate = isNaN(invDate.getTime())
    ? '—'
    : invDate.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });

  let statusBadge: CoHostInvitationViewModel['statusBadge'] = {
    label: 'Chờ phản hồi',
    variant: 'warning',
  };

  if (inv.status === 'accepted') {
    statusBadge = {
      label: 'Đã đồng ý',
      variant: 'success',
    };
  } else if (inv.status === 'declined') {
    statusBadge = {
      label: 'Đã từ chối',
      variant: 'danger',
    };
  }

  return {
    id: inv.id,
    activityId: inv.activity_id,
    activityTitle: inv.activity_title || 'Hoạt động ngoại khóa',
    hostGroupId: inv.host_group_id,
    hostGroupName: inv.host_group_name || 'CLB Tổ chức',
    invitedGroupId: inv.invited_group_id,
    invitedGroupName: inv.invited_group_name || 'CLB của bạn',
    status: inv.status,
    statusBadge,
    message: inv.message || undefined,
    createdDateFormatted: formattedDate,
  };
}
