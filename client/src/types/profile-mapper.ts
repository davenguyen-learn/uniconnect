export type SectionStatus = 'loading' | 'success' | 'error';

export interface ProfileSectionState<T> {
  status: SectionStatus;
  data: T | null;
  error: string | null;
}

export interface FormattedRankBadge {
  title: string;
  badgeClass: string;
  glowColor: string;
}

/**
 * Maps verified server rank title to presentation styling tokens.
 * Invariant: Rank title is strictly derived from backend policy.
 */
export function mapRankToBadge(rankTitle: string): FormattedRankBadge {
  if (rankTitle.includes('Tiêu biểu') || rankTitle.includes('Ambassador') || rankTitle.includes('Đại sứ')) {
    return {
      title: rankTitle,
      badgeClass: 'rank-badge--ambassador',
      glowColor: '#f59e0b',
    };
  }
  if (rankTitle.includes('Năng nổ') || rankTitle.includes('Leader') || rankTitle.includes('Thủ lĩnh')) {
    return {
      title: rankTitle,
      badgeClass: 'rank-badge--leader',
      glowColor: '#8b5cf6',
    };
  }
  if (rankTitle.includes('Tích cực') || rankTitle.includes('Pioneer') || rankTitle.includes('Tiên phong')) {
    return {
      title: rankTitle,
      badgeClass: 'rank-badge--pioneer',
      glowColor: '#3b82f6',
    };
  }
  return {
    title: rankTitle,
    badgeClass: 'rank-badge--active',
    glowColor: '#10b981',
  };
}

/** Extracts user initials for avatar fallback */
export function getInitials(fullName?: string | null, username?: string | null): string {
  if (fullName && fullName.trim()) {
    const parts = fullName.trim().split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return parts[0].slice(0, 2).toUpperCase();
  }
  if (username && username.trim()) {
    return username.trim().slice(0, 2).toUpperCase();
  }
  return 'UC';
}

/** Formats ISO dates according to Vietnamese locale for presentation */
export function formatMemberSince(createdDateStr: string): string {
  const d = new Date(createdDateStr);
  return d.toLocaleDateString('vi-VN', {
    month: 'long',
    year: 'numeric',
  });
}

export function formatActivityDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

export function formatActivityTimeRange(startTimeStr: string, endTimeStr?: string | null): string {
  if (!startTimeStr) return '';
  const start = new Date(startTimeStr);
  const startDateStr = start.toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
  const startTimeVal = start.toLocaleTimeString('vi-VN', {
    hour: '2-digit',
    minute: '2-digit',
  });

  if (!endTimeStr) {
    return `${startTimeVal} • ${startDateStr}`;
  }

  const end = new Date(endTimeStr);
  const endDateStr = end.toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
  const endTimeVal = end.toLocaleTimeString('vi-VN', {
    hour: '2-digit',
    minute: '2-digit',
  });

  if (startDateStr === endDateStr) {
    return `${startTimeVal} - ${endTimeVal} • ${startDateStr}`;
  }
  return `${startTimeVal} ${startDateStr} - ${endTimeVal} ${endDateStr}`;
}
