import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { activitiesApi, type ActivityResponse } from '../../api/activities';
import { useToast } from '../../components/Toast/ToastContext';
import Button from '../../components/Button/Button';
import CollectionLayout from '../../components/Layout/CollectionLayout';
import ActivityCard from '../../components/ActivityCard/ActivityCard';
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

  const tabs = [
    { id: 'hosting', label: 'Đang tổ chức' },
    { id: 'joined', label: 'Đã tham gia' },
  ];

  return (
    <CollectionLayout
      title="Hoạt động của tôi"
      action={
        <Link to="/activities/new">
          <Button>Tạo mới</Button>
        </Link>
      }
      tabs={tabs}
      activeTab={activeTab}
      onTabChange={(tabId) => setActiveTab(tabId as 'hosting' | 'joined')}
      loading={loading}
      loadingMessage="Đang tải hoạt động..."
      isEmpty={activities.length === 0}
      emptyTitle="Bạn chưa có hoạt động nào ở đây."
      emptyAction={
        activeTab === 'hosting' ? (
          <Link to="/activities/new">
            <Button variant="secondary">Tổ chức một hoạt động</Button>
          </Link>
        ) : undefined
      }
    >
      {activities.map(activity => (
        <ActivityCard key={activity.id} activity={activity} />
      ))}
    </CollectionLayout>
  );
}
