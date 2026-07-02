import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { activitiesApi, type ActivityResponse } from '../../api/activities';
import { useToast } from '../../components/Toast/ToastContext';
import Button from '../../components/Button/Button';
import './MyActivities.css';

export default function MyActivities() {
  const toast = useToast();
  const [activities, setActivities] = useState<ActivityResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'hosting' | 'joined'>('hosting');

  useEffect(() => {
    loadActivities();
  }, [activeTab]);

  async function loadActivities() {
    try {
      setLoading(true);
      if (activeTab === 'hosting') {
        const res = await activitiesApi.getMyActivities();
        setActivities(res.items);
      } else {
        const res = await activitiesApi.getJoinedActivities();
        setActivities(res.items);
      }
    } catch (error) {
      toast.error('Failed to load activities');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="my-activities-page">
      <div className="my-activities-container">
        <div className="page-header">
          <h1>My Activities</h1>
          <Link to="/activities/new">
            <Button>Create New</Button>
          </Link>
        </div>

        <div className="tabs">
          <button 
            className={`tab ${activeTab === 'hosting' ? 'active' : ''}`}
            onClick={() => setActiveTab('hosting')}
          >
            Hosting
          </button>
          <button 
            className={`tab ${activeTab === 'joined' ? 'active' : ''}`}
            onClick={() => setActiveTab('joined')}
          >
            Joined
          </button>
        </div>

        <div className="activities-grid">
          {loading ? (
            <div className="loading-state">Loading...</div>
          ) : activities.length === 0 ? (
            <div className="empty-state glass">
              <p>You don't have any activities here yet.</p>
              {activeTab === 'hosting' && (
                <Link to="/activities/new">
                  <Button variant="secondary" className="mt-4">Host an Activity</Button>
                </Link>
              )}
            </div>
          ) : (
            activities.map(activity => (
              <div key={activity.id} className="activity-card glass">
                <div className="card-header">
                  <span className="category">{activity.category || 'General'}</span>
                  <span className={`privacy ${activity.privacy}`}>{activity.privacy}</span>
                </div>
                <h3>{activity.title}</h3>
                <p className="time">
                  {new Date(activity.start_time).toLocaleDateString()} at {new Date(activity.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                </p>
                <div className="stats">
                  <span>{activity.current_participants}/{activity.max_participants} joined</span>
                </div>
                <div className="card-actions">
                  <Link to={`/activities/${activity.id}`}>
                    <Button size="sm" fullWidth>Manage</Button>
                  </Link>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
