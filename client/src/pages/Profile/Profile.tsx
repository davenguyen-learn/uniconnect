import { useState, useEffect, useCallback, type FormEvent } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Award,
  GraduationCap,
  Trophy,
  FileText,
  Sparkles,
  Calendar,
  Users,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import {
  usersApi,
  type UserProfile as UserProfileType,
  type UserUpdate,
  type FollowStatus,
  type MyUserStats,
  type PublicUserStats,
} from '../../api/users';
import { trophiesApi, type UserTrophyResponse } from '../../api/trophies';
import { activitiesApi, type ActivityResponse } from '../../api/activities';
import { useToast } from '../../components/Toast/ToastContext';
import { ApiRequestError } from '../../api/client';
import Button from '../../components/Button/Button';
import Input from '../../components/Input/Input';
import { Textarea } from '../../components/Input/Input';
import { CertificateModal } from '../../components/CertificateModal/CertificateModal';
import {
  mapRankToBadge,
  getInitials,
  formatMemberSince,
  formatActivityDate,
  type ProfileSectionState,
} from '../../types/profile-mapper';
import './Profile.css';

export default function Profile() {
  const { id } = useParams<{ id: string }>();
  const { user, refreshUser } = useAuth();
  const toast = useToast();

  const isOwnProfile = !id || id === user?.id;
  const targetUserId = isOwnProfile ? user?.id : id;

  // Independent section states for fault isolation (Promise.allSettled)
  const [profileState, setProfileState] = useState<ProfileSectionState<UserProfileType>>({
    status: 'loading',
    data: null,
    error: null,
  });

  const [statsState, setStatsState] = useState<ProfileSectionState<MyUserStats | PublicUserStats>>({
    status: 'loading',
    data: null,
    error: null,
  });

  const [trophiesState, setTrophiesState] = useState<ProfileSectionState<UserTrophyResponse[]>>({
    status: 'loading',
    data: null,
    error: null,
  });

  const [activitiesState, setActivitiesState] = useState<ProfileSectionState<ActivityResponse[]>>({
    status: 'loading',
    data: null,
    error: null,
  });

  // Follow & Edit state
  const [followStatus, setFollowStatus] = useState<FollowStatus | null>(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<UserUpdate>({});
  const [saving, setSaving] = useState(false);
  const [followLoading, setFollowLoading] = useState(false);

  // Certificate Modal state
  const [selectedCertificateActivityId, setSelectedCertificateActivityId] = useState<string | null>(null);

  const loadProfileData = useCallback(async () => {
    if (!targetUserId) return;

    // Reset section statuses to loading
    setProfileState(prev => ({ ...prev, status: 'loading', error: null }));
    setStatsState(prev => ({ ...prev, status: 'loading', error: null }));
    setTrophiesState(prev => ({ ...prev, status: 'loading', error: null }));
    if (isOwnProfile) {
      setActivitiesState(prev => ({ ...prev, status: 'loading', error: null }));
    }

    // Parallel queries with Promise.allSettled to guarantee resilience
    const queries = [
      isOwnProfile ? usersApi.getMe() : usersApi.getUser(targetUserId),
      isOwnProfile ? usersApi.getMyStats() : usersApi.getUserStats(targetUserId),
      trophiesApi.getUserTrophies(targetUserId),
      isOwnProfile ? activitiesApi.getJoinedActivities({ limit: 10, offset: 0 }) : Promise.resolve(null),
      !isOwnProfile ? usersApi.getFollowStatus(targetUserId) : Promise.resolve(null),
    ];

    const results = await Promise.allSettled(queries);

    // 1. Profile Info
    if (results[0].status === 'fulfilled' && results[0].value) {
      const data = results[0].value as UserProfileType;
      setProfileState({ status: 'success', data, error: null });
      setForm({
        full_name: data.full_name || '',
        bio: data.bio || '',
        university: data.university || '',
      });
    } else {
      setProfileState({
        status: 'error',
        data: null,
        error: 'Không thể tải thông tin cá nhân',
      });
    }

    // 2. Server-Derived Stats
    if (results[1].status === 'fulfilled' && results[1].value) {
      setStatsState({
        status: 'success',
        data: results[1].value as MyUserStats | PublicUserStats,
        error: null,
      });
    } else {
      setStatsState({
        status: 'error',
        data: null,
        error: 'Không thể tải bảng số liệu thành tích',
      });
    }

    // 3. Trophies
    if (results[2].status === 'fulfilled' && results[2].value) {
      setTrophiesState({
        status: 'success',
        data: results[2].value as UserTrophyResponse[],
        error: null,
      });
    } else {
      setTrophiesState({
        status: 'error',
        data: null,
        error: 'Không thể tải danh sách cúp thành tích',
      });
    }

    // 4. Joined Activities (For Certificates - Paginated 10)
    if (isOwnProfile && results[3].status === 'fulfilled' && results[3].value) {
      const actData = results[3].value as { items: ActivityResponse[] };
      setActivitiesState({
        status: 'success',
        data: actData.items || [],
        error: null,
      });
    }

    // 5. Follow Status
    if (!isOwnProfile && results[4].status === 'fulfilled' && results[4].value) {
      setFollowStatus(results[4].value as FollowStatus);
    }
  }, [targetUserId, isOwnProfile]);

  useEffect(() => {
    loadProfileData();
  }, [loadProfileData]);

  async function handleSave(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const updated = await usersApi.updateMe(form);
      setProfileState(prev => ({ ...prev, data: updated }));
      setEditing(false);
      await refreshUser();
      toast.success('Đã cập nhật hồ sơ');
    } catch (err) {
      if (err instanceof ApiRequestError) {
        toast.error('Cập nhật thất bại', err.message);
      } else {
        toast.error('Đã xảy ra lỗi khi lưu thông tin');
      }
    } finally {
      setSaving(false);
    }
  }

  async function handleFollowToggle() {
    if (!targetUserId || followLoading) return;
    setFollowLoading(true);
    try {
      if (followStatus?.is_following) {
        await usersApi.unfollowUser(targetUserId);
        setFollowStatus(prev =>
          prev
            ? {
                ...prev,
                is_following: false,
                followers_count: Math.max(0, prev.followers_count - 1),
              }
            : null
        );
        toast.success('Đã bỏ theo dõi');
      } else {
        await usersApi.followUser(targetUserId);
        setFollowStatus(prev =>
          prev
            ? {
                ...prev,
                is_following: true,
                followers_count: prev.followers_count + 1,
              }
            : null
        );
        toast.success('Đã theo dõi');
      }
    } catch {
      toast.error('Không thể cập nhật trạng thái theo dõi');
    } finally {
      setFollowLoading(false);
    }
  }

  const profile = profileState.data;
  const stats = statsState.data;
  const trophies = trophiesState.data || [];
  const activities = activitiesState.data || [];

  const rankBadge = stats ? mapRankToBadge(stats.rank_title) : null;
  const isMyStats = isOwnProfile && stats && 'target_ctxh_days' in stats;
  const myStats = isMyStats ? (stats as MyUserStats) : null;

  return (
    <div className="container profile-container">
      {/* 1. PROFILE HEADER CARD */}
      <div className="profile-card glass animate-fade-in">
        {profileState.status === 'loading' ? (
          <div className="flex flex-col items-center gap-3 py-6">
            <div className="skeleton w-24 h-24 rounded-full" />
            <div className="skeleton w-48 h-6 rounded-md" />
            <div className="skeleton w-32 h-4 rounded-md" />
          </div>
        ) : profileState.status === 'error' ? (
          <div className="profile-section-error" role="alert">
            <AlertTriangle size={18} />
            <span>{profileState.error}</span>
            <Button size="sm" variant="secondary" onClick={loadProfileData}>
              <RefreshCw size={14} className="mr-1 inline" /> Thử lại
            </Button>
          </div>
        ) : profile ? (
          <>
            <div className="profile-avatar-wrapper">
              <div className="profile-avatar">
                {getInitials(profile.full_name, profile.username)}
              </div>
              {profile.is_verified && (
                <div className="profile-verified-badge" title="Tài khoản đã xác minh">
                  <ShieldCheck size={16} />
                </div>
              )}
            </div>

            {!editing ? (
              <div className="w-full flex flex-col items-center">
                <div className="profile-name-row">
                  <h1 className="profile-name">{profile.full_name || profile.username}</h1>
                </div>
                <p className="profile-username">@{profile.username}</p>

                {/* Server-derived Rank Title Badge */}
                {rankBadge && (
                  <div className={`profile-rank-badge ${rankBadge.badgeClass}`}>
                    <Sparkles size={14} />
                    <span>{rankBadge.title}</span>
                  </div>
                )}

                <div className="profile-meta-chips">
                  {profile.university && (
                    <div className="profile-meta-item">
                      <GraduationCap size={15} />
                      <span>{profile.university}</span>
                    </div>
                  )}
                  <div className="profile-meta-item">
                    <Calendar size={15} />
                    <span>Tham gia từ {formatMemberSince(profile.created_at)}</span>
                  </div>
                </div>

                {profile.bio && <p className="profile-bio">{profile.bio}</p>}

                {!isOwnProfile && followStatus && (
                  <div className="profile-follow-stats">
                    <div>
                      <strong>{followStatus.followers_count}</strong> Người theo dõi
                    </div>
                    <div>
                      <strong>{followStatus.following_count}</strong> Đang theo dõi
                    </div>
                  </div>
                )}

                <div className="profile-action-btn">
                  {isOwnProfile ? (
                    <Button variant="secondary" onClick={() => setEditing(true)}>
                      Chỉnh sửa hồ sơ
                    </Button>
                  ) : (
                    <Button
                      variant={followStatus?.is_following ? 'secondary' : 'primary'}
                      onClick={handleFollowToggle}
                      loading={followLoading}
                    >
                      <Users size={16} className="inline mr-1.5" />
                      {followStatus?.is_following ? 'Bỏ theo dõi' : 'Theo dõi'}
                    </Button>
                  )}
                </div>
              </div>
            ) : (
              <form className="profile-form animate-fade-in" onSubmit={handleSave}>
                <Input
                  label="Họ và tên"
                  value={form.full_name || ''}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                  placeholder="Họ và tên của bạn"
                />
                <Input
                  label="Trường đại học"
                  value={form.university || ''}
                  onChange={(e) => setForm({ ...form, university: e.target.value })}
                  placeholder="Trường đại học của bạn"
                />
                <Textarea
                  label="Tiểu sử"
                  value={form.bio || ''}
                  onChange={(e) => setForm({ ...form, bio: e.target.value })}
                  placeholder="Giới thiệu về bản thân bạn"
                />
                <div className="profile-form-actions">
                  <Button variant="ghost" type="button" onClick={() => setEditing(false)}>
                    Hủy
                  </Button>
                  <Button type="submit" loading={saving}>
                    Lưu thay đổi
                  </Button>
                </div>
              </form>
            )}
          </>
        ) : null}
      </div>

      {/* 2. CTXH PASSPORT & RECOGNITION STATS WIDGET (100% Server-Derived Data) */}
      <div className="profile-ctxh-card glass animate-fade-in">
        <div className="ctxh-passport-header">
          <div className="ctxh-passport-title-group">
            <Award size={24} className="text-emerald-500" />
            <div>
              <h2 className="ctxh-passport-title">Hộ Chiếu Ngày CTXH & Cống Hiến</h2>
              <p className="ctxh-passport-subtitle">Số liệu xác thực chính thức từ hệ thống</p>
            </div>
          </div>
          {stats && (
            <div className="trophies-points-badge">
              <Trophy size={16} />
              <span>{stats.total_trophy_points} Điểm rèn luyện</span>
            </div>
          )}
        </div>

        {statsState.status === 'loading' ? (
          <div className="py-8 flex flex-col gap-3">
            <div className="skeleton w-full h-16 rounded-xl" />
            <div className="skeleton w-full h-3 rounded-full" />
          </div>
        ) : statsState.status === 'error' ? (
          <div className="profile-section-error" role="alert">
            <AlertTriangle size={18} />
            <span>{statsState.error}</span>
          </div>
        ) : stats ? (
          <>
            <div className="ctxh-stat-grid">
              <div className="ctxh-stat-box">
                <span className="ctxh-stat-box-label">Tổng ngày CTXH</span>
                <span className="ctxh-stat-box-value text-emerald-600 dark:text-emerald-400">
                  {stats.total_ctxh_days.toFixed(1)} ngày
                </span>
                <span className="ctxh-stat-box-hint">
                  {myStats
                    ? myStats.is_target_reached
                      ? 'Đã hoàn thành xuất sắc chỉ tiêu tốt nghiệp'
                      : `Còn thiếu ${myStats.remaining_ctxh_days.toFixed(1)} ngày để đủ 15 ngày`
                    : 'Số ngày cống hiến vì cộng đồng'}
                </span>
              </div>

              <div className="ctxh-stat-box">
                <span className="ctxh-stat-box-label">Hoạt động đã có mặt</span>
                <span className="ctxh-stat-box-value text-indigo-600 dark:text-indigo-400">
                  {stats.total_attended_activities} sự kiện
                </span>
                <span className="ctxh-stat-box-hint">Điểm danh định vị đã xác thực</span>
              </div>

              <div className="ctxh-stat-box">
                <span className="ctxh-stat-box-label">Huy hiệu Trophy</span>
                <span className="ctxh-stat-box-value text-amber-600 dark:text-amber-400">
                  {stats.total_trophies_count} danh hiệu
                </span>
                <span className="ctxh-stat-box-hint">Thành tích rèn luyện được cấp</span>
              </div>
            </div>

            {/* Private Progress Bar towards 15 days graduation target (Self view only) */}
            {myStats && (
              <div className="mt-2">
                <div
                  className="ctxh-progress-track"
                  role="progressbar"
                  aria-valuenow={myStats.ctxh_completion_percent}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label="Tiến độ hoàn thành chỉ tiêu 15 ngày CTXH"
                >
                  <div
                    className={`ctxh-progress-fill ${myStats.is_target_reached ? 'ctxh-progress-fill--complete' : ''}`}
                    style={{ width: `${myStats.ctxh_completion_percent}%` }}
                  />
                </div>
                <div className="ctxh-progress-footer">
                  <span>
                    Chỉ tiêu: <strong>15.0 ngày</strong>
                  </span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                    {myStats.ctxh_completion_percent}% hoàn thành
                  </span>
                </div>
              </div>
            )}
          </>
        ) : null}
      </div>

      {/* 3. TROPHY SHOWCASE CARD */}
      <div className="profile-trophies-card glass animate-fade-in">
        <div className="trophies-header">
          <div className="flex items-center gap-3">
            <Trophy size={26} className="text-amber-500" />
            <div>
              <h2 className="trophies-title">Bộ sưu tập Trophy</h2>
              <p className="trophies-subtitle">Danh hiệu đạt được khi tham gia các hoạt động</p>
            </div>
          </div>
        </div>

        {trophiesState.status === 'loading' ? (
          <div className="py-8 flex gap-4">
            <div className="skeleton w-1/3 h-28 rounded-xl" />
            <div className="skeleton w-1/3 h-28 rounded-xl" />
            <div className="skeleton w-1/3 h-28 rounded-xl" />
          </div>
        ) : trophiesState.status === 'error' ? (
          <div className="profile-section-error" role="alert">
            <AlertTriangle size={18} />
            <span>{trophiesState.error}</span>
          </div>
        ) : trophies.length === 0 ? (
          <div className="trophies-empty">
            <Trophy size={36} className="mx-auto mb-2 text-gray-400" />
            <p className="text-sm text-[var(--color-text-secondary)]">
              {isOwnProfile
                ? 'Bạn chưa nhận được Trophy nào. Hãy tham gia các hoạt động để nhận Trophy vinh danh!'
                : 'Người dùng này chưa có Trophy nào.'}
            </p>
          </div>
        ) : (
          <div className="trophies-grid">
            {trophies.map((ut) => (
              <div key={ut.id} className="trophy-item-card glass">
                <div className="trophy-icon-wrapper">
                  <span className="trophy-icon-display">{ut.trophy?.icon || '🏆'}</span>
                  <span className="trophy-points-tag">+{ut.trophy?.points || 0} điểm</span>
                </div>
                <div className="trophy-item-info">
                  <h3 className="trophy-item-name">{ut.trophy?.name}</h3>
                  {ut.trophy?.description && (
                    <p className="trophy-item-desc">{ut.trophy.description}</p>
                  )}
                  {ut.activity && (
                    <Link to={`/activities/${ut.activity.id}`} className="trophy-activity-link">
                      <ExternalLink size={12} /> {ut.activity.title}
                    </Link>
                  )}
                  <span className="trophy-item-date">
                    Đạt được: {formatActivityDate(ut.created_at)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 4. CERTIFICATE & PROOF INTEGRATION (Private to own profile) */}
      {isOwnProfile && (
        <div className="profile-certificates-card glass animate-fade-in">
          <div className="ctxh-passport-header">
            <div className="ctxh-passport-title-group">
              <FileText size={24} className="text-indigo-500" />
              <div>
                <h2 className="ctxh-passport-title">Minh Chứng & Giấy Chứng Nhận Điện Tử</h2>
                <p className="ctxh-passport-subtitle">
                  Xuất file PDF chuẩn A4 và mã QR tra cứu chống làm giả
                </p>
              </div>
            </div>
          </div>

          {activitiesState.status === 'loading' ? (
            <div className="py-6 flex flex-col gap-3">
              <div className="skeleton w-full h-14 rounded-xl" />
              <div className="skeleton w-full h-14 rounded-xl" />
            </div>
          ) : activitiesState.status === 'error' ? (
            <div className="profile-section-error" role="alert">
              <AlertTriangle size={18} />
              <span>{activitiesState.error}</span>
            </div>
          ) : activities.length === 0 ? (
            <p className="text-sm text-[var(--color-text-secondary)] py-4 text-center">
              Chưa có hoạt động đã hoàn thành nào.
            </p>
          ) : (
            <div className="certificates-list">
              {activities.map((act) => (
                <div key={act.id} className="certificate-row-item">
                  <div className="certificate-row-info">
                    <span className="certificate-row-title">{act.title}</span>
                    <div className="certificate-row-meta">
                      <span>{formatActivityDate(act.start_time)}</span>
                      {act.social_work_days && act.social_work_days > 0 && (
                        <span className="text-emerald-600 dark:text-emerald-400 font-semibold">
                          +{act.social_work_days} ngày CTXH
                        </span>
                      )}
                    </div>
                  </div>

                  <Button
                    size="sm"
                    variant="primary"
                    onClick={() => setSelectedCertificateActivityId(act.id)}
                  >
                    <FileText size={14} className="inline mr-1" />
                    Xuất Bằng Khen / PDF
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Certificate Modal */}
      {selectedCertificateActivityId && (
        <CertificateModal
          isOpen={!!selectedCertificateActivityId}
          onClose={() => setSelectedCertificateActivityId(null)}
          activityId={selectedCertificateActivityId}
          userId={targetUserId}
        />
      )}
    </div>
  );
}
