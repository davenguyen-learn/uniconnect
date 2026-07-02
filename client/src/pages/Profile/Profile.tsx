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
      toast.error('Failed to load profile');
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
      toast.success('Profile updated');
    } catch (err) {
      if (err instanceof ApiRequestError) {
        toast.error('Update failed', err.message);
      } else {
        toast.error('Something went wrong');
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
        toast.success('Unfollowed');
      } else {
        await usersApi.followUser(id);
        setFollowStatus(prev => prev ? { 
          ...prev, 
          is_following: true, 
          followers_count: prev.followers_count + 1 
        } : null);
        toast.success('Followed');
      }
    } catch {
      toast.error('Failed to update follow status');
    } finally {
      setFollowLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="container profile-container">
        <div className="profile-card glass">
          <div className="skeleton" style={{ width: '80px', height: '80px', borderRadius: '50%' }} />
          <div className="skeleton" style={{ width: '200px', height: '24px', marginTop: '16px' }} />
          <div className="skeleton" style={{ width: '150px', height: '16px', marginTop: '8px' }} />
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
                <span className="profile-detail-label">University</span>
                <span>{profile.university}</span>
              </div>
            )}

            {profile.bio && (
              <div className="profile-detail">
                <span className="profile-detail-label">Bio</span>
                <span>{profile.bio}</span>
              </div>
            )}

            {!isOwnProfile && followStatus && (
              <div className="profile-detail" style={{ display: 'flex', gap: '16px' }}>
                <div>
                  <strong>{followStatus.followers_count}</strong> Followers
                </div>
                <div>
                  <strong>{followStatus.following_count}</strong> Following
                </div>
              </div>
            )}

            <div className="profile-detail">
              <span className="profile-detail-label">Member since</span>
              <span>{new Date(profile.created_at).toLocaleDateString('en-US', {
                month: 'long', year: 'numeric'
              })}</span>
            </div>

            {isOwnProfile ? (
              <Button variant="secondary" onClick={() => setEditing(true)} style={{ marginTop: 'var(--space-6)' }}>
                Edit Profile
              </Button>
            ) : (
              <Button 
                variant={followStatus?.is_following ? "secondary" : "primary"} 
                onClick={handleFollowToggle} 
                loading={followLoading}
                style={{ marginTop: 'var(--space-6)' }}
              >
                {followStatus?.is_following ? 'Unfollow' : 'Follow'}
              </Button>
            )}
          </div>
        ) : (
          <form className="profile-form animate-fade-in" onSubmit={handleSave}>
            <Input
              label="Full Name"
              value={form.full_name || ''}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              placeholder="Your full name"
            />
            <Input
              label="University"
              value={form.university || ''}
              onChange={(e) => setForm({ ...form, university: e.target.value })}
              placeholder="Your university"
            />
            <Textarea
              label="Bio"
              value={form.bio || ''}
              onChange={(e) => setForm({ ...form, bio: e.target.value })}
              placeholder="Tell us about yourself"
            />
            <div className="profile-form-actions">
              <Button variant="ghost" type="button" onClick={() => setEditing(false)}>
                Cancel
              </Button>
              <Button type="submit" loading={saving}>
                Save Changes
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
