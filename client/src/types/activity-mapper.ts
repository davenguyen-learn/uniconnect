import type { ActivityResponse } from '../api/activities';
import {
  type ActivityRegistrationState,
  computeActivityRegistrationState,
} from './activity-states';

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
  isPast: boolean;
  registrationState: ActivityRegistrationState;
  distanceKm: string | null;
}

export function mapActivityToCardViewModel(
  activity: ActivityResponse,
  isRegistered = false,
  userRegistrationStatus?: 'pending' | 'approved' | 'declined' | 'cancelled'
): ActivityCardViewModel {
  const startDate = new Date(activity.start_time);
  const endDate = new Date(activity.end_time || activity.start_time);
  const now = new Date();
  const isPast = endDate < now;

  const maxParticipants = activity.max_participants || 0;
  const currentParticipants = activity.current_participants || 0;
  const percentFilled =
    maxParticipants > 0
      ? Math.min(100, Math.round((currentParticipants / maxParticipants) * 100))
      : 0;

  const registrationState = isPast
    ? 'deadline_passed'
    : computeActivityRegistrationState({
        isRegistered,
        registrationStatus: userRegistrationStatus,
        currentParticipants,
        maxParticipants,
        hasConflict: activity.conflict_info?.has_conflict,
      });

  const startTimeFormatted = `${startDate.toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
  })} • ${startDate.toLocaleTimeString('vi-VN', {
    hour: '2-digit',
    minute: '2-digit',
  })}`;

  const distanceKm =
    typeof activity.distance_meters === 'number'
      ? `${(activity.distance_meters / 1000).toFixed(1)} km`
      : null;

  return {
    id: activity.id,
    title: activity.title,
    category: activity.category || 'Chung',
    coverUrl: null, // Default placeholder gradient or image
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
    coOrganizerName: null, // Sẽ gắn khi có co-host
    hasConflict: !!activity.conflict_info?.has_conflict,
    conflictWarning: activity.conflict_info?.warning_message || null,
    isPast,
    registrationState,
    distanceKm,
  };
}
