import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  Users,
  Calendar,
  Award,
  Globe,
  Lock,
  Inbox,
  UserPlus,
  LogOut,
  Settings,
  CalendarPlus,
  AlertCircle,
  AlertTriangle,
  Loader2,
  FileText,
  Camera,
  Trash2,
  Search,
  SlidersHorizontal,
  X,
  BookOpen,
  Heart,
  Trophy,
  GraduationCap,
  Lightbulb,
  Utensils,
  Coffee,
  Flame,
  PartyPopper,
  Gamepad2,
  Music,
  Compass,
  Crown,
  PauseCircle,
  PlayCircle
} from 'lucide-react';
import { resolveAvatarUrl } from '../../utils/avatar';
import { formatCtxh } from '../../utils/format';
import {
  groupsApi,
  type GroupDetailResponse
} from '../../api/groups';
import type { ActivityResponse } from '../../api/activities';
import {
  mapGroupStatsToViewModel,
  type GroupStatsViewModel
} from '../../types/groups-mapper';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../components/Toast/ToastContext';
import Button from '../../components/Button/Button';
import Input, { Textarea } from '../../components/Input/Input';
import ActivityCard from '../../components/ActivityCard/ActivityCard';
import { CoHostInboxModal } from '../../components/groups/CoHostInboxModal';
import { MemberManagementModal } from '../../components/groups/MemberManagementModal';
import './GroupDetail.css';

const categoryChips = [
  { id: 'all', label: 'Tất cả' },
  { id: 'Học tập', label: 'Học tập', icon: BookOpen },
  { id: 'Workshop', label: 'Workshop', icon: Lightbulb },
  { id: 'Tình nguyện', label: 'Tình nguyện', icon: Heart },
  { id: 'CTXH', label: 'CTXH', icon: GraduationCap },
  { id: 'Thể thao', label: 'Thể thao', icon: Trophy },
  { id: 'Vận động', label: 'Vận động', icon: Flame },
  { id: 'Hướng nghiệp', label: 'Hướng nghiệp', icon: Compass },
  { id: 'Giải trí', label: 'Giải trí', icon: PartyPopper },
  { id: 'Âm nhạc', label: 'Âm nhạc', icon: Music },
  { id: 'Game', label: 'Game', icon: Gamepad2 },
  { id: 'Cà phê', label: 'Cà phê', icon: Coffee },
  { id: 'Ăn uống', label: 'Ăn uống', icon: Utensils },
];

export default function GroupDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const toast = useToast();

  useEffect(() => {
    if (id === 'create' || id === 'new') {
      navigate('/groups/new', { replace: true });
    }
  }, [id, navigate]);

  const [group, setGroup] = useState<GroupDetailResponse | null>(null);
  const [stats, setStats] = useState<GroupStatsViewModel | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'about' | 'activities' | 'settings'>('activities');

  const [activities, setActivities] = useState<ActivityResponse[]>([]);
  const [loadingContent, setLoadingContent] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  // Activities Search & Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [scopeFilter, setScopeFilter] = useState<'all' | 'lead' | 'cohost'>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [timeFilter, setTimeFilter] = useState<'all' | 'upcoming' | 'past'>('all');
  const [filterCtxhOnly, setFilterCtxhOnly] = useState(false);
  const [filterTrophyOnly, setFilterTrophyOnly] = useState(false);
  const [hideConflicts, setHideConflicts] = useState(false);
  const [sortBy, setSortBy] = useState<'time_asc' | 'time_desc' | 'created_desc'>('time_asc');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery.trim());
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const activeFilterCount =
    (categoryFilter !== 'all' ? 1 : 0) +
    (scopeFilter !== 'all' ? 1 : 0) +
    (timeFilter !== 'all' ? 1 : 0) +
    (filterCtxhOnly ? 1 : 0) +
    (filterTrophyOnly ? 1 : 0) +
    (hideConflicts ? 1 : 0) +
    (sortBy !== 'time_asc' ? 1 : 0);

  const handleResetFilters = useCallback(() => {
    setSearchQuery('');
    setDebouncedSearch('');
    setScopeFilter('all');
    setCategoryFilter('all');
    setTimeFilter('all');
    setFilterCtxhOnly(false);
    setFilterTrophyOnly(false);
    setHideConflicts(false);
    setSortBy('time_asc');
  }, []);

  const leadCount = useMemo(() => activities.filter(a => a.group_id === id).length, [activities, id]);
  const cohostCount = useMemo(() => activities.filter(a => a.group_id !== id).length, [activities, id]);

  const filteredActivities = useMemo(() => {
    let result = [...activities];

    if (debouncedSearch) {
      const q = debouncedSearch.toLowerCase();
      result = result.filter(a => 
        a.title.toLowerCase().includes(q) ||
        (a.description && a.description.toLowerCase().includes(q)) ||
        (a.location_name && a.location_name.toLowerCase().includes(q)) ||
        (a.meeting_location && a.meeting_location.toLowerCase().includes(q))
      );
    }

    if (scopeFilter === 'lead') {
      result = result.filter(a => a.group_id === id);
    } else if (scopeFilter === 'cohost') {
      result = result.filter(a => a.group_id !== id);
    }

    if (categoryFilter !== 'all') {
      result = result.filter(a => a.category === categoryFilter);
    }

    const now = new Date();
    if (timeFilter === 'upcoming') {
      result = result.filter(a => new Date(a.end_time || a.start_time) >= now);
    } else if (timeFilter === 'past') {
      result = result.filter(a => new Date(a.end_time || a.start_time) < now);
    }

    if (filterCtxhOnly) {
      result = result.filter(a => typeof a.social_work_days === 'number' && a.social_work_days > 0);
    }

    if (filterTrophyOnly) {
      result = result.filter(a => !!a.trophy);
    }

    if (hideConflicts) {
      result = result.filter(a => !a.conflict_info?.has_conflict);
    }

    result.sort((a, b) => {
      const aStart = new Date(a.start_time).getTime();
      const bStart = new Date(b.start_time).getTime();
      const aCreated = new Date(a.created_at || a.start_time).getTime();
      const bCreated = new Date(b.created_at || b.start_time).getTime();

      if (sortBy === 'time_asc') {
        return aStart - bStart;
      } else if (sortBy === 'time_desc') {
        return bStart - aStart;
      } else if (sortBy === 'created_desc') {
        return bCreated - aCreated;
      }
      return 0;
    });

    return result;
  }, [activities, debouncedSearch, scopeFilter, categoryFilter, timeFilter, filterCtxhOnly, filterTrophyOnly, hideConflicts, sortBy, id]);

  // Modals
  const [showCoHostInbox, setShowCoHostInbox] = useState(false);
  const [showMemberManagement, setShowMemberManagement] = useState(false);
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [formResponses, setFormResponses] = useState<Record<string, any>>({});

  // Pending counts for badges
  const [pendingInvitesCount, setPendingInvitesCount] = useState(0);
  const [pendingRequestsCount, setPendingRequestsCount] = useState(0);

  // Settings form state
  const [settingsForm, setSettingsForm] = useState({
    name: '',
    description: '',
    publicDescription: '',
    privateDescription: '',
    privacy: 'public' as 'public' | 'private',
    requireApproval: true,
    allowActivities: true,
  });
  const [savingSettings, setSavingSettings] = useState(false);

  // Avatar upload state
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [avatarPreviewUrl, setAvatarPreviewUrl] = useState<string | null>(null);
  const [selectedAvatarFile, setSelectedAvatarFile] = useState<File | null>(null);
  const [avatarModalOpen, setAvatarModalOpen] = useState(false);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [avatarError, setAvatarError] = useState(false);
  const [showAvatarMenu, setShowAvatarMenu] = useState(false);
  const avatarMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (avatarMenuRef.current && !avatarMenuRef.current.contains(e.target as Node)) {
        setShowAvatarMenu(false);
      }
    };
    if (showAvatarMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showAvatarMenu]);

  useEffect(() => {
    setAvatarError(false);
  }, [group?.avatar_url]);

  const isMember = Boolean(group?.members?.some(m => m.user_id === user?.id));
  const memberRecord = group?.members?.find(m => m.user_id === user?.id);
  const isOwner = group?.owner_id === user?.id;
  const isAdmin = memberRecord?.role === 'admin' || isOwner;
  const isInactive = group?.status === 'inactive' || group?.status === 'suspended';

  const canCreateActivity = !isInactive && (isAdmin || (isMember && group?.allow_member_activities));

  const [suspendLoading, setSuspendLoading] = useState(false);
  const [showSuspendModal, setShowSuspendModal] = useState(false);
  const [transferMemberId, setTransferMemberId] = useState('');
  const [transferringOwner, setTransferringOwner] = useState(false);
  const [showTransferConfirmModal, setShowTransferConfirmModal] = useState(false);

  const loadGroupAndStats = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const [groupData, statsData] = await Promise.all([
        groupsApi.getGroup(id),
        groupsApi.getGroupStats(id),
      ]);
      setGroup(groupData);
      setStats(mapGroupStatsToViewModel(statsData));
      setSettingsForm({
        name: groupData.name,
        description: groupData.description || '',
        publicDescription: groupData.public_description || '',
        privateDescription: groupData.private_description || '',
        privacy: (groupData.privacy as any) || 'public',
        requireApproval: groupData.require_approval ?? true,
        allowActivities: groupData.allow_member_activities ?? true,
      });

      // If user is leadership, fetch badge counts
      if (groupData.owner_id === user?.id || groupData.members?.some(m => m.user_id === user?.id && m.role === 'admin')) {
        try {
          const [invRes, reqRes] = await Promise.all([
            groupsApi.getCoHostInvitations(id, { status: 'pending', limit: 1 }),
            groupsApi.getJoinRequests(id, { status: 'pending', limit: 1 }),
          ]);
          setPendingInvitesCount(invRes.length);
          setPendingRequestsCount(reqRes.length);
        } catch {
          // Silent fallback for badge counts
        }
      }
    } catch {
      toast.error('Không thể tải thông tin nhóm');
    } finally {
      setLoading(false);
    }
  }, [id, user?.id, toast]);

  useEffect(() => {
    loadGroupAndStats();
  }, [loadGroupAndStats]);

  useEffect(() => {
    if (activeTab === 'activities' && id) {
      loadActivities();
    }
  }, [activeTab, id, user?.id]);

  async function loadActivities() {
    if (!id) return;
    setLoadingContent(true);
    try {
      const data = await groupsApi.getGroupActivities(id, { limit: 50, include_past: true });
      setActivities(data.items);
    } catch {
      toast.error('Không thể tải danh sách hoạt động');
    } finally {
      setLoadingContent(false);
    }
  }

  async function handleJoinLeaveClick() {
    if (!id || actionLoading) return;

    if (isMember) {
      if (isOwner) {
        toast.error('Trưởng nhóm không thể rời nhóm. Hãy chuyển quyền trước.');
        return;
      }
      if (!window.confirm('Bạn có chắc chắn muốn rời khỏi nhóm này?')) return;
      setActionLoading(true);
      try {
        await groupsApi.leaveGroup(id);
        toast.success('Đã rời nhóm');
        loadGroupAndStats();
      } catch {
        toast.error('Không thể rời nhóm lúc này');
      } finally {
        setActionLoading(false);
      }
    } else {
      if (group?.custom_form && group.custom_form.fields?.length > 0) {
        setShowJoinModal(true);
      } else {
        submitJoinGroup({});
      }
    }
  }

  async function submitJoinGroup(responses: Record<string, any>) {
    if (!id) return;
    setActionLoading(true);
    try {
      await groupsApi.joinGroup(id, { form_responses: responses });
      if (group?.require_approval) {
        toast.success('Đã gửi đơn tham gia nhóm, vui lòng chờ Ban Quản Trị duyệt!');
      } else {
        toast.success('Chào mừng bạn đã gia nhập nhóm!');
      }
      setShowJoinModal(false);
      loadGroupAndStats();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Không thể gửi đơn tham gia');
    } finally {
      setActionLoading(false);
    }
  }

  async function handleSaveSettings(e: React.FormEvent) {
    e.preventDefault();
    if (!id || savingSettings) return;

    setSavingSettings(true);
    try {
      await groupsApi.updateGroup(id, {
        name: settingsForm.name,
        description: settingsForm.description,
        public_description: settingsForm.publicDescription,
        private_description: settingsForm.privateDescription,
        privacy: settingsForm.privacy,
        require_approval: settingsForm.requireApproval,
        allow_member_activities: settingsForm.allowActivities,
      });
      toast.success('Đã cập nhật thông tin nhóm');
      loadGroupAndStats();
    } catch {
      toast.error('Không thể cập nhật thông tin');
    } finally {
      setSavingSettings(false);
    }
  }

  async function handleToggleSuspend() {
    if (!id || !group || suspendLoading) return;
    setSuspendLoading(true);
    try {
      if (isInactive) {
        await groupsApi.resumeGroup(id);
        toast.success('Đã kích hoạt lại hoạt động nhóm thành công!');
      } else {
        await groupsApi.suspendGroup(id);
        toast.success('Đã tạm dừng hoạt động nhóm.');
      }
      setShowSuspendModal(false);
      loadGroupAndStats();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Không thể thay đổi trạng thái nhóm');
    } finally {
      setSuspendLoading(false);
    }
  }

  async function handleTransferOwnership() {
    if (!id || !transferMemberId || transferringOwner) return;
    setTransferringOwner(true);
    try {
      await groupsApi.transferOwnership(id, transferMemberId);
      toast.success('Đã chuyển giao quyền Trưởng nhóm thành công!');
      setShowTransferConfirmModal(false);
      setTransferMemberId('');
      loadGroupAndStats();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Chuyển quyền Trưởng nhóm thất bại');
    } finally {
      setTransferringOwner(false);
    }
  }

  const handleAvatarFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Ảnh vượt quá dung lượng tối đa 5MB');
      return;
    }
    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      toast.error('Chỉ hỗ trợ file ảnh định dạng JPEG, PNG hoặc WebP');
      return;
    }
    setSelectedAvatarFile(file);
    const preview = URL.createObjectURL(file);
    setAvatarPreviewUrl(preview);
    setAvatarModalOpen(true);
    e.target.value = '';
  };

  const closeAvatarModal = () => {
    if (avatarPreviewUrl) {
      URL.revokeObjectURL(avatarPreviewUrl);
      setAvatarPreviewUrl(null);
    }
    setSelectedAvatarFile(null);
    setAvatarModalOpen(false);
  };

  const handleUploadConfirm = async () => {
    if (!selectedAvatarFile || !id) return;
    setUploadingAvatar(true);
    try {
      const updated = await groupsApi.uploadAvatar(id, selectedAvatarFile);
      setGroup(updated);
      setAvatarError(false);
      closeAvatarModal();
      toast.success('Đã cập nhật ảnh đại diện nhóm thành công');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Tải ảnh lên thất bại');
    } finally {
      setUploadingAvatar(false);
    }
  };

  const handleDeleteAvatar = async () => {
    if (!id || !window.confirm('Bạn có chắc muốn xóa ảnh đại diện của nhóm?')) return;
    try {
      const updated = await groupsApi.deleteAvatar(id);
      setGroup(updated);
      setAvatarError(false);
      toast.success('Đã xóa ảnh đại diện nhóm');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Xóa ảnh đại diện thất bại');
    }
  };


  if (loading) {
    return (
      <div className="container club-loading-state">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600 mb-3" />
        <p className="text-slate-500 font-medium">Đang tải thông tin nhóm...</p>
      </div>
    );
  }

  if (!group) {
    return (
      <div className="container club-empty-page">
        <AlertCircle className="w-12 h-12 text-rose-500 mb-2" />
        <h2>Không tìm thấy nhóm</h2>
        <Link to="/groups" className="mt-4 text-indigo-600 hover:underline font-medium">
          Trở về danh sách nhóm
        </Link>
      </div>
    );
  }

  return (
    <div className="container group-detail-page">
      {/* ── 1. Hero Showcase Banner ── */}
      <div className="club-hero-card glass">
        <div className="club-hero-cover">
          <div className="club-hero-badge-strip">

            <span className={`club-pill-badge ${group.privacy === 'private' ? 'club-pill-private' : 'club-pill-public'}`}>
              {group.privacy === 'private' ? (
                <>
                  <Lock className="w-3.5 h-3.5" /> Riêng tư
                </>
              ) : (
                <>
                  <Globe className="w-3.5 h-3.5" /> Công khai
                </>
              )}
            </span>

            {isInactive && (
              <span
                className="club-pill-badge"
                style={{ backgroundColor: '#fef3c7', color: '#92400e', border: '1px solid #fcd34d' }}
              >
                ⏸ Tạm dừng hoạt động
              </span>
            )}
          </div>
        </div>

        <div className="club-hero-body">
          <div className="club-hero-profile-row">
            {/* Club Emblem */}
            <div className="club-emblem-wrapper">
              <div className="club-emblem">
                {group.avatar_url && !avatarError ? (
                  <img
                    src={resolveAvatarUrl(group.avatar_url)!}
                    alt={group.name}
                    className="club-emblem-image"
                    onError={() => setAvatarError(true)}
                  />
                ) : (
                  <span>{group.name.charAt(0).toUpperCase()}</span>
                )}
              </div>

              {isAdmin && (
                <div className="club-emblem-actions" ref={avatarMenuRef}>
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={(e) => {
                      setShowAvatarMenu(false);
                      handleAvatarFileChange(e);
                    }}
                    accept="image/jpeg,image/png,image/webp"
                    style={{ display: 'none' }}
                  />
                  <button
                    type="button"
                    className="club-emblem-action-btn club-emblem-settings-btn"
                    onClick={() => setShowAvatarMenu(prev => !prev)}
                    title="Cài đặt ảnh đại diện"
                    aria-label="Cài đặt ảnh đại diện"
                  >
                    <Settings className="w-4 h-4" />
                  </button>

                  {showAvatarMenu && (
                    <div className="club-emblem-menu">
                      <button
                        type="button"
                        className="club-emblem-menu-item"
                        onClick={() => {
                          setShowAvatarMenu(false);
                          fileInputRef.current?.click();
                        }}
                      >
                        <Camera className="w-3.5 h-3.5" />
                        <span>Thay đổi ảnh</span>
                      </button>
                      {group.avatar_url && (
                        <button
                          type="button"
                          className="club-emblem-menu-item club-emblem-menu-item--danger"
                          onClick={() => {
                            setShowAvatarMenu(false);
                            handleDeleteAvatar();
                          }}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                          <span>Xóa ảnh</span>
                        </button>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Title & Info */}
            <div className="club-hero-details">
              <h1 className="club-name-heading">{group.name}</h1>
              <p className="club-short-desc" title={group.description || undefined}>{group.description || 'Chưa có mô tả ngắn'}</p>
            </div>
          </div>

          {/* Action Buttons Row */}
          <div className="club-hero-actions">
            {!isAdmin && (
              <Button
                variant="secondary"
                onClick={() => setShowMemberManagement(true)}
                className="view-members-btn flex items-center gap-1.5"
                title="Xem danh sách thành viên"
              >
                <Users className="w-4 h-4 mr-1" />
                Danh sách thành viên
              </Button>
            )}

            <Button
              variant={isMember ? 'secondary' : 'primary'}
              onClick={handleJoinLeaveClick}
              loading={actionLoading}
              disabled={isInactive && !isMember}
              className={`join-leave-btn ${isMember ? 'club-leave-btn' : ''}`}
            >
              {isMember ? (
                <>
                  <LogOut className="w-4 h-4 mr-1.5" />
                  Rời nhóm
                </>
              ) : isInactive ? (
                <>
                  <AlertTriangle className="w-4 h-4 mr-1.5" />
                  Đã dừng hoạt động
                </>
              ) : (
                <>
                  <UserPlus className="w-4 h-4 mr-1.5" />
                  {group.require_approval ? 'Gửi đơn gia nhập' : 'Tham gia nhóm'}
                </>
              )}
            </Button>
          </div>

          {/* Leadership Command Bar (Owner / Admin) */}
          {isAdmin && (
            <div className="club-leadership-toolbar">
              <div className="club-leadership-title">
                Ban Quản Trị
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <button
                  onClick={() => setShowCoHostInbox(true)}
                  className="leadership-tool-btn"
                >
                  <Inbox className="w-4 h-4 text-indigo-500" />
                  Hộp thư mời đồng tổ chức
                  {pendingInvitesCount > 0 && (
                    <span className="badge-pill bg-amber-500 text-white">
                      {pendingInvitesCount}
                    </span>
                  )}
                </button>
                <button
                  onClick={() => setShowMemberManagement(true)}
                  className="leadership-tool-btn"
                >
                  <Users className="w-4 h-4 text-blue-500" />
                  Quản lý Thành viên
                  {pendingRequestsCount > 0 && (
                    <span className="badge-pill bg-rose-500 text-white">
                      {pendingRequestsCount}
                    </span>
                  )}
                </button>
                {canCreateActivity && (
                  <Link to={`/activities/new?group_id=${id}`} state={{ group_id: id }}>
                    <button className="leadership-tool-btn leadership-tool-btn--primary">
                      <CalendarPlus className="w-4 h-4" />
                      Tạo hoạt động mới
                    </button>
                  </Link>
                )}
                {isOwner && (
                  <button
                    onClick={() => setShowSuspendModal(true)}
                    className="leadership-tool-btn"
                    title={isInactive ? 'Kích hoạt lại hoạt động nhóm' : 'Tạm dừng hoạt động nhóm'}
                  >
                    {isInactive ? (
                      <>
                        <PlayCircle className="w-4 h-4 text-emerald-500" />
                        Tiếp tục hoạt động
                      </>
                    ) : (
                      <>
                        <PauseCircle className="w-4 h-4 text-amber-500" />
                        Tạm dừng hoạt động
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Inactive / Suspended Warning Alert */}
      {isInactive && (
        <div
          style={{
            margin: '18px 0',
            padding: '12px 18px',
            borderRadius: 14,
            backgroundColor: '#fffbeb',
            border: '1px solid #fde68a',
            color: '#92400e',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 12,
            fontSize: '0.95rem',
            fontWeight: 500,
            boxShadow: 'var(--shadow-sm)',
            flexWrap: 'wrap',
          }}
        >
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 flex-shrink-0 text-amber-600" />
            <span>
              Nhóm này hiện <strong>đang tạm dừng hoạt động</strong>. Các tính năng tạo hoạt động mới và gửi đơn tham gia tạm thời bị khóa.
            </span>
          </div>
          {isOwner && (
            <Button
              type="button"
              variant="secondary"
              onClick={() => setShowSuspendModal(true)}
              className="text-xs shrink-0 bg-white hover:bg-amber-100 text-amber-900 border-amber-300"
            >
              <PlayCircle className="w-4 h-4 mr-1 text-emerald-600" />
              Tiếp tục hoạt động
            </Button>
          )}
        </div>
      )}

      {/* ── 2. The 3 Golden Server-Derived Stats ── */}
      <div className="club-stats-grid">
        <div
          className="club-stat-card glass cursor-pointer"
          onClick={() => setShowMemberManagement(true)}
          title="Nhấp để xem danh sách thành viên"
        >
          <div className="club-stat-icon-wrapper">
            <Users className="w-6 h-6" />
          </div>
          <div className="club-stat-meta">
            <span className="club-stat-value">{stats?.memberCount ?? group.member_count}</span>
            <span className="club-stat-label">Thành viên chính thức</span>
          </div>
        </div>

        <div className="club-stat-card glass">
          <div className="club-stat-icon-wrapper">
            <Calendar className="w-6 h-6" />
          </div>
          <div className="club-stat-meta">
            <span className="club-stat-value">{stats?.totalActivitiesCount ?? 0}</span>
            <span className="club-stat-label">Hoạt động đã tổ chức</span>
          </div>
        </div>

        <div className="club-stat-card glass">
          <div className="club-stat-icon-wrapper">
            <Award className="w-6 h-6" />
          </div>
          <div className="club-stat-meta">
            <span className="club-stat-value">{formatCtxh(stats?.totalCtxhContributed)}</span>
            <span className="club-stat-label">Tổng cống hiến CTXH</span>
          </div>
        </div>
      </div>

      {/* ── 3. Tabs Navigation ── */}
      <div className="club-nav-tabs">
        <button
          className={`club-nav-tab ${activeTab === 'activities' ? 'active' : ''}`}
          onClick={() => setActiveTab('activities')}
        >
          <Calendar className="w-4 h-4 mr-2" />
          Hoạt động ({activities.length})
        </button>
        <button
          className={`club-nav-tab ${activeTab === 'about' ? 'active' : ''}`}
          onClick={() => setActiveTab('about')}
        >
          <Globe className="w-4 h-4 mr-2" />
          Giới thiệu
        </button>

        {isOwner && (
          <button
            className={`club-nav-tab ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            <Settings className="w-4 h-4 mr-2" />
            Cài đặt nhóm
          </button>
        )}
      </div>

      {/* ── 4. Tab Content ── */}
      <div className="club-tab-content">
        {activeTab === 'activities' && (
          <div className="activities-section space-y-4">
            {/* Search Bar & Advanced Filter Toggle */}
            <div className="group-activity-search-container">
              <div className="dashboard-search-bar">
                <Search size={18} className="dashboard-search-icon" />
                <input
                  type="text"
                  className="dashboard-search-input"
                  placeholder="Tìm kiếm theo tên hoạt động, địa điểm, chủ đề..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  aria-label="Tìm kiếm hoạt động trong nhóm"
                />
                {searchQuery && (
                  <button
                    type="button"
                    className="dashboard-search-clear"
                    onClick={() => setSearchQuery('')}
                    aria-label="Xóa nội dung tìm kiếm"
                  >
                    <X size={15} />
                  </button>
                )}
              </div>

              <button
                type="button"
                className={`chip-filter-toggle ${showAdvancedFilters ? 'chip-filter-toggle--open' : ''} ${activeFilterCount > 0 ? 'chip-filter-toggle--has-active' : ''}`}
                onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                title="Bộ lọc nâng cao"
              >
                <SlidersHorizontal size={16} />
                <span className="chip-filter-toggle-text">Bộ lọc</span>
                {activeFilterCount > 0 && (
                  <span className="filter-count-badge">{activeFilterCount}</span>
                )}
              </button>
            </div>

            {/* Active Filters Summary */}
            {activeFilterCount > 0 && !showAdvancedFilters && (
              <div className="group-active-filters-row">
                <span className="active-filters-title">Đang lọc:</span>
                {scopeFilter !== 'all' && (
                  <span className="active-filter-pill">
                    <span>{scopeFilter === 'lead' ? 'Nhóm chủ trì' : 'Đồng tổ chức'}</span>
                    <button type="button" onClick={() => setScopeFilter('all')}><X size={12} /></button>
                  </span>
                )}
                {categoryFilter !== 'all' && (
                  <span className="active-filter-pill">
                    <span>{categoryChips.find(c => c.id === categoryFilter)?.label || categoryFilter}</span>
                    <button type="button" onClick={() => setCategoryFilter('all')}><X size={12} /></button>
                  </span>
                )}
                {timeFilter !== 'all' && (
                  <span className="active-filter-pill">
                    <span>{timeFilter === 'upcoming' ? 'Sắp diễn ra' : 'Đã kết thúc'}</span>
                    <button type="button" onClick={() => setTimeFilter('all')}><X size={12} /></button>
                  </span>
                )}
                {filterCtxhOnly && (
                  <span className="active-filter-pill">
                    <span>Có CTXH</span>
                    <button type="button" onClick={() => setFilterCtxhOnly(false)}><X size={12} /></button>
                  </span>
                )}
                {filterTrophyOnly && (
                  <span className="active-filter-pill">
                    <span>Có danh hiệu</span>
                    <button type="button" onClick={() => setFilterTrophyOnly(false)}><X size={12} /></button>
                  </span>
                )}
                {hideConflicts && (
                  <span className="active-filter-pill">
                    <span>Ẩn trùng lịch</span>
                    <button type="button" onClick={() => setHideConflicts(false)}><X size={12} /></button>
                  </span>
                )}
                {sortBy !== 'time_asc' && (
                  <span className="active-filter-pill">
                    <span>{sortBy === 'time_desc' ? 'Xếp: Xa nhất' : 'Xếp: Mới đăng'}</span>
                    <button type="button" onClick={() => setSortBy('time_asc')}><X size={12} /></button>
                  </span>
                )}
                <button
                  type="button"
                  className="btn-clear-all-filters"
                  onClick={handleResetFilters}
                >
                  Đặt lại
                </button>
              </div>
            )}

            {/* Advanced Filters Panel */}
            {showAdvancedFilters && (
              <div className="group-filters-panel">
                {/* 1. Danh mục hoạt động */}
                <div className="filters-panel-section">
                  <span className="filters-panel-title">Danh mục hoạt động</span>
                  <div className="filters-panel-chips">
                    {categoryChips.map((chip) => {
                      const IconComponent = chip.icon;
                      const isActive = categoryFilter === chip.id;
                      return (
                        <button
                          key={chip.id}
                          type="button"
                          className={`chip-btn ${isActive ? 'chip-btn--active' : ''}`}
                          onClick={() => setCategoryFilter(chip.id)}
                        >
                          {IconComponent && <IconComponent size={14} className="chip-btn__icon" />}
                          <span>{chip.label}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Vai trò tổ chức */}
                <div className="filters-panel-section pt-2 border-t border-[var(--color-glass-border)]">
                  <span className="filters-panel-title">Vai trò tổ chức của nhóm</span>
                  <div className="flex gap-2 flex-wrap">
                    <button
                      type="button"
                      className={`chip-btn ${scopeFilter === 'all' ? 'chip-btn--active' : ''}`}
                      onClick={() => setScopeFilter('all')}
                    >
                      Tất cả ({activities.length})
                    </button>
                    <button
                      type="button"
                      className={`chip-btn ${scopeFilter === 'lead' ? 'chip-btn--active' : ''}`}
                      onClick={() => setScopeFilter('lead')}
                    >
                      Nhóm chủ trì ({leadCount})
                    </button>
                    <button
                      type="button"
                      className={`chip-btn ${scopeFilter === 'cohost' ? 'chip-btn--active' : ''}`}
                      onClick={() => setScopeFilter('cohost')}
                    >
                      🤝 Đồng tổ chức ({cohostCount})
                    </button>
                  </div>
                </div>

                {/* 2. Trạng thái & Sắp xếp */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-[var(--color-glass-border)]">
                  <div className="filters-panel-section">
                    <span className="filters-panel-title">Thời gian diễn ra</span>
                    <div className="flex gap-2 flex-wrap">
                      <button
                        type="button"
                        className={`chip-btn ${timeFilter === 'all' ? 'chip-btn--active' : ''}`}
                        onClick={() => setTimeFilter('all')}
                      >
                        Tất cả
                      </button>
                      <button
                        type="button"
                        className={`chip-btn ${timeFilter === 'upcoming' ? 'chip-btn--active' : ''}`}
                        onClick={() => setTimeFilter('upcoming')}
                      >
                        Sắp diễn ra
                      </button>
                      <button
                        type="button"
                        className={`chip-btn ${timeFilter === 'past' ? 'chip-btn--active' : ''}`}
                        onClick={() => setTimeFilter('past')}
                      >
                        Đã kết thúc
                      </button>
                    </div>
                  </div>

                  <div className="filters-panel-section">
                    <span className="filters-panel-title">Sắp xếp theo</span>
                    <div className="flex gap-2 flex-wrap">
                      <button
                        type="button"
                        className={`chip-btn ${sortBy === 'time_asc' ? 'chip-btn--active' : ''}`}
                        onClick={() => setSortBy('time_asc')}
                      >
                        Sắp diễn ra
                      </button>
                      <button
                        type="button"
                        className={`chip-btn ${sortBy === 'time_desc' ? 'chip-btn--active' : ''}`}
                        onClick={() => setSortBy('time_desc')}
                      >
                        Xa nhất
                      </button>
                      <button
                        type="button"
                        className={`chip-btn ${sortBy === 'created_desc' ? 'chip-btn--active' : ''}`}
                        onClick={() => setSortBy('created_desc')}
                      >
                        Mới đăng
                      </button>
                    </div>
                  </div>
                </div>

                {/* 3. Tiêu chí đặc biệt (Checkboxes) */}
                <div className="filters-panel-footer">
                  <div className="flex items-center gap-4 flex-wrap">
                    <label className="filter-checkbox-label">
                      <input
                        type="checkbox"
                        checked={filterCtxhOnly}
                        onChange={(e) => setFilterCtxhOnly(e.target.checked)}
                      />
                      <span>Chỉ hoạt động có CTXH</span>
                    </label>

                    <label className="filter-checkbox-label">
                      <input
                        type="checkbox"
                        checked={filterTrophyOnly}
                        onChange={(e) => setFilterTrophyOnly(e.target.checked)}
                      />
                      <span>Có danh hiệu</span>
                    </label>

                    <label className="filter-checkbox-label">
                      <input
                        type="checkbox"
                        checked={hideConflicts}
                        onChange={(e) => setHideConflicts(e.target.checked)}
                      />
                      <span>Ẩn trùng lịch cá nhân</span>
                    </label>
                  </div>

                  <button
                    type="button"
                    className="btn-clear-all-filters"
                    onClick={handleResetFilters}
                  >
                    Đặt lại bộ lọc
                  </button>
                </div>
              </div>
            )}

            {/* Activities Results */}
            {loadingContent ? (
              <div className="flex flex-col items-center justify-center py-16 text-slate-400">
                <Loader2 className="w-8 h-8 animate-spin mb-2" />
                <p className="text-sm">Đang tải hoạt động...</p>
              </div>
            ) : filteredActivities.length > 0 ? (
              <div className="activities-grid">
                {filteredActivities.map((activity) => (
                  <ActivityCard
                    key={activity.id}
                    activity={activity}
                    onShare={(actId) => {
                      const shareUrl = `${window.location.origin}/activities/${actId}`;
                      navigator.clipboard.writeText(shareUrl).then(() => {
                        toast.success('Đã sao chép liên kết hoạt động!');
                      }).catch(() => {
                        toast.info(`Liên kết: ${shareUrl}`);
                      });
                    }}
                  />
                ))}
              </div>
            ) : activities.length > 0 ? (
              /* When filters produce 0 results */
              <div className="empty-filter-results-box">
                <Search className="w-10 h-10 text-slate-300 mb-2" />
                <h4 className="text-base font-semibold text-slate-700">
                  Không tìm thấy hoạt động phù hợp
                </h4>
                <p className="text-xs text-slate-400 max-w-sm mt-1 mb-4">
                  Không có hoạt động nào trong nhóm thỏa mãn các điều kiện tìm kiếm hoặc bộ lọc hiện tại.
                </p>
                <Button size="sm" variant="secondary" onClick={handleResetFilters}>
                  Xóa bộ lọc
                </Button>
              </div>
            ) : (
              /* When group genuinely has 0 activities */
              <div className="glass empty-activities-box">
                <Calendar className="w-12 h-12 text-slate-300 mb-3" />
                <h4 className="text-base font-semibold text-slate-700">
                  Chưa có hoạt động nào được tổ chức
                </h4>
                <p className="text-xs text-slate-400 max-w-sm mt-1 mb-4">
                  Khi nhóm chủ trì hoặc tham gia Đồng tổ chức hoạt động ngoại khóa, thông tin sẽ xuất hiện tại đây.
                </p>
                {canCreateActivity && (
                  <Link to={`/activities/new?group_id=${id}`} state={{ group_id: id }}>
                    <Button size="sm">Tạo hoạt động đầu tiên</Button>
                  </Link>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'about' && (
          <div className="about-section glass p-6 rounded-2xl space-y-6">
            {!group.public_description?.trim() && !group.description?.trim() && (!isMember || !group.private_description?.trim()) ? (
              <div className="flex flex-col items-center justify-center py-10 text-center text-slate-400">
                <FileText className="w-10 h-10 mb-2.5 text-slate-300" />
                <p className="text-sm font-medium text-slate-600">
                  Group chưa có giới thiệu hay điều lệ nào
                </p>
                <p className="text-xs text-slate-400 mt-1 max-w-sm">
                  Ban quản trị nhóm chưa cập nhật phần giới thiệu hoặc điều lệ hoạt động cho nhóm này.
                </p>
              </div>
            ) : (
              <>
                {(group.public_description || group.description) && (
                  <div>
                    <p className="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap">
                      {group.public_description || group.description}
                    </p>
                  </div>
                )}

                {isMember ? (
                  group.private_description && (
                    <div className="p-4 rounded-xl bg-indigo-50/50 border border-indigo-100">
                      <h3 className="text-sm font-bold text-indigo-900 mb-1 flex items-center gap-2">
                        <Lock className="w-4 h-4 text-indigo-600" />
                        Thông tin & Kênh liên lạc nội bộ
                      </h3>
                      <p className="text-xs text-indigo-800/80 leading-relaxed whitespace-pre-wrap">
                        {group.private_description}
                      </p>
                    </div>
                  )
                ) : (
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-500 flex items-center gap-2">
                    <Lock className="w-4 h-4 text-slate-400" />
                    <span>Nội quy và các liên kết trao đổi nội bộ chỉ hiển thị cho thành viên chính thức.</span>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {activeTab === 'settings' && isOwner && (
          <div className="space-y-6">
            {/* 1. General Info & Permissions */}
            <div className="settings-section glass p-6 rounded-2xl">
              <h3 className="text-base font-bold text-slate-900 mb-1">Cài đặt thông tin & Hoạt động</h3>
              <p className="text-xs text-slate-500 mb-5">Quản lý tên, mô tả và quyền hạn cơ bản của thành viên trong nhóm.</p>

              <form onSubmit={handleSaveSettings} className="settings-form max-w-xl space-y-4">
                <Input
                  label="Tên nhóm"
                  value={settingsForm.name}
                  onChange={e => setSettingsForm({ ...settingsForm, name: e.target.value })}
                  required
                />
                <Textarea
                  label="Mô tả ngắn (hiển thị trên thẻ tìm kiếm)"
                  value={settingsForm.description}
                  onChange={e => setSettingsForm({ ...settingsForm, description: e.target.value })}
                />
                <Textarea
                  label="Tổng quan công khai"
                  value={settingsForm.publicDescription}
                  onChange={e => setSettingsForm({ ...settingsForm, publicDescription: e.target.value })}
                />
                <Textarea
                  label="Mô tả & Kênh liên lạc nội bộ (Chỉ thành viên thấy)"
                  value={settingsForm.privateDescription}
                  onChange={e => setSettingsForm({ ...settingsForm, privateDescription: e.target.value })}
                />

                <div className="form-group">
                  <label htmlFor="privacy_select" className="form-label text-sm font-semibold">
                    Chế độ hiển thị
                  </label>
                  <select
                    id="privacy_select"
                    className="form-select group-settings-select"
                    value={settingsForm.privacy}
                    onChange={e => setSettingsForm({ ...settingsForm, privacy: e.target.value as any })}
                  >
                    <option value="public">Công khai (Ai cũng có thể tìm thấy)</option>
                    <option value="private">Riêng tư (Chỉ thành viên thấy nội dung)</option>
                  </select>
                </div>

                <div className="space-y-3 pt-2">
                  <label className="group-switch-row">
                    <span className="group-switch-label">
                      Yêu cầu Ban Quản Trị duyệt đơn để gia nhập
                    </span>
                    <input
                      type="checkbox"
                      className="sr-only"
                      checked={settingsForm.requireApproval}
                      onChange={(e) => setSettingsForm({ ...settingsForm, requireApproval: e.target.checked })}
                    />
                    <div className={`group-toggle-switch ${settingsForm.requireApproval ? 'on' : ''}`}>
                      <span className="group-toggle-handle" />
                    </div>
                  </label>

                  <label className="group-switch-row">
                    <span className="group-switch-label">
                      Cho phép thành viên tạo hoạt động ngoại khóa
                    </span>
                    <input
                      type="checkbox"
                      className="sr-only"
                      checked={settingsForm.allowActivities}
                      onChange={(e) => setSettingsForm({ ...settingsForm, allowActivities: e.target.checked })}
                    />
                    <div className={`group-toggle-switch ${settingsForm.allowActivities ? 'on' : ''}`}>
                      <span className="group-toggle-handle" />
                    </div>
                  </label>
                </div>

                <div className="pt-4">
                  <Button type="submit" loading={savingSettings}>
                    Lưu thay đổi
                  </Button>
                </div>
              </form>
            </div>

            {/* 2. Group Operation Status */}
            <div className="settings-section glass p-6 rounded-2xl">
              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div>
                  <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 mb-1">
                    {isInactive ? (
                      <PauseCircle className="w-5 h-5 text-amber-500" />
                    ) : (
                      <PlayCircle className="w-5 h-5 text-emerald-500" />
                    )}
                    Trạng thái hoạt động của nhóm
                  </h3>
                  <p className="text-xs text-slate-500 max-w-lg leading-relaxed">
                    {isInactive
                      ? 'Nhóm hiện đang tạm dừng hoạt động. Các thành viên không thể tạo hoạt động mới và sinh viên bên ngoài không thể gửi đơn tham gia.'
                      : 'Nhóm đang hoạt động bình thường. Thành viên và Ban Quản Trị có thể tổ chức hoạt động và tuyển thành viên mới.'}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
                      isInactive
                        ? 'bg-amber-50 text-amber-800 border border-amber-200'
                        : 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                    }`}
                  >
                    <span className={`w-2 h-2 rounded-full ${isInactive ? 'bg-amber-500' : 'bg-emerald-500'}`} />
                    {isInactive ? 'Đang tạm dừng' : 'Đang hoạt động'}
                  </span>
                </div>
              </div>

              <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between flex-wrap gap-3">
                <p className="text-xs text-slate-500">
                  {isInactive
                    ? 'Bạn có thể kích hoạt lại để câu lạc bộ/nhóm tiếp tục hoạt động bất cứ lúc nào.'
                    : 'Tạm dừng sẽ khóa tạm thời các chức năng nộp đơn và tạo hoạt động mới.'}
                </p>
                <Button
                  type="button"
                  variant={isInactive ? 'primary' : 'secondary'}
                  onClick={() => setShowSuspendModal(true)}
                  className="flex items-center gap-1.5"
                >
                  {isInactive ? (
                    <>
                      <PlayCircle className="w-4 h-4 text-emerald-500 mr-1" />
                      Tiếp tục hoạt động
                    </>
                  ) : (
                    <>
                      <PauseCircle className="w-4 h-4 text-amber-600 mr-1" />
                      Tạm dừng hoạt động
                    </>
                  )}
                </Button>
              </div>
            </div>

            {/* 3. Transfer Group Ownership */}
            <div className="settings-section glass p-6 rounded-2xl border border-amber-100/60">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-xl bg-amber-50 flex items-center justify-center text-amber-600 shrink-0">
                  <Crown className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900 mb-1">
                    Chuyển giao quyền Trưởng nhóm
                  </h3>
                  <p className="text-xs text-slate-500 leading-relaxed max-w-xl">
                    Chuyển giao toàn quyền điều hành câu lạc bộ/nhóm cho một thành viên chính thức khác.
                    Sau khi chuyển nhượng, người được chỉ định sẽ là <strong>Trưởng nhóm (Owner)</strong>,
                    và bạn sẽ giữ vai trò <strong>Quản trị viên (Admin)</strong>.
                  </p>
                </div>
              </div>

              <div className="mt-5 pt-4 border-t border-slate-100 max-w-xl space-y-3">
                <label className="text-xs font-semibold text-slate-700 block">
                  Chọn thành viên tiếp quản:
                </label>
                <div className="flex gap-2 flex-wrap sm:flex-nowrap">
                  <select
                    className="form-select flex-1 p-2.5 rounded-xl border border-slate-200 text-sm bg-white focus:outline-none focus:border-amber-400"
                    value={transferMemberId}
                    onChange={(e) => setTransferMemberId(e.target.value)}
                  >
                    <option value="">-- Chọn thành viên chính thức trong nhóm --</option>
                    {group.members
                      ?.filter((m) => m.user_id !== group.owner_id)
                      .map((m) => (
                        <option key={m.user_id} value={m.user_id}>
                          {m.full_name || m.username || 'Thành viên'} (@{m.username || 'user'})
                          {m.role === 'admin' ? ' [Quản trị viên]' : ''}
                        </option>
                      ))}
                  </select>
                  <Button
                    type="button"
                    disabled={!transferMemberId}
                    onClick={() => setShowTransferConfirmModal(true)}
                    className="shrink-0 bg-amber-600 hover:bg-amber-700 text-white font-semibold border-none"
                  >
                    <Crown className="w-4 h-4 mr-1.5" />
                    Chuyển quyền
                  </Button>
                </div>
                {group.members?.filter((m) => m.user_id !== group.owner_id).length === 0 && (
                  <p className="text-xs text-slate-400 italic">
                    Nhóm chưa có thành viên nào khác để chuyển giao quyền Trưởng nhóm.
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── 5. Modals ── */}
      <CoHostInboxModal
        groupId={group.id}
        groupName={group.name}
        isOpen={showCoHostInbox}
        onClose={() => setShowCoHostInbox(false)}
        onSuccess={() => {
          loadGroupAndStats();
          loadActivities();
        }}
      />

      <MemberManagementModal
        groupId={group.id}
        groupName={group.name}
        isOpen={showMemberManagement}
        onClose={() => setShowMemberManagement(false)}
        onUpdated={() => loadGroupAndStats()}
        isAdmin={isAdmin}
        isOwner={isOwner}
        ownerId={group.owner_id}
        customForm={group.custom_form}
      />

      {/* Dynamic Form Join Modal */}
      {showJoinModal && (
        <div className="modal-overlay">
          <div className="glass modal-content group-join-modal">
            <h2 className="text-lg font-bold text-slate-900">
              Đơn đăng ký gia nhập {group.name}
            </h2>
            <p className="modal-hint text-xs text-slate-500 mt-1 mb-4">
              {group.custom_form?.description || 'Vui lòng hoàn thiện thông tin dưới đây để gửi Ban Quản Trị xem xét.'}
            </p>

            <form onSubmit={(e) => {
              e.preventDefault();
              submitJoinGroup(formResponses);
            }} className="space-y-4">
              {group.custom_form?.fields?.map((field: any) => (
                <div key={field.id} className="modal-field">
                  <label className="modal-field-label text-xs font-semibold text-slate-700">
                    {field.label} {field.is_required && <span className="text-rose-500">*</span>}
                  </label>
                  {field.field_type === 'checkbox' ? (
                    <input
                      type="checkbox"
                      required={field.is_required}
                      onChange={(e) => setFormResponses(prev => ({ ...prev, [field.id]: e.target.checked }))}
                      className="ml-2 rounded text-indigo-600"
                    />
                  ) : (
                    <input
                      type={field.field_type === 'number' ? 'number' : 'text'}
                      className="input-field w-full p-2 rounded-lg border border-slate-200 text-sm mt-1"
                      required={field.is_required}
                      onChange={(e) => setFormResponses(prev => ({ ...prev, [field.id]: field.field_type === 'number' ? Number(e.target.value) : e.target.value }))}
                    />
                  )}
                </div>
              ))}

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100">
                <Button type="button" variant="secondary" onClick={() => setShowJoinModal(false)}>
                  Hủy
                </Button>
                <Button type="submit" loading={actionLoading}>
                  Gửi đơn tham gia
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Suspend / Resume Modal */}
      {showSuspendModal && (
        <div className="modal-overlay" onClick={() => !suspendLoading && setShowSuspendModal(false)}>
          <div className="glass modal-content max-w-md w-full p-6 text-slate-900" onClick={e => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-3">
              {isInactive ? (
                <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
                  <PlayCircle className="w-6 h-6" />
                </div>
              ) : (
                <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center shrink-0">
                  <PauseCircle className="w-6 h-6" />
                </div>
              )}
              <div>
                <h3 className="text-base font-bold">
                  {isInactive ? 'Kích hoạt lại hoạt động nhóm' : 'Tạm dừng hoạt động nhóm'}
                </h3>
                <p className="text-xs text-slate-500">Xác nhận thay đổi trạng thái nhóm</p>
              </div>
            </div>

            <div className="text-sm text-slate-600 my-4 space-y-2">
              {isInactive ? (
                <p>
                  Bạn có chắc muốn kích hoạt lại <strong>{group.name}</strong>? Nhóm sẽ mở lại tính năng nộp đơn tham gia và cho phép tạo các hoạt động ngoại khóa mới.
                </p>
              ) : (
                <>
                  <p>
                    Bạn có chắc muốn tạm dừng hoạt động nhóm <strong>{group.name}</strong>?
                  </p>
                  <div className="p-3 bg-amber-50 rounded-xl border border-amber-200 text-xs text-amber-800 space-y-1">
                    <p>• Thành viên sẽ <strong>không thể tạo hoạt động mới</strong> dưới danh nghĩa nhóm.</p>
                    <p>• Sinh viên khác <strong>không thể gửi đơn xin gia nhập</strong> nhóm.</p>
                    <p>• Bạn có thể kích hoạt lại hoạt động của nhóm bất cứ khi nào.</p>
                  </div>
                </>
              )}
            </div>

            <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100">
              <Button
                variant="secondary"
                disabled={suspendLoading}
                onClick={() => setShowSuspendModal(false)}
              >
                Hủy
              </Button>
              <Button
                variant={isInactive ? 'primary' : 'secondary'}
                onClick={handleToggleSuspend}
                loading={suspendLoading}
                className={!isInactive ? 'bg-amber-600 hover:bg-amber-700 text-white border-none' : ''}
              >
                {isInactive ? 'Xác nhận mở lại' : 'Xác nhận tạm dừng'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Transfer Ownership Confirmation Modal */}
      {showTransferConfirmModal && (
        <div className="modal-overlay" onClick={() => !transferringOwner && setShowTransferConfirmModal(false)}>
          <div className="glass modal-content max-w-md w-full p-6 text-slate-900" onClick={e => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center shrink-0">
                <Crown className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold">Xác nhận chuyển quyền Trưởng nhóm</h3>
                <p className="text-xs text-slate-500">Chuyển giao quyền điều hành cao nhất</p>
              </div>
            </div>

            {(() => {
              const target = group.members?.find(m => m.user_id === transferMemberId);
              return (
                <div className="text-sm text-slate-600 my-4 space-y-3">
                  <p>
                    Bạn đang chuẩn bị chuyển giao toàn quyền Trưởng nhóm <strong>{group.name}</strong> cho thành viên:
                  </p>
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs">
                    <p className="font-bold text-slate-900 text-sm">
                      {target?.full_name || target?.username || 'Thành viên'}
                    </p>
                    <p className="text-slate-500">@{target?.username || 'user'}</p>
                  </div>
                  <div className="p-3 bg-amber-50 rounded-xl border border-amber-200 text-xs text-amber-800 space-y-1">
                    <p>• Người này sẽ nắm quyền quản lý cao nhất của nhóm.</p>
                    <p>• Bạn sẽ chuyển sang vai trò <strong>Quản trị viên (Admin)</strong>.</p>
                    <p>• Thao tác này có hiệu lực ngay lập tức.</p>
                  </div>
                </div>
              );
            })()}

            <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100">
              <Button
                variant="secondary"
                disabled={transferringOwner}
                onClick={() => setShowTransferConfirmModal(false)}
              >
                Hủy
              </Button>
              <Button
                onClick={handleTransferOwnership}
                loading={transferringOwner}
                className="bg-amber-600 hover:bg-amber-700 text-white font-semibold border-none"
              >
                Xác nhận chuyển giao
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Avatar Preview Modal */}
      {avatarModalOpen && avatarPreviewUrl && (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="glass modal-content max-w-sm w-full p-6 text-center">
            <h3 className="text-lg font-bold mb-1 text-slate-900">Xem trước ảnh đại diện nhóm</h3>
            <p className="text-xs text-slate-500 mb-4">Ảnh sẽ được lưu làm biểu trưng cho {group.name}</p>
            <div className="w-32 h-32 mx-auto rounded-3xl overflow-hidden border-2 border-indigo-500 shadow-xl mb-6 bg-slate-900 flex items-center justify-center">
              <img src={avatarPreviewUrl} alt="Xem trước" className="w-full h-full object-cover" />
            </div>
            <div className="flex gap-2 justify-end pt-3 border-t border-slate-100">
              <Button variant="secondary" onClick={closeAvatarModal} disabled={uploadingAvatar}>
                Hủy
              </Button>
              <Button onClick={handleUploadConfirm} loading={uploadingAvatar}>
                Cập nhật ảnh
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
