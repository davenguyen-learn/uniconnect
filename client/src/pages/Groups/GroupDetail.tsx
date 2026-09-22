import { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { 
  Users, 
  Calendar, 
  Award, 
  ShieldCheck, 
  Globe, 
  Lock, 
  Inbox, 
  UserPlus, 
  LogOut, 
  Settings, 
  CalendarPlus, 
  CheckCircle2, 
  Sparkles,
  AlertCircle,
  Loader2
} from 'lucide-react';
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

  const isMember = Boolean(group?.members?.some(m => m.user_id === user?.id));
  const memberRecord = group?.members?.find(m => m.user_id === user?.id);
  const isOwner = group?.owner_id === user?.id;
  const isAdmin = memberRecord?.role === 'admin' || isOwner;

  const canCreateActivity = isOwner || (isMember && group?.allow_member_activities);

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
      toast.error('Không thể tải thông tin câu lạc bộ');
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
  }, [activeTab, id]);

  async function loadActivities() {
    if (!id) return;
    setLoadingContent(true);
    try {
      const data = await groupsApi.getGroupActivities(id, { limit: 50 });
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
      if (!window.confirm('Bạn có chắc chắn muốn rời khỏi câu lạc bộ này?')) return;
      setActionLoading(true);
      try {
        await groupsApi.leaveGroup(id);
        toast.success('Đã rời câu lạc bộ');
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
        toast.success('Đã gửi đơn tham gia câu lạc bộ, vui lòng chờ Ban Chủ Nhiệm duyệt!');
      } else {
        toast.success('Chào mừng bạn đã gia nhập câu lạc bộ!');
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
      toast.success('Đã cập nhật thông tin câu lạc bộ');
      loadGroupAndStats();
    } catch {
      toast.error('Không thể cập nhật thông tin');
    } finally {
      setSavingSettings(false);
    }
  }

  if (loading) {
    return (
      <div className="container club-loading-state">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600 mb-3" />
        <p className="text-slate-500 font-medium">Đang tải thông tin câu lạc bộ...</p>
      </div>
    );
  }

  if (!group) {
    return (
      <div className="container club-empty-page">
        <AlertCircle className="w-12 h-12 text-rose-500 mb-2" />
        <h2>Không tìm thấy câu lạc bộ</h2>
        <Link to="/groups" className="mt-4 text-indigo-600 hover:underline font-medium">
          Trở về danh sách câu lạc bộ
        </Link>
      </div>
    );
  }

  return (
    <div className="container group-detail-page">
      {/* ── 1. Hero Showcase Banner ── */}
      <div className="club-hero-card glass">
        <div className="club-hero-cover">
          <div className="club-hero-cover-gradient" />
          <div className="club-hero-badge-strip">
            <span className="club-pill-badge club-pill-verified">
              <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
              CLB / Đội / Nhóm Đại học
            </span>
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
          </div>
        </div>

        <div className="club-hero-body">
          <div className="club-hero-profile-row">
            {/* Club Emblem */}
            <div className="club-emblem">
              <span>{group.name.charAt(0).toUpperCase()}</span>
            </div>

            {/* Title & Info */}
            <div className="club-hero-details">
              <div className="flex items-center gap-2">
                <h1 className="club-name-heading">{group.name}</h1>
                <span title="Xác thực bởi Đoàn - Hội">
                  <CheckCircle2 className="w-5 h-5 text-blue-500 shrink-0" />
                </span>
              </div>
              <p className="club-short-desc">{group.description || 'Chưa có mô tả ngắn'}</p>
            </div>

            {/* Primary Action Button */}
            <div className="club-hero-actions">
              <Button
                variant={isMember ? 'secondary' : 'primary'}
                onClick={handleJoinLeaveClick}
                loading={actionLoading}
                className="join-leave-btn"
              >
                {isMember ? (
                  <>
                    <LogOut className="w-4 h-4 mr-1.5" />
                    Rời CLB
                  </>
                ) : (
                  <>
                    <UserPlus className="w-4 h-4 mr-1.5" />
                    {group.require_approval ? 'Gửi đơn gia nhập' : 'Tham gia CLB'}
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Leadership Command Bar (Owner / Admin) */}
          {isAdmin && (
            <div className="club-leadership-toolbar">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
                <Sparkles className="w-4 h-4" />
                Ban Chủ Nhiệm CLB
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <button
                  onClick={() => setShowCoHostInbox(true)}
                  className="leadership-tool-btn"
                >
                  <Inbox className="w-4 h-4 text-indigo-500" />
                  Hộp thư Co-Hosting
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
                  <Link to="/activities/new">
                    <button className="leadership-tool-btn leadership-tool-btn--primary">
                      <CalendarPlus className="w-4 h-4" />
                      Tạo hoạt động mới
                    </button>
                  </Link>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── 2. The 3 Golden Server-Derived Stats ── */}
      <div className="club-stats-grid">
        <div className="club-stat-card glass">
          <div className="club-stat-icon-wrapper bg-blue-50 text-blue-600 dark:bg-blue-950/50 dark:text-blue-400">
            <Users className="w-6 h-6" />
          </div>
          <div className="club-stat-meta">
            <span className="club-stat-value">{stats?.memberCount ?? group.member_count}</span>
            <span className="club-stat-label">Thành viên chính thức</span>
          </div>
        </div>

        <div className="club-stat-card glass">
          <div className="club-stat-icon-wrapper bg-indigo-50 text-indigo-600 dark:bg-indigo-950/50 dark:text-indigo-400">
            <Calendar className="w-6 h-6" />
          </div>
          <div className="club-stat-meta">
            <span className="club-stat-value">{stats?.totalActivitiesCount ?? 0}</span>
            <span className="club-stat-label">Hoạt động đã tổ chức</span>
          </div>
        </div>

        <div className="club-stat-card glass club-stat-card--gold">
          <div className="club-stat-icon-wrapper bg-amber-50 text-amber-600 dark:bg-amber-950/50 dark:text-amber-400">
            <Award className="w-6 h-6" />
          </div>
          <div className="club-stat-meta">
            <span className="club-stat-value">{stats?.ctxhContributedFormatted ?? '0.0 ngày CTXH'}</span>
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
          Giới thiệu & Điều lệ
        </button>
        {isOwner && (
          <button
            className={`club-nav-tab ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            <Settings className="w-4 h-4 mr-2" />
            Cài đặt CLB
          </button>
        )}
      </div>

      {/* ── 4. Tab Content ── */}
      <div className="club-tab-content">
        {activeTab === 'activities' && (
          <div className="activities-section space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                  Hoạt động của CLB
                </h3>
                <p className="text-xs text-slate-500">
                  Bao gồm các sự kiện CLB chủ trì và các hoạt động Đồng tổ chức (Co-Hosted)
                </p>
              </div>
              {canCreateActivity && (
                <Link to="/activities/new">
                  <Button size="sm">
                    <CalendarPlus className="w-4 h-4 mr-1.5" />
                    Tạo hoạt động
                  </Button>
                </Link>
              )}
            </div>

            {loadingContent ? (
              <div className="flex flex-col items-center justify-center py-16 text-slate-400">
                <Loader2 className="w-8 h-8 animate-spin mb-2" />
                <p className="text-sm">Đang tải hoạt động...</p>
              </div>
            ) : activities.length > 0 ? (
              <div className="activities-grid">
                {activities.map((activity) => (
                  <ActivityCard
                    key={activity.id}
                    activity={activity}
                    onClick={() => window.location.href = `/activities/${activity.id}`}
                  />
                ))}
              </div>
            ) : (
              <div className="glass empty-activities-box">
                <Calendar className="w-12 h-12 text-slate-300 dark:text-slate-600 mb-3" />
                <h4 className="text-base font-semibold text-slate-700 dark:text-slate-300">
                  Chưa có hoạt động nào được tổ chức
                </h4>
                <p className="text-xs text-slate-400 max-w-sm mt-1 mb-4">
                  Khi câu lạc bộ chủ trì hoặc tham gia Đồng tổ chức hoạt động ngoại khóa, thông tin sẽ xuất hiện tại đây.
                </p>
                {canCreateActivity && (
                  <Link to="/activities/new">
                    <Button size="sm">Tạo hoạt động đầu tiên</Button>
                  </Link>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'about' && (
          <div className="about-section glass p-6 rounded-2xl space-y-6">
            {group.public_description && (
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white mb-2 flex items-center gap-2">
                  <Globe className="w-4 h-4 text-indigo-500" />
                  Về chúng tôi
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">
                  {group.public_description}
                </p>
              </div>
            )}

            {isMember ? (
              group.private_description && (
                <div className="p-4 rounded-xl bg-indigo-50/50 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900/50">
                  <h3 className="text-sm font-bold text-indigo-900 dark:text-indigo-300 mb-1 flex items-center gap-2">
                    <Lock className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                    Thông tin & Kênh liên lạc nội bộ
                  </h3>
                  <p className="text-xs text-indigo-800/80 dark:text-indigo-200/80 leading-relaxed whitespace-pre-wrap">
                    {group.private_description}
                  </p>
                </div>
              )
            ) : (
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 text-xs text-slate-500 flex items-center gap-2">
                <Lock className="w-4 h-4 text-slate-400" />
                <span>Nội quy và các liên kết trao đổi nội bộ chỉ hiển thị cho thành viên chính thức.</span>
              </div>
            )}
          </div>
        )}

        {activeTab === 'settings' && isOwner && (
          <div className="settings-section glass p-6 rounded-2xl">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
              Cài đặt câu lạc bộ
            </h2>
            <form onSubmit={handleSaveSettings} className="settings-form max-w-xl space-y-4">
              <Input
                label="Tên câu lạc bộ"
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
                  className="form-select w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm"
                  value={settingsForm.privacy}
                  onChange={e => setSettingsForm({ ...settingsForm, privacy: e.target.value as any })}
                >
                  <option value="public">Công khai (Ai cũng có thể tìm thấy)</option>
                  <option value="private">Riêng tư (Chỉ thành viên thấy nội dung)</option>
                </select>
              </div>

              <div className="space-y-2 pt-2">
                <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                  <input
                    type="checkbox"
                    className="rounded text-indigo-600 focus:ring-indigo-500"
                    checked={settingsForm.requireApproval}
                    onChange={(e) => setSettingsForm({ ...settingsForm, requireApproval: e.target.checked })}
                  />
                  <span>Yêu cầu Ban Chủ Nhiệm duyệt đơn để gia nhập</span>
                </label>
                <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                  <input
                    type="checkbox"
                    className="rounded text-indigo-600 focus:ring-indigo-500"
                    checked={settingsForm.allowActivities}
                    onChange={(e) => setSettingsForm({ ...settingsForm, allowActivities: e.target.checked })}
                  />
                  <span>Cho phép thành viên tạo hoạt động ngoại khóa</span>
                </label>
              </div>

              <div className="pt-4">
                <Button type="submit" loading={savingSettings}>
                  Lưu thay đổi
                </Button>
              </div>
            </form>
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
      />

      {/* Dynamic Form Join Modal */}
      {showJoinModal && (
        <div className="modal-overlay">
          <div className="glass modal-content">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">
              Đơn đăng ký gia nhập {group.name}
            </h2>
            <p className="modal-hint text-xs text-slate-500 mt-1 mb-4">
              {group.custom_form?.description || 'Vui lòng hoàn thiện thông tin dưới đây để gửi Ban Chủ Nhiệm xem xét.'}
            </p>

            <form onSubmit={(e) => {
              e.preventDefault();
              submitJoinGroup(formResponses);
            }} className="space-y-4">
              {group.custom_form?.fields?.map((field: any) => (
                <div key={field.id} className="modal-field">
                  <label className="modal-field-label text-xs font-semibold text-slate-700 dark:text-slate-300">
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
                      className="input-field w-full p-2 rounded-lg border border-slate-200 dark:border-slate-700 text-sm mt-1"
                      required={field.is_required}
                      onChange={(e) => setFormResponses(prev => ({ ...prev, [field.id]: field.field_type === 'number' ? Number(e.target.value) : e.target.value }))}
                    />
                  )}
                </div>
              ))}

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100 dark:border-slate-800">
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
    </div>
  );
}
