import { useState, useEffect, type FormEvent } from 'react';
import { useParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { usersApi, type UserProfile as UserProfileType, type UserUpdate, type FollowStatus } from '../../api/users';
import { useToast } from '../../components/Toast/ToastContext';
import { ApiRequestError } from '../../api/client';
import Button from '../../components/Button/Button';
import Input from '../../components/Input/Input';
import { Textarea } from '../../components/Input/Input';
import './Profile.css';

export default function Profile() {
  const { id } = useParams<{ id: string }>();
  const { user, refreshUser } = useAuth();
  const toast = useToast();

  const isOwnProfile = !id || id === user?.id;

  const [profile, setProfile] = useState<UserProfileType | null>(null);
  const [followStatus, setFollowStatus] = useState<FollowStatus | null>(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<UserUpdate>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [followLoading, setFollowLoading] = useState(false);

  useEffect(() => {
    loadProfile();
  }, [id]);

  async function loadProfile() {
    setLoading(true);
    try {
      if (isOwnProfile) {
        const data = await usersApi.getMe();
        setProfile(data);
        setForm({
          full_name: data.full_name || '',
          bio: data.bio || '',
          university: data.university || '',
        });
      } else {
        const data = await usersApi.getUser(id!);
        setProfile(data);
        const status = await usersApi.getFollowStatus(id!);
        setFollowStatus(status);
      }
    } catch {
      toast.error('Không thể tải hồ sơ');
    } finally {
      setLoading(false);
    }
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const updated = await usersApi.updateMe(form);
      setProfile(updated);
      setEditing(false);
      await refreshUser();
      toast.success('Đã cập nhật hồ sơ');
    } catch (err) {
      if (err instanceof ApiRequestError) {
        toast.error('Cập nhật thất bại', err.message);
      } else {
        toast.error('Đã xảy ra lỗi');
      }
    } finally {
      setSaving(false);
    }
  }

  async function handleFollowToggle() {
    if (!id || followLoading) return;
    setFollowLoading(true);
    try {
      if (followStatus?.is_following) {
        await usersApi.unfollowUser(id);
        setFollowStatus(prev => prev ? { 
          ...prev, 
          is_following: false, 
          followers_count: Math.max(0, prev.followers_count - 1) 
        } : null);
        toast.success('Đã bỏ theo dõi');
      } else {
        await usersApi.followUser(id);
        setFollowStatus(prev => prev ? { 
          ...prev, 
          is_following: true, 
          followers_count: prev.followers_count + 1 
        } : null);
        toast.success('Đã theo dõi');
      }
    } catch {
      toast.error('Không thể cập nhật trạng thái theo dõi');
    } finally {
      setFollowLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="container profile-container">
        <div className="profile-card glass">
          <div className="skeleton profile-skeleton-avatar" />
          <div className="skeleton profile-skeleton-name" />
          <div className="skeleton profile-skeleton-email" />
        </div>
      </div>
    );
  }

  if (!profile) return null;

  return (
    <div className="container profile-container">
      <div className="profile-card glass">
        <div className="profile-avatar">
          {profile.full_name
            ? profile.full_name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
            : profile.username.slice(0, 2).toUpperCase()}
        </div>

        {!editing ? (
          <div className="profile-info animate-fade-in">
            <h1 className="profile-name">{profile.full_name || profile.username}</h1>
            <p className="profile-username">@{profile.username}</p>
            {isOwnProfile && <p className="profile-email">{profile.email}</p>}

            {profile.university && (
              <div className="profile-detail">
                <span className="profile-detail-label">Trường đại học</span>
                <span>{profile.university}</span>
              </div>
            )}

            {profile.bio && (
              <div className="profile-detail" style={{ marginTop: 'var(--space-2)' }}>
                <span className="text-pre-wrap">{profile.bio}</span>
              </div>
            )}

            {!isOwnProfile && followStatus && (
              <div className="profile-detail profile-follow-stats">
                <div>
                  <strong>{followStatus.followers_count}</strong> Người theo dõi
                </div>
                <div>
                  <strong>{followStatus.following_count}</strong> Đang theo dõi
                </div>
              </div>
            )}

            <div className="profile-detail">
              <span className="profile-detail-label">Thành viên từ</span>
              <span>{new Date(profile.created_at).toLocaleDateString('vi-VN', {
                month: 'long', year: 'numeric'
              })}</span>
            </div>

            {isOwnProfile ? (
              <Button variant="secondary" onClick={() => setEditing(true)} className="profile-action-btn">
                Chỉnh sửa hồ sơ
              </Button>
            ) : (
              <Button 
                variant={followStatus?.is_following ? "secondary" : "primary"} 
                onClick={handleFollowToggle} 
                loading={followLoading}
                className="profile-action-btn"
              >
                {followStatus?.is_following ? 'Bỏ theo dõi' : 'Theo dõi'}
              </Button>
            )}
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
      </div>
    </div>
  );
}
