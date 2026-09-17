import type { ChatMessageDTO, ChatEventCardDTO } from '../api/chat';

export interface ChatEventCardViewModel {
  activityId: string;
  title: string;
  dateTimeFormatted: string;
  locationName: string;
  ctxhFormatted?: string;
  distanceFormatted?: string;
  conflictBadge: {
    label: string;
    variant: 'danger' | 'warning' | 'none';
  };
  statusBadge: {
    label: string;
    variant: 'available' | 'registered' | 'full' | 'closed';
  };
  ctaLabel: string;
}

export interface ChatMessageViewModel {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  cards: ChatEventCardViewModel[];
  timeFormatted: string;
}

export function mapChatEventCardToViewModel(dto: ChatEventCardDTO): ChatEventCardViewModel {
  // Format date time
  let dateTimeFormatted = '';
  try {
    const start = new Date(dto.start_time);
    const end = new Date(dto.end_time);
    const timeStr = `${start.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })} - ${end.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}`;
    const dateStr = start.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
    dateTimeFormatted = `${timeStr} • ${dateStr}`;
  } catch {
    dateTimeFormatted = dto.start_time;
  }

  // Format CTXH
  const ctxhFormatted = dto.social_work_days && dto.social_work_days > 0 
    ? `+${dto.social_work_days.toFixed(1)} Ngày CTXH` 
    : undefined;

  // Format distance
  let distanceFormatted: string | undefined;
  if (dto.distance_meters !== null && dto.distance_meters !== undefined) {
    if (dto.distance_meters < 1000) {
      distanceFormatted = `${Math.round(dto.distance_meters)}m`;
    } else {
      distanceFormatted = `${(dto.distance_meters / 1000).toFixed(1)}km`;
    }
    if (dto.distance_status === 'nearby') {
      distanceFormatted += ' • Rất gần';
    }
  }

  // Conflict badge
  let conflictBadge: ChatEventCardViewModel['conflictBadge'] = {
    label: '',
    variant: 'none',
  };
  if (dto.conflict_status === 'hard_conflict') {
    conflictBadge = {
      label: 'Trùng lịch bận!',
      variant: 'danger',
    };
  } else if (dto.conflict_status === 'soft_conflict') {
    conflictBadge = {
      label: 'Lịch sát giờ',
      variant: 'warning',
    };
  }

  // Status & CTA
  let statusBadge: ChatEventCardViewModel['statusBadge'] = {
    label: 'Còn chỗ',
    variant: 'available',
  };
  let ctaLabel = 'Xem hoạt động';

  if (dto.registration_status === 'registered') {
    statusBadge = { label: 'Đã đăng ký', variant: 'registered' };
    ctaLabel = 'Xem vé tham gia';
  } else if (dto.registration_status === 'capacity_full') {
    statusBadge = { label: 'Đã hết chỗ', variant: 'full' };
    ctaLabel = 'Xem chi tiết';
  } else if (dto.registration_status === 'deadline_passed') {
    statusBadge = { label: 'Đã đóng đăng ký', variant: 'closed' };
    ctaLabel = 'Xem chi tiết';
  }

  return {
    activityId: dto.activity_id,
    title: dto.title,
    dateTimeFormatted,
    locationName: dto.location_name,
    ctxhFormatted,
    distanceFormatted,
    conflictBadge,
    statusBadge,
    ctaLabel,
  };
}

export function mapChatMessageToViewModel(dto: ChatMessageDTO): ChatMessageViewModel {
  const cards = (dto.cards || []).map(mapChatEventCardToViewModel);
  let timeFormatted = '';
  try {
    const d = new Date(dto.created_at);
    timeFormatted = d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
  } catch {
    timeFormatted = '';
  }

  return {
    id: dto.id,
    role: dto.role === 'user' ? 'user' : 'assistant',
    content: dto.content,
    cards,
    timeFormatted,
  };
}
