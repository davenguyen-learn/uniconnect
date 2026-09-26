import type { ActivityResponse } from '../api/activities';
import {
  type ActivityRegistrationState,
  computeActivityRegistrationState,
} from './activity-states';

const CATEGORY_TRANSLATIONS: Record<string, string> = {
  Food: 'Ăn uống',
  Cafe: 'Cà phê',
  Coffee: 'Cà phê',
  Study: 'Học tập',
  Workshop: 'Workshop',
  Sports: 'Thể thao',
  Fitness: 'Vận động',
  Volunteer: 'Tình nguyện',
  CTXH: 'CTXH',
  CLB: 'Nhóm',
  Club: 'Nhóm',
  Team: 'Đội nhóm',
  Career: 'Hướng nghiệp',
  Job: 'Việc làm',
  Movie: 'Xem phim',
  Entertainment: 'Giải trí',
  Music: 'Âm nhạc',
  Art: 'Nghệ thuật',
  Boardgame: 'Boardgame',
  Gaming: 'Game',
  Game: 'Game',
  Esports: 'Esports',
  Travel: 'Dã ngoại',
  Backpacking: 'Phượt',
  Social: 'Giao lưu kết bạn',
  Tech: 'Học tập',
  'Ăn uống & Cà phê': 'Ăn uống',
  'Thể thao & Vận động': 'Thể thao',
  'Học thuật & Workshop': 'Học tập',
  'Học thuật & Kỹ năng': 'Học tập',
  'Công nghệ & Lập trình': 'Học tập',
  'Tình nguyện & CTXH': 'Tình nguyện',
  'CLB & Đội nhóm': 'Nhóm',
  'Hướng nghiệp & Việc làm': 'Hướng nghiệp',
  'Xem phim & Giải trí': 'Xem phim',
  'Thể thao & Giải trí': 'Thể thao',
  'Âm nhạc & Nghệ thuật': 'Âm nhạc',
  'Game & Esports': 'Game',
  'Dã ngoại & Phượt': 'Dã ngoại',
};

export function normalizeCategoryName(category?: string | null): string {
  if (!category) return 'Chung';
  const trimmed = category.trim();
  return CATEGORY_TRANSLATIONS[trimmed] || trimmed;
}

export interface ActivityCardViewModel {
  id: string;
  title: string;
  category: string;
  coverUrl: string | null;
  startTimeFormatted: string;
  locationName: string;
  currentParticipants: number;
  maxParticipants: number;
  percentFilled: number;
  socialWorkDays: number | null;
  trophy: {
    id: string;
    name: string;
    icon?: string;
    points: number;
  } | null;
  coOrganizerName?: string | null;
  hasConflict: boolean;
  conflictWarning: string | null;
  conflictingTargetId?: string | null;
  conflictingType?: string | null;
  isPast: boolean;
  registrationState: ActivityRegistrationState;
  distanceKm: string | null;
  requireApproval: boolean;
  host: {
    id: string;
    username: string;
    fullName: string | null;
    avatarUrl?: string | null;
  } | null;
  group: {
    id: string;
    name: string;
    avatarUrl?: string | null;
  } | null;
  coHosts?: Array<{
    id: string;
    name: string;
    avatarUrl?: string | null;
  }>;
  isHost: boolean;
}

export function mapActivityToCardViewModel(
  activity: ActivityResponse,
  isRegistered = false,
  userRegistrationStatus?: 'pending' | 'approved' | 'declined' | 'cancelled',
  currentUserId?: string | null
): ActivityCardViewModel {
  const startDate = new Date(activity.start_time);
  const endDate = new Date(activity.end_time || activity.start_time);
  const now = new Date();
  const isPast = endDate < now;

  const isHost = Boolean(currentUserId && String(activity.host_id) === String(currentUserId));
  const effectiveIsRegistered =
    Boolean(isRegistered) ||
    Boolean(activity.joined_at) ||
    activity.attendance_confirmed !== undefined ||
    (activity as any).is_registered === true ||
    (activity as any).isRegistered === true ||
    isHost;

  const maxParticipants = activity.max_participants || 0;
  const currentParticipants = activity.current_participants || 0;
  const percentFilled =
    maxParticipants > 0
      ? Math.min(100, Math.round((currentParticipants / maxParticipants) * 100))
      : 0;

  const registrationState = isPast
    ? 'deadline_passed'
    : computeActivityRegistrationState({
        isRegistered: effectiveIsRegistered,
        registrationStatus: userRegistrationStatus,
        currentParticipants,
        maxParticipants,
        hasConflict: activity.conflict_info?.has_conflict,
      });

  const formatDate = (d: Date) =>
    d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
  const formatTime = (d: Date) =>
    d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });

  const startDay = formatDate(startDate);
  const startTime = formatTime(startDate);
  const endDay = formatDate(endDate);
  const endTime = formatTime(endDate);

  const hasEndTime = !!activity.end_time && activity.end_time !== activity.start_time;

  const startTimeFormatted = hasEndTime
    ? startDay === endDay
      ? `${startDay} • ${startTime} - ${endTime}`
      : `${startDay} ${startTime} - ${endDay} ${endTime}`
    : `${startDay} • ${startTime}`;

  const distanceKm =
    typeof activity.distance_meters === 'number'
      ? `${(activity.distance_meters / 1000).toFixed(1)} km`
      : null;

  const host = activity.host
    ? {
        id: activity.host_id,
        username: activity.host.username,
        fullName: activity.host.full_name || null,
        avatarUrl: activity.host.avatar_url || null,
      }
    : activity.host_id
    ? {
        id: activity.host_id,
        username: 'Người dùng',
        fullName: null,
        avatarUrl: null,
      }
    : null;

  const group = activity.group
    ? {
        id: String(activity.group.id),
        name: activity.group.name,
        avatarUrl: activity.group.avatar_url || null,
      }
    : null;

  return {
    id: activity.id,
    title: activity.title,
    category: normalizeCategoryName(activity.category),
    coverUrl: (activity as any).image_url || (activity as any).cover_url || null,
    startTimeFormatted,
    locationName: activity.meeting_location || activity.location_name || 'Khuôn viên trường',
    currentParticipants,
    maxParticipants,
    percentFilled,
    socialWorkDays:
      typeof activity.social_work_days === 'number' && activity.social_work_days > 0
        ? activity.social_work_days
        : null,
    trophy: activity.trophy
      ? {
          id: activity.trophy.id,
          name: activity.trophy.name,
          icon: activity.trophy.icon,
          points: activity.trophy.points,
        }
      : null,
    coOrganizerName: activity.co_hosts && activity.co_hosts.length > 0
      ? activity.co_hosts.map((c) => c.name).join(', ')
      : null,
    coHosts: (activity.co_hosts || []).map((ch) => ({
      id: String(ch.id),
      name: ch.name,
      avatarUrl: ch.avatar_url || null,
    })),
    hasConflict: !!activity.conflict_info?.has_conflict,
    conflictWarning: activity.conflict_info?.warning_message || null,
    conflictingTargetId: activity.conflict_info?.conflicting_with?.target_id || null,
    conflictingType: activity.conflict_info?.conflicting_with?.type || null,
    isPast,
    registrationState,
    distanceKm,
    requireApproval: !!activity.require_approval,
    host,
    group,
    isHost,
  };
}
