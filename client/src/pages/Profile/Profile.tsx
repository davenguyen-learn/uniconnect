import { useState, useEffect, useCallback, useRef, type FormEvent } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Award,
  GraduationCap,
  Trophy,
  FileText,
  Calendar,
  Users,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
  Camera,
  Trash2,
  X,
  Lock,
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
  formatActivityTimeRange,
  type ProfileSectionState,
} from '../../types/profile-mapper';
import { formatCtxh } from '../../utils/format';
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

  // Avatar Modal & Upload state
  const [imageError, setImageError] = useState(false);
  const [avatarModalOpen, setAvatarModalOpen] = useState(false);
  const [selectedAvatarFile, setSelectedAvatarFile] = useState<File | null>(null);
  const [avatarPreviewUrl, setAvatarPreviewUrl] = useState<string | null>(null);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const resolveAvatarUrl = useCallback((url: string | null | undefined): string | null => {
    if (!url) return null;
    if (url.startsWith('http://') || url.startsWith('https://')) return url;
    const serverOrigin = import.meta.env.VITE_API_URL?.replace('/api/v1', '') || 'http://localhost:8000';
    return `${serverOrigin}${url}`;
  }, []);

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
    if (!selectedAvatarFile) return;
    setUploadingAvatar(true);
    try {
      const updated = await usersApi.uploadAvatar(selectedAvatarFile);
      setProfileState(prev => ({ ...prev, data: updated }));
      setImageError(false);
      closeAvatarModal();
      await refreshUser();
      toast.success('Đã cập nhật ảnh đại diện thành công');
    } catch (err) {
      if (err instanceof ApiRequestError) {
        toast.error('Tải ảnh thất bại', err.message);
      } else {
        toast.error('Đã xảy ra lỗi khi tải ảnh lên');
      }
    } finally {
      setUploadingAvatar(false);
    }
  };

  const handleDeleteAvatar = async () => {
    setUploadingAvatar(true);
    try {
      const updated = await usersApi.deleteAvatar();
      setProfileState(prev => ({ ...prev, data: updated }));
      setImageError(false);
      closeAvatarModal();
      await refreshUser();
      toast.success('Đã gỡ ảnh đại diện, chuyển về chữ viết tắt');
    } catch (err) {
      toast.error('Không thể gỡ ảnh đại diện');
    } finally {
      setUploadingAvatar(false);
    }
  };

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
      usersApi.getFollowStatus(targetUserId),
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
    if (results[4].status === 'fulfilled' && results[4].value) {
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
              {profile.avatar_url && !imageError ? (
                <img
                  src={resolveAvatarUrl(profile.avatar_url)!}
                  alt={profile.full_name || profile.username}
                  className="profile-avatar-img"
                  onError={() => setImageError(true)}
                />
              ) : (
                <div className="profile-avatar">
                  {getInitials(profile.full_name, profile.username)}
                </div>
              )}
              {profile.is_verified && (
                <div className="profile-verified-badge" title="Tài khoản đã xác minh">
                  <ShieldCheck size={16} />
                </div>
              )}
              {isOwnProfile && (
                <>
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleAvatarFileChange}
                    accept="image/jpeg,image/png,image/webp"
                    style={{ display: 'none' }}
                    aria-label="Chọn ảnh đại diện mới"
                  />
                  <button
                    type="button"
                    className="profile-avatar-camera-btn"
                    onClick={() => fileInputRef.current?.click()}
                    title="Đổi ảnh đại diện"
                    aria-label="Đổi ảnh đại diện"
                  >
                    <Camera size={15} />
                  </button>
                </>
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

                {followStatus && (
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

      {/* 2. ACTIVITY STATS WIDGET (100% Server-Derived Data) */}
      <div className="profile-ctxh-card glass animate-fade-in">
        <div className="ctxh-passport-header">
          <div className="ctxh-passport-title-group">
            <Award size={24} className="text-emerald-700" />
            <div>
              <h2 className="ctxh-passport-title">
                {isOwnProfile ? 'Thống kê hoạt động của bạn' : 'Thống kê hoạt động'}
              </h2>
            </div>
          </div>
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
          <div className="ctxh-stat-grid">
            <div className="ctxh-stat-box">
              <span className="ctxh-stat-box-label">Tổng ngày CTXH</span>
              <span className="ctxh-stat-box-value ctxh-stat-box-value--ctxh">
                {formatCtxh(stats.total_ctxh_days)} ngày
              </span>
              <span className="ctxh-stat-box-hint">
                Số ngày tích lũy trên nền tảng UniConnect
              </span>
            </div>

            <div className="ctxh-stat-box">
              <span className="ctxh-stat-box-label">Hoạt động đã có mặt</span>
              <span className="ctxh-stat-box-value text-indigo-700">
                {stats.total_attended_activities} sự kiện
              </span>
              <span className="ctxh-stat-box-hint">Điểm danh định vị đã xác thực</span>
            </div>

            <div className="ctxh-stat-box">
              <span className="ctxh-stat-box-label">Danh hiệu đạt được</span>
              <span className="ctxh-stat-box-value text-amber-700">
                {stats.total_trophies_count} danh hiệu
              </span>
              <span className="ctxh-stat-box-hint">Huy hiệu vinh danh được cấp</span>
            </div>
          </div>
        ) : null}
      </div>

      {/* 3. TROPHY SHOWCASE CARD */}
      <div className="profile-trophies-card glass animate-fade-in">
        <div className="trophies-header">
          <div className="flex items-center gap-3">
            <Trophy size={26} className="text-amber-500" />
            <div>
              <h2 className="trophies-title">Bộ sưu tập Danh hiệu</h2>
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
                ? 'Bạn chưa nhận được danh hiệu nào. Hãy tham gia các hoạt động để nhận danh hiệu vinh danh!'
                : 'Người dùng này chưa có danh hiệu nào.'}
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
                    ut.activity.is_accessible && ut.activity.id ? (
                      <Link to={`/activities/${ut.activity.id}`} className="trophy-activity-link">
                        <ExternalLink size={12} /> {ut.activity.title}
                      </Link>
                    ) : (
                      <span className="trophy-activity-private-tag">
                        <Lock size={12} />
                        <span>Sự kiện riêng tư</span>
                      </span>
                    )
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
                <h2 className="ctxh-passport-title">Minh chứng tham gia hoạt động</h2>
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
                    <Link
                      to={`/activities/${act.id}`}
                      className="certificate-row-title"
                      title="Xem chi tiết hoạt động"
                    >
                      <span>{act.title}</span>
                      <ExternalLink size={14} className="certificate-row-icon" />
                    </Link>
                    {typeof act.social_work_days === 'number' && act.social_work_days > 0 ? (
                      <div className="certificate-row-badge-line">
                        <span className="certificate-badge-ctxh">
                          +{formatCtxh(act.social_work_days)} ngày CTXH
                        </span>
                      </div>
                    ) : null}
                    <div className="certificate-row-meta">
                      <Calendar size={13} className="certificate-meta-icon" />
                      <span>{formatActivityTimeRange(act.start_time, act.end_time)}</span>
                    </div>
                  </div>

                  <div className="certificate-row-actions">
                    <Button
                      size="sm"
                      className={act.attendance_confirmed ? 'btn-cert-confirmed' : 'btn-cert-unconfirmed'}
                      disabled={!act.attendance_confirmed}
                      title={act.attendance_confirmed ? 'Xuất giấy xác nhận đã tham gia' : 'Hoạt động này chưa được xác nhận điểm danh'}
                      onClick={() => {
                        if (act.attendance_confirmed) {
                          setSelectedCertificateActivityId(act.id);
                        }
                      }}
                    >
                      <FileText size={14} className="inline mr-1" />
                      Xuất giấy xác nhận đã tham gia
                    </Button>
                  </div>
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

      {/* Avatar Preview & Confirmation Modal */}
      {avatarModalOpen && (
        <div className="avatar-modal-overlay" onClick={closeAvatarModal} role="dialog" aria-modal="true">
          <div className="avatar-modal-card glass animate-fade-in" onClick={(e) => e.stopPropagation()}>
            <div className="avatar-modal-header">
              <h3 className="avatar-modal-title">Cập nhật ảnh đại diện</h3>
              <button
                type="button"
                className="avatar-modal-close"
                onClick={closeAvatarModal}
                disabled={uploadingAvatar}
                aria-label="Đóng"
              >
                <X size={18} />
              </button>
            </div>

            <div className="avatar-modal-body">
              {avatarPreviewUrl ? (
                <div className="avatar-modal-preview-wrapper">
                  <img src={avatarPreviewUrl} alt="Xem trước avatar" className="avatar-modal-preview-img" />
                  <span className="avatar-modal-file-info">
                    {selectedAvatarFile?.name} ({(selectedAvatarFile ? selectedAvatarFile.size / 1024 : 0).toFixed(1)} KB)
                  </span>
                </div>
              ) : null}
            </div>

            <div className="avatar-modal-actions">
              {profile?.avatar_url && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-rose-600 hover:text-rose-700 mr-auto"
                  onClick={handleDeleteAvatar}
                  disabled={uploadingAvatar}
                >
                  <Trash2 size={14} className="inline mr-1" /> Gỡ ảnh
                </Button>
              )}
              <Button variant="secondary" size="sm" onClick={closeAvatarModal} disabled={uploadingAvatar}>
                Hủy
              </Button>
              <Button variant="primary" size="sm" onClick={handleUploadConfirm} loading={uploadingAvatar}>
                Lưu ảnh đại diện
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
