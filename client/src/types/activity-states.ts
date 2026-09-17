/**
 * Domain State Machines & State Contracts for Activity Registration & Proximity Check-in.
 * UI components only render these states, without containing raw business logic.
 */

// ============================================================================
// 1. Activity Registration State Machine
// ============================================================================

export type ActivityRegistrationState =
  | 'available'        // Eligible, open slots, within deadline -> Primary Register button
  | 'checking_conflict'// Transient: checking personal calendar conflicts
  | 'conflict_warn'    // Conflict detected -> Warning dialog with user confirmation
  | 'registered'       // Already registered / approved -> Secondary Joined status
  | 'capacity_full'    // No seats left -> Disabled "Full" indicator
  | 'deadline_passed'  // Beyond registration_deadline -> Disabled "Closed" indicator
  | 'not_eligible';    // Restricted / not allowed

export type RegistrationEvent =
  | { type: 'SUBMIT_REGISTRATION' }
  | { type: 'CONFLICT_DETECTED'; conflictingEventTitle: string; timeRange: string }
  | { type: 'CONFIRM_CONFLICT_OVERRIDE' }
  | { type: 'CANCEL_REGISTRATION_INTENT' }
  | { type: 'CANCEL_PARTICIPATION' }
  | { type: 'CAPACITY_EXHAUSTED' }
  | { type: 'REGISTRATION_SUCCESS' };

// ============================================================================
// 2. Proximity Check-in State Machine (Untrusted Client GPS -> Server Validation)
// ============================================================================

export type CheckInState =
  | 'idle'                  // Ready for check-in action
  | 'requesting_location'   // Requesting navigator.geolocation
  | 'location_denied'       // Browser/OS permission denied
  | 'location_unavailable'  // Hardware/GPS unavailable
  | 'gps_accuracy_low'      // GPS accuracy radius > 100m (unreliable)
  | 'validating'            // Sending payload to server for validation
  | 'outside_radius'        // Server rejected: distance > activity.check_in_radius
  | 'session_closed'        // Server rejected: host session window inactive
  | 'already_confirmed'     // Idempotent: already confirmed attendance
  | 'success'               // Verified: attendance marked & trophy awarded
  | 'network_error';        // Network failure during server call

export type CheckInEvent =
  | { type: 'INITIATE_CHECK_IN' }
  | { type: 'LOCATION_GRANTED'; latitude: number; longitude: number; accuracy: number }
  | { type: 'LOCATION_ERROR'; error: 'denied' | 'unavailable' | 'timeout' }
  | { type: 'ACCURACY_TOO_LOW'; accuracy: number }
  | { type: 'SERVER_SUCCESS'; attendedAt: string; trophyAwarded?: any; socialWorkDays?: number }
  | { type: 'SERVER_REJECTED'; reason: 'outside_radius' | 'session_closed' | 'already_confirmed' | 'network' }
  | { type: 'RETRY' };

/** Helper to compute initial registration state from backend activity payload */
export function computeActivityRegistrationState(params: {
  isRegistered: boolean;
  registrationStatus?: 'pending' | 'approved' | 'declined' | 'cancelled';
  currentParticipants: number;
  maxParticipants: number;
  registrationDeadline?: string | null;
  hasConflict?: boolean;
}): ActivityRegistrationState {
  const {
    isRegistered,
    registrationStatus,
    currentParticipants,
    maxParticipants,
    registrationDeadline,
    hasConflict,
  } = params;

  if (isRegistered || registrationStatus === 'approved' || registrationStatus === 'pending') {
    return 'registered';
  }

  if (registrationDeadline && new Date() > new Date(registrationDeadline)) {
    return 'deadline_passed';
  }

  if (maxParticipants > 0 && currentParticipants >= maxParticipants) {
    return 'capacity_full';
  }

  if (hasConflict) {
    return 'conflict_warn';
  }

  return 'available';
}
