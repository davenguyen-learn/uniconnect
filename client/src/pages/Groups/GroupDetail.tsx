import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { groupsApi, type GroupDetailResponse } from '../../api/groups';
import type { ActivityResponse } from '../../api/activities';
import type { DocumentResponse } from '../../api/documents';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../components/Toast/ToastContext';
import Button from '../../components/Button/Button';
import Input, { Textarea } from '../../components/Input/Input';
import ActivityCard from '../../components/ActivityCard/ActivityCard';
import './GroupDetail.css';

export default function GroupDetail() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const toast = useToast();

  const [group, setGroup] = useState<GroupDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'about' | 'activities' | 'documents' | 'settings'>('about');

  const [activities, setActivities] = useState<ActivityResponse[]>([]);
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [loadingContent, setLoadingContent] = useState(false);

  const [actionLoading, setActionLoading] = useState(false);

  // Form modal state when joining
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [formResponses, setFormResponses] = useState<Record<string, any>>({});

  // Settings form state
  const [settingsForm, setSettingsForm] = useState({
    name: '',
    description: '',
    publicDescription: '',
    privateDescription: '',
    privacy: 'public' as 'public' | 'private',
    requireApproval: true,
    allowActivities: true,
    allowDocuments: true,
  });
  const [savingSettings, setSavingSettings] = useState(false);

  useEffect(() => {
    loadGroup();
  }, [id]);

  useEffect(() => {
    if (activeTab === 'activities') {
      loadActivities();
    } else if (activeTab === 'documents') {
      loadDocuments();
    }
  }, [activeTab, id]);

  const isMember = group?.members.some(m => m.user_id === user?.id);
  const isOwner = group?.owner_id === user?.id;

  const canCreateActivity = isOwner || (isMember && group?.allow_member_activities);
  const canUploadDocument = isOwner || (isMember && group?.allow_member_documents);

  async function loadGroup() {
    if (!id) return;
    setLoading(true);
    try {
      const data = await groupsApi.getGroup(id);
      setGroup(data);
      setSettingsForm({
        name: data.name,
        description: data.description || '',
        publicDescription: data.public_description || '',
        privateDescription: data.private_description || '',
        privacy: (data.privacy as any) || 'public',
        requireApproval: data.require_approval ?? true,
        allowActivities: data.allow_member_activities ?? true,
        allowDocuments: data.allow_member_documents ?? true,
      });
    } catch {
      toast.error('Không thể tải chi tiết nhóm');
    } finally {
      setLoading(false);
    }
  }

  async function loadActivities() {
    if (!id || !isMember) return;
    setLoadingContent(true);
    try {
      const data = await groupsApi.getGroupActivities(id);
      setActivities(data.items);
    } catch {
      toast.error('Không thể tải hoạt động nhóm');
    } finally {
      setLoadingContent(false);
    }
  }

  async function loadDocuments() {
    if (!id || !isMember) return;
    setLoadingContent(true);
    try {
      const data = await groupsApi.getGroupDocuments(id);
      setDocuments(data.items);
    } catch {
      toast.error('Không thể tải tài liệu nhóm');
    } finally {
      setLoadingContent(false);
    }
  }

  async function handleJoinLeaveClick() {
    if (!id || actionLoading) return;

    if (isMember) {
      // Leave group immediately
      setActionLoading(true);
      try {
        await groupsApi.leaveGroup(id);
        toast.success('Đã rời nhóm');
        loadGroup();
      } catch {
        toast.error('Không thể rời nhóm');
      } finally {
        setActionLoading(false);
      }
    } else {
      // If group has custom form or requires approval, show join modal
      if (group?.custom_form && group.custom_form.fields?.length > 0) {
        setShowJoinModal(true);
      } else {
        // Direct join
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
        toast.success('Đã gửi yêu cầu tham gia để chờ phê duyệt!');
      } else {
        toast.success('Đã tham gia nhóm thành công!');
      }
      setShowJoinModal(false);
      loadGroup();
    } catch {
      toast.error('Không thể tham gia nhóm');
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
        allow_member_documents: settingsForm.allowDocuments,
      });
      toast.success('Đã cập nhật cài đặt thành công');
      loadGroup();
    } catch {
      toast.error('Không thể cập nhật cài đặt nhóm');
    } finally {
      setSavingSettings(false);
    }
  }

  if (loading) {
    return <div className="container group-loading">Đang tải nhóm...</div>;
  }

  if (!group) return null;

  return (
    <div className="container group-detail-page">
      <div className="group-detail-header glass">
        <div className="group-header-row">
          <div>
            <div className="group-title-row">
              <h1 className="brutalist-highlight">{group.name}</h1>
              <span className={`privacy-badge ${group.privacy === 'private' ? 'privacy-badge--private' : 'privacy-badge--public'}`}>
                {group.privacy === 'private' ? '🔒 Riêng tư' : '🌐 Công khai'}
              </span>
            </div>
            <p className="group-detail-desc">{group.description}</p>
            <div className="group-meta">
              <span>{group.member_count} Thành viên</span>
              <span>•</span>
              <span>Đã tạo {new Date(group.created_at).toLocaleDateString('vi-VN')}</span>
            </div>
          </div>
          <Button
            variant={isMember ? 'secondary' : 'primary'}
            onClick={handleJoinLeaveClick}
            loading={actionLoading}
          >
            {isMember ? 'Rời nhóm' : (group.require_approval ? 'Yêu cầu tham gia' : 'Tham gia nhóm')}
          </Button>
        </div>
      </div>

      {/* Join Group Modal with Custom Form */}
      {showJoinModal && (
        <div className="modal-overlay">
          <div className="glass modal-content">
            <h2>Đơn đăng ký tham gia nhóm</h2>
            <p className="modal-hint">
              {group.custom_form?.description || 'Vui lòng trả lời các câu hỏi sau để yêu cầu tham gia nhóm này.'}
            </p>

            <form onSubmit={(e) => {
              e.preventDefault();
              submitJoinGroup(formResponses);
            }}>
              {group.custom_form?.fields?.map((field: any) => (
                <div key={field.id} className="modal-field">
                  <label className="modal-field-label">
                    {field.label} {field.is_required && <span className="required-mark">*</span>}
                  </label>
                  {field.field_type === 'checkbox' ? (
                    <input
                      type="checkbox"
                      required={field.is_required}
                      onChange={(e) => setFormResponses(prev => ({ ...prev, [field.id]: e.target.checked }))}
                    />
                  ) : (
                    <input
                      type={field.field_type === 'number' ? 'number' : 'text'}
                      className="input-field"
                      required={field.is_required}
                      onChange={(e) => setFormResponses(prev => ({ ...prev, [field.id]: field.field_type === 'number' ? Number(e.target.value) : e.target.value }))}
                    />
                  )}
                </div>
              ))}

              <div className="modal-actions">
                <Button type="button" variant="secondary" onClick={() => setShowJoinModal(false)}>
                  Hủy
                </Button>
                <Button type="submit" loading={actionLoading}>
                  Gửi yêu cầu
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="group-tabs">
        <button
          className={`group-tab ${activeTab === 'about' ? 'active' : ''}`}
          onClick={() => setActiveTab('about')}
        >
          Giới thiệu & Thành viên
        </button>
        <button
          className={`group-tab ${activeTab === 'activities' ? 'active' : ''}`}
          onClick={() => setActiveTab('activities')}
        >
          Hoạt động
        </button>
        <button
          className={`group-tab ${activeTab === 'documents' ? 'active' : ''}`}
          onClick={() => setActiveTab('documents')}
        >
          Tài liệu
        </button>
        {isOwner && (
          <button
            className={`group-tab ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            Cài đặt
          </button>
        )}
      </div>

      <div className="group-content">
        {activeTab === 'about' && (
          <div className="group-members-section glass">
            {group.public_description && (
              <div className="about-section">
                <h3>Về chúng tôi</h3>
                <p className="text-pre-wrap">{group.public_description}</p>
              </div>
            )}

            {group.private_description ? (
              <div className="callout">
                <h3 className="member-info-heading">🔓 Thông tin dành cho thành viên</h3>
                <p className="text-pre-wrap">{group.private_description}</p>
              </div>
            ) : group.privacy === 'private' && !isMember && (
              <div className="callout callout--muted">
                🔒 Thông tin riêng tư của thành viên (Tham gia nhóm để xem các liên kết và mô tả riêng tư)
              </div>
            )}

            <h3>Thành viên ({group.members.length})</h3>
            <div className="members-list">
              {group.members.map(member => (
                <div key={member.user_id} className="member-item">
                  <div className="member-avatar">
                    {(member.full_name || member.username || '?').charAt(0).toUpperCase()}
                  </div>
                  <div className="member-info">
                    <Link to={`/profile/${member.user_id}`} className="member-name">
                      {member.full_name || member.username}
                    </Link>
                    <span className="member-role">{member.role}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'activities' && (
          <div className="group-activities-section">
            <div className="section-actions">
              {canCreateActivity && (
                <Link to="/activities/new">
                  <Button size="sm">Tạo hoạt động</Button>
                </Link>
              )}
            </div>
            {!isMember ? (
              <div className="glass empty-state">
                <p>Bạn phải là thành viên để xem các hoạt động của nhóm.</p>
              </div>
            ) : loadingContent ? (
              <p>Đang tải hoạt động...</p>
            ) : activities.length > 0 ? (
              <div className="activities-grid">
                {activities.map(activity => (
                  <ActivityCard
                    key={activity.id}
                    activity={activity}
                    onClick={() => window.location.href = `/activities/${activity.id}`}
                  />
                ))}
              </div>
            ) : (
              <div className="glass empty-state">
                <p>Chưa có hoạt động nào trong nhóm này.</p>
                {canCreateActivity && (
                  <Link to="/activities/new">
                    <Button className="empty-state-cta">Tạo hoạt động</Button>
                  </Link>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'documents' && (
          <div className="group-documents-section">
            <div className="section-actions">
              {canUploadDocument && (
                <Link to={`/documents/upload?groupId=${id}`}>
                  <Button size="sm">Tải lên</Button>
                </Link>
              )}
            </div>
            {!isMember ? (
              <div className="glass empty-state">
                <p>Bạn phải là thành viên để xem tài liệu của nhóm.</p>
              </div>
            ) : loadingContent ? (
              <p>Đang tải tài liệu...</p>
            ) : documents.length > 0 ? (
              <div className="documents-grid">
                {documents.map(doc => (
                  <div key={doc.id} className="glass document-item">
                    <h4>{doc.title}</h4>
                    <p>{doc.file_name}</p>
                    <Link to={`/documents/${doc.id}`}>
                      <Button size="sm" variant="secondary">Xem</Button>
                    </Link>
                  </div>
                ))}
              </div>
            ) : (
              <div className="glass empty-state">
                <p>Chưa có tài liệu nào trong nhóm này.</p>
                {canUploadDocument && (
                  <Link to={`/documents/upload?groupId=${id}`}>
                    <Button className="empty-state-cta">Tải tài liệu lên</Button>
                  </Link>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'settings' && isOwner && (
          <div className="group-settings-section glass">
            <h2>Cài đặt nhóm</h2>
            <form onSubmit={handleSaveSettings} className="settings-form">
              <Input
                label="Tên nhóm"
                value={settingsForm.name}
                onChange={e => setSettingsForm({ ...settingsForm, name: e.target.value })}
                required
              />
              <Textarea
                label="Mô tả ngắn"
                value={settingsForm.description}
                onChange={e => setSettingsForm({ ...settingsForm, description: e.target.value })}
              />

              <Textarea
                label="Tổng quan công khai"
                value={settingsForm.publicDescription}
                onChange={e => setSettingsForm({ ...settingsForm, publicDescription: e.target.value })}
              />

              <Textarea
                label="Mô tả riêng tư (Chỉ dành cho thành viên) 🔒"
                value={settingsForm.privateDescription}
                onChange={e => setSettingsForm({ ...settingsForm, privateDescription: e.target.value })}
              />

              <div className="form-group">
                <label htmlFor="privacy_select" className="form-label">Loại quyền riêng tư</label>
                <select
                  id="privacy_select"
                  className="form-select"
                  value={settingsForm.privacy}
                  onChange={e => setSettingsForm({ ...settingsForm, privacy: e.target.value as any })}
                >
                  <option value="public">Công khai</option>
                  <option value="private">Riêng tư</option>
                </select>
              </div>

              <div className="settings-checkboxes">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={settingsForm.requireApproval}
                    onChange={(e) => setSettingsForm({ ...settingsForm, requireApproval: e.target.checked })}
                  />
                  <span>Yêu cầu quản trị viên phê duyệt để tham gia</span>
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={settingsForm.allowActivities}
                    onChange={(e) => setSettingsForm({ ...settingsForm, allowActivities: e.target.checked })}
                  />
                  <span>Cho phép thành viên tạo hoạt động</span>
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={settingsForm.allowDocuments}
                    onChange={(e) => setSettingsForm({ ...settingsForm, allowDocuments: e.target.checked })}
                  />
                  <span>Cho phép thành viên tải tài liệu lên</span>
                </label>
              </div>

              <div className="settings-submit">
                <Button type="submit" loading={savingSettings}>Lưu cài đặt</Button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
