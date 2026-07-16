import { useState, useEffect, useCallback } from 'react';
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
  
  // Search and Sort
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('newest');

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      if (activeTab === 'my') {
        const data = await groupsApi.getMyGroups();
        setMyGroups(data);
      } else {
        const data = await groupsApi.discoverGroups({ search, sort_by: sortBy });
        setDiscoverGroups(data);
      }
    } catch (err) {
      toast.error('Failed to load groups');
    } finally {
      setLoading(false);
    }
  }, [activeTab, search, sortBy, toast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
  };

  const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSortBy(e.target.value);
  };

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
      
      {activeTab === 'discover' && (
        <div className="groups-controls glass">
          <div className="groups-search">
            <input 
              type="text" 
              placeholder="Search groups..." 
              value={search}
              onChange={handleSearchChange}
              className="input-field"
            />
          </div>
          <div className="groups-sort">
            <select value={sortBy} onChange={handleSortChange} className="input-field">
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
              <option value="most_members">Most Members</option>
            </select>
          </div>
        </div>
      )}

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
              <h3>No groups found.</h3>
              {search ? (
                <p>Try adjusting your search terms.</p>
              ) : (
                <>
                  <p>Why not create your own group?</p>
                  <Link to="/groups/new">
                    <Button style={{marginTop: '1rem'}}>Create Group</Button>
                  </Link>
                </>
              )}
            </div>
          )
        )}
      </div>
    </div>
  );
}
