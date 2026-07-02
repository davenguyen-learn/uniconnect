import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { groupsApi, type GroupResponse } from '../../api/groups';
import { useToast } from '../../components/Toast/ToastContext';
import Button from '../../components/Button/Button';
import './Groups.css';

export default function Groups() {
  const toast = useToast();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'my' | 'discover'>('my');
  
  const [myGroups, setMyGroups] = useState<GroupResponse[]>([]);
  const [discoverGroups, setDiscoverGroups] = useState<GroupResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [activeTab]);

  async function loadData() {
    setLoading(true);
    try {
      if (activeTab === 'my') {
        const data = await groupsApi.getMyGroups();
        setMyGroups(data);
      } else {
        const data = await groupsApi.discoverGroups();
        setDiscoverGroups(data);
      }
    } catch (err) {
      toast.error('Failed to load groups');
    } finally {
      setLoading(false);
    }
  }

  const renderGroupCard = (group: GroupResponse) => (
    <div key={group.id} className="group-card glass" onClick={() => navigate(`/groups/${group.id}`)}>
      <div className="group-card-header">
        <h3 className="group-card-title">{group.name}</h3>
        <span className="group-card-members">{group.member_count} members</span>
      </div>
      <p className="group-card-desc">{group.description || 'No description provided.'}</p>
      <div className="group-card-footer">
        <span>Created {new Date(group.created_at).toLocaleDateString()}</span>
      </div>
    </div>
  );

  return (
    <div className="container groups-page">
      <div className="groups-header">
        <div>
          <h1 className="gradient-text">Groups</h1>
          <p className="groups-subtitle">Connect with people who share your interests.</p>
        </div>
        <Link to="/groups/new">
          <Button>+ Create Group</Button>
        </Link>
      </div>

      <div className="groups-tabs">
        <button 
          className={`groups-tab ${activeTab === 'my' ? 'active' : ''}`}
          onClick={() => setActiveTab('my')}
        >
          My Groups
        </button>
        <button 
          className={`groups-tab ${activeTab === 'discover' ? 'active' : ''}`}
          onClick={() => setActiveTab('discover')}
        >
          Discover
        </button>
      </div>

      <div className="groups-grid">
        {loading ? (
          <div className="groups-loading">Loading groups...</div>
        ) : activeTab === 'my' ? (
          myGroups.length > 0 ? (
            myGroups.map(renderGroupCard)
          ) : (
            <div className="groups-empty glass">
              <h3>You haven't joined any groups yet.</h3>
              <p>Explore the Discover tab to find interesting groups to join!</p>
              <Button onClick={() => setActiveTab('discover')} style={{marginTop: '1rem'}}>
                Discover Groups
              </Button>
            </div>
          )
        ) : (
          discoverGroups.length > 0 ? (
            discoverGroups.map(renderGroupCard)
          ) : (
            <div className="groups-empty glass">
              <h3>No new groups found.</h3>
              <p>Why not create your own group?</p>
              <Link to="/groups/new">
                <Button style={{marginTop: '1rem'}}>Create Group</Button>
              </Link>
            </div>
          )
        )}
      </div>
    </div>
  );
}
