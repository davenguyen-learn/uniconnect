export type UserRole = 'student' | 'organization' | 'education_admin' | 'admin';

export interface NavItemConfig {
  id: string;
  label: string;
  path: string;
  iconName: string;
  /** Whether item is visible on LeftSidebar (Desktop) */
  showOnSidebar: boolean;
  /** Whether item is visible on BottomNav (Mobile) */
  showOnBottomNav: boolean;
  /** Roles allowed to view this navigation item. If omitted, visible to all authenticated users */
  allowedRoles?: UserRole[];
  /** Require verified organization status */
  requireVerifiedOrg?: boolean;
  /** Highlight as primary CTA (e.g. Floating Action Button on mobile) */
  isPrimaryAction?: boolean;
  /** Exact match for active state path */
  exact?: boolean;
}

export const MAIN_NAVIGATION_ITEMS: NavItemConfig[] = [
  {
    id: 'discovery',
    label: 'Khám phá',
    path: '/dashboard',
    iconName: 'Compass',
    showOnSidebar: true,
    showOnBottomNav: true,
  },
  {
    id: 'calendar',
    label: 'Lịch của tôi',
    path: '/calendar',
    iconName: 'Calendar',
    showOnSidebar: true,
    showOnBottomNav: true,
  },
  {
    id: 'create_activity',
    label: 'Tạo hoạt động',
    path: '/activities/create',
    iconName: 'PlusCircle',
    showOnSidebar: true,
    showOnBottomNav: true,
    isPrimaryAction: true,
    allowedRoles: ['organization', 'education_admin', 'admin'],
    requireVerifiedOrg: true,
  },
  {
    id: 'groups',
    label: 'Câu lạc bộ',
    path: '/groups',
    iconName: 'Users',
    showOnSidebar: true,
    showOnBottomNav: true,
  },
  {
    id: 'profile',
    label: 'Hồ sơ',
    path: '/profile',
    iconName: 'User',
    showOnSidebar: false, // On desktop, Profile card is docked at the bottom of the sidebar
    showOnBottomNav: true,
  },
];
