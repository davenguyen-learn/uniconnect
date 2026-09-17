import type { ActivityResponse } from '../api/activities';
import type { JoinRequestResponse } from '../api/participation';
import type { ConflictInfo } from '../api/calendar';
import {
  type ActivityRegistrationState,
  computeActivityRegistrationState,
} from './activity-states';

export type DynamicFieldType =
  | 'text'
  | 'number'
  | 'textarea'
  | 'select'
  | 'radio'
  | 'checkbox';

export interface DynamicFormField {
  id: string;
  label: string;
  fieldType: DynamicFieldType;
  isRequired: boolean;
  order: number;
  options?: string[];
}

export interface ActivityDetailViewModel {
  id: string;
  title: string;
  description: string | null;
  category: string;
  privacy: string;
  startFormatted: string;
  endFormatted: string;
  locationName: string;
  latitude: number;
  longitude: number;
  currentParticipants: number;
  maxParticipants: number;
  percentFilled: number;
  socialWorkDays: number | null;
  trophy: {
    id: string;
    name: string;
    description?: string;
    icon?: string;
    points: number;
  } | null;
  host: {
    id: string;
    username: string;
    fullName: string;
    isVerified: boolean;
  };
  requireApproval: boolean;
  attendanceMode: 'manual' | 'auto' | 'qr_code';
  checkInRadius: number;
  registrationState: ActivityRegistrationState;
  hasConflict: boolean;
  conflictWarning: string | null;
  conflictMessage: string | null;
  canRegister: boolean;
  ctaText: string;
  ctaDisabled: boolean;
  isHost: boolean;
  isPast: boolean;
  dynamicForm: {
    title: string | null;
    description: string | null;
    fields: DynamicFormField[];
  } | null;
  customForm: {
    title: string | null;
    description: string | null;
    fields: DynamicFormField[];
  } | null;
}

export function mapActivityToDetailViewModel(params: {
  activity: ActivityResponse;
  currentUserId?: string;
  myRequest?: JoinRequestResponse | null;
  conflictInfo?: ConflictInfo | null;
}): ActivityDetailViewModel {
  const { activity, currentUserId, myRequest, conflictInfo } = params;
  const isHost = !!currentUserId && currentUserId === activity.host_id;

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

  const isRegistered =
    myRequest?.status === 'approved' ||
    myRequest?.status === 'pending' ||
    false;

  const registrationState = isPast
    ? 'deadline_passed'
    : computeActivityRegistrationState({
        isRegistered,
        registrationStatus: myRequest?.status,
        currentParticipants,
        maxParticipants,
        hasConflict: !!conflictInfo?.has_conflict,
      });

  const startFormatted = `${startDate.toLocaleDateString('vi-VN')} • ${startDate.toLocaleTimeString(
    'vi-VN',
    { hour: '2-digit', minute: '2-digit' }
  )}`;

  const endFormatted = `${endDate.toLocaleDateString('vi-VN')} • ${endDate.toLocaleTimeString(
    'vi-VN',
    { hour: '2-digit', minute: '2-digit' }
  )}`;

  // Parse custom form fields
  const parsedFields: DynamicFormField[] = (activity.custom_form?.fields || []).map(
    (f, idx) => ({
      id: f.id || `field_${idx}`,
      label: f.label,
      fieldType: (f.field_type as DynamicFieldType) || 'text',
      isRequired: !!f.is_required,
      order: f.order ?? idx,
      options: (f as any).options || undefined,
    })
  );

  return {
    id: activity.id,
    title: activity.title,
    description: activity.description,
    category: activity.category || 'Chung',
    privacy: activity.privacy || 'public',
    startFormatted,
    endFormatted,
    locationName: activity.location_name || 'Khuôn viên trường',
    latitude: activity.latitude,
    longitude: activity.longitude,
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
          description: activity.trophy.description,
          icon: activity.trophy.icon,
          points: activity.trophy.points,
        }
      : null,
    host: {
      id: activity.host_id,
      username: activity.host?.username || 'Host',
      fullName: activity.host?.full_name || activity.host?.username || 'Host',
      isVerified: (activity.host as any)?.is_verified || false,
    },
    requireApproval: !!activity.require_approval,
    attendanceMode: activity.attendance_mode || 'manual',
    checkInRadius: activity.check_in_radius || 200,
    registrationState,
    hasConflict: !!conflictInfo?.has_conflict,
    conflictWarning: conflictInfo?.warning_message || null,
    conflictMessage: conflictInfo?.warning_message || null,
    canRegister:
      !isHost &&
      !isPast &&
      currentParticipants < maxParticipants &&
      (!myRequest || myRequest.status === 'cancelled' || myRequest.status === 'declined'),
    ctaText: isPast
      ? 'Đã hết hạn'
      : currentParticipants >= maxParticipants
      ? 'Hoạt động đã đầy'
      : myRequest?.status === 'approved'
      ? 'Đã tham gia'
      : myRequest?.status === 'pending'
      ? 'Đang chờ phê duyệt'
      : activity.require_approval
      ? 'Gửi yêu cầu tham gia'
      : 'Tham gia hoạt động',
    ctaDisabled:
      isPast ||
      currentParticipants >= maxParticipants ||
      myRequest?.status === 'approved' ||
      myRequest?.status === 'pending',
    isHost,
    isPast,
    dynamicForm: activity.custom_form
      ? {
          title: activity.custom_form.title,
          description: activity.custom_form.description,
          fields: parsedFields,
        }
      : null,
    customForm: activity.custom_form
      ? {
          title: activity.custom_form.title,
          description: activity.custom_form.description,
          fields: parsedFields,
        }
      : null,
  };
}

export function validateDynamicForm(
  fields: DynamicFormField[],
  responses: Record<string, any>
): { isValid: boolean; errors: Record<string, string> } {
  const errors: Record<string, string> = {};

  for (const field of fields) {
    if (field.isRequired) {
      const val = responses[field.label];
      if (val === undefined || val === null || String(val).trim() === '') {
        errors[field.label] = `Vui lòng điền "${field.label}"`;
      }
    }
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
}
