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

  // Settings form state
  const [settingsForm, setSettingsForm] = useState({
    name: '',
    description: '',
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
        allowActivities: data.allow_member_activities ?? true,
        allowDocuments: data.allow_member_documents ?? true,
      });
    } catch {
      toast.error('Failed to load group details');
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
      toast.error('Failed to load group activities');
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
      toast.error('Failed to load group documents');
    } finally {
      setLoadingContent(false);
    }
  }

  async function handleJoinLeave() {
    if (!id || actionLoading) return;
    setActionLoading(true);
    try {
      if (isMember) {
        await groupsApi.leaveGroup(id);
        toast.success('Left group');
      } else {
        await groupsApi.joinGroup(id);
        toast.success('Joined group');
      }
      loadGroup(); // reload members
    } catch {
      toast.error(isMember ? 'Failed to leave group' : 'Failed to join group');
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
        allow_member_activities: settingsForm.allowActivities,
        allow_member_documents: settingsForm.allowDocuments,
      });
      toast.success('Settings updated successfully');
      loadGroup();
    } catch {
      toast.error('Failed to update group settings');
    } finally {
      setSavingSettings(false);
    }
  }

  if (loading) {
    return <div className="container" style={{paddingTop: '32px'}}>Loading group...</div>;
  }

  if (!group) return null;

  return (
    <div className="container group-detail-page">
      <div className="group-detail-header glass">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1 className="gradient-text">{group.name}</h1>
            <p className="group-detail-desc">{group.description}</p>
            <div className="group-meta">
              <span>{group.member_count} Members</span>
              <span>•</span>
              <span>Created {new Date(group.created_at).toLocaleDateString()}</span>
            </div>
          </div>
          <Button 
            variant={isMember ? 'secondary' : 'primary'} 
            onClick={handleJoinLeave}
            loading={actionLoading}
          >
            {isMember ? 'Leave Group' : 'Join Group'}
          </Button>
        </div>
      </div>

      <div className="group-tabs">
        <button 
          className={`group-tab ${activeTab === 'about' ? 'active' : ''}`}
          onClick={() => setActiveTab('about')}
        >
          About & Members
        </button>
        <button 
          className={`group-tab ${activeTab === 'activities' ? 'active' : ''}`}
          onClick={() => setActiveTab('activities')}
        >
          Activities
        </button>
        <button 
          className={`group-tab ${activeTab === 'documents' ? 'active' : ''}`}
          onClick={() => setActiveTab('documents')}
        >
          Documents
        </button>
        {isOwner && (
          <button 
            className={`group-tab ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            Settings
          </button>
        )}
      </div>

      <div className="group-content">
        {activeTab === 'about' && (
          <div className="group-members-section glass">
            <h2>Members</h2>
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
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '16px' }}>
              {canCreateActivity && (
                <Link to="/activities/new">
                  <Button size="sm">+ Create Activity</Button>
                </Link>
              )}
            </div>
            {!isMember ? (
              <div className="glass empty-state">
                <p>You must be a member to view group activities.</p>
              </div>
            ) : loadingContent ? (
              <p>Loading activities...</p>
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
                <p>No activities in this group yet.</p>
                {canCreateActivity && (
                  <Link to="/activities/new">
                    <Button style={{ marginTop: '16px' }}>Create Activity</Button>
                  </Link>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'documents' && (
          <div className="group-documents-section">
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '16px' }}>
              {canUploadDocument && (
                <Link to={`/documents/upload?groupId=${id}`}>
                  <Button size="sm">+ Upload</Button>
                </Link>
              )}
            </div>
            {!isMember ? (
              <div className="glass empty-state">
                <p>You must be a member to view group documents.</p>
              </div>
            ) : loadingContent ? (
              <p>Loading documents...</p>
            ) : documents.length > 0 ? (
              <div className="documents-grid">
                {documents.map(doc => (
                  <div key={doc.id} className="glass document-item">
                    <h4>{doc.title}</h4>
                    <p>{doc.file_name}</p>
                    <Link to={`/documents/${doc.id}`}>
                      <Button size="sm" variant="secondary">View</Button>
                    </Link>
                  </div>
                ))}
              </div>
            ) : (
              <div className="glass empty-state">
                <p>No documents in this group yet.</p>
                {canUploadDocument && (
                  <Link to={`/documents/upload?groupId=${id}`}>
                    <Button style={{ marginTop: '16px' }}>Upload Document</Button>
                  </Link>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'settings' && isOwner && (
          <div className="group-settings-section glass">
            <h2>Group Settings</h2>
            <form onSubmit={handleSaveSettings} style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '16px', maxWidth: '500px' }}>
              <Input
                label="Group Name"
                value={settingsForm.name}
                onChange={e => setSettingsForm({...settingsForm, name: e.target.value})}
                required
              />
              <Textarea
                label="Description"
                value={settingsForm.description}
                onChange={e => setSettingsForm({...settingsForm, description: e.target.value})}
              />
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '8px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input 
                    type="checkbox" 
                    checked={settingsForm.allowActivities}
                    onChange={(e) => setSettingsForm({...settingsForm, allowActivities: e.target.checked})}
                  />
                  <span>Allow members to create activities</span>
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input 
                    type="checkbox" 
                    checked={settingsForm.allowDocuments}
                    onChange={(e) => setSettingsForm({...settingsForm, allowDocuments: e.target.checked})}
                  />
                  <span>Allow members to upload documents</span>
                </label>
              </div>

              <div style={{ marginTop: '16px' }}>
                <Button type="submit" loading={savingSettings}>Save Settings</Button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
