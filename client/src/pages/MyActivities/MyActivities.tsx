import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { activitiesApi, type ActivityResponse } from '../../api/activities';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../components/Toast/ToastContext';
import Button from '../../components/Button/Button';
import CollectionLayout, { type CollectionTab } from '../../components/Layout/CollectionLayout';
import ActivityCard from '../../components/ActivityCard/ActivityCard';
import { CertificateModal } from '../../components/CertificateModal/CertificateModal';
import './MyActivities.css';

type FilterType = 'all' | 'hosting' | 'upcoming' | 'past';

export default function MyActivities() {
  const { user } = useAuth();
  const toast = useToast();
  const [allActivities, setAllActivities] = useState<ActivityResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState<FilterType>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCertificateActivityId, setSelectedCertificateActivityId] = useState<string | null>(null);

  useEffect(() => {
    loadActivities();
  }, []);

  async function loadActivities() {
    try {
      setLoading(true);
      const [joinedRes, hostedRes] = await Promise.all([
        activitiesApi.getJoinedActivities({ limit: 100 }),
        activitiesApi.getMyActivities({ limit: 100 }),
      ]);

      const map = new Map<string, ActivityResponse>();
      // Process hosted activities
      for (const act of hostedRes.items) {
        map.set(act.id, act);
      }
      // Process joined activities (merge and preserve joined_at, attendance status)
      for (const act of joinedRes.items) {
        if (!map.has(act.id)) {
          map.set(act.id, act);
        } else {
          const existing = map.get(act.id)!;
          if (act.joined_at && !existing.joined_at) {
            existing.joined_at = act.joined_at;
          }
          if (act.attendance_confirmed !== undefined) {
            existing.attendance_confirmed = act.attendance_confirmed;
          }
        }
      }

      const combined = Array.from(map.values());
      // Sort by action timestamp (time user joined or created the activity, newest first)
      combined.sort((a, b) => {
        const timeA = new Date(a.joined_at || a.created_at).getTime();
        const timeB = new Date(b.joined_at || b.created_at).getTime();
        return timeB - timeA;
      });

      setAllActivities(combined);
    } catch (error) {
      toast.error('Không thể tải danh sách hoạt động');
    } finally {
      setLoading(false);
    }
  }

  async function handleDeleteActivity(activityId: string) {
    const confirm = window.confirm('Bạn có chắc chắn muốn hủy hoạt động này? Hành động này không thể hoàn tác.');
    if (!confirm) return;

    try {
      await activitiesApi.delete(activityId);
      toast.success('Đã hủy hoạt động thành công');
      setAllActivities(prev => prev.filter(a => a.id !== activityId));
    } catch (error: any) {
      toast.error(error?.message || 'Không thể hủy hoạt động');
    }
  }

  const handleShare = (actId: string) => {
    const shareUrl = `${window.location.origin}/activities/${actId}`;
    navigator.clipboard.writeText(shareUrl).then(() => {
      toast.success('Đã sao chép liên kết hoạt động!');
    }).catch(() => {
      toast.info(`Liên kết: ${shareUrl}`);
    });
  };

  const counts = useMemo(() => {
    const now = new Date();
    return {
      all: allActivities.length,
      hosting: allActivities.filter(a => a.host_id === user?.id).length,
      upcoming: allActivities.filter(a => new Date(a.end_time) >= now).length,
      past: allActivities.filter(a => new Date(a.end_time) < now).length,
    };
  }, [allActivities, user?.id]);

  const tabs: CollectionTab[] = [
    { id: 'all', label: 'Tất cả', count: counts.all },
    { id: 'hosting', label: 'Bản thân tổ chức', count: counts.hosting },
    { id: 'upcoming', label: 'Sắp diễn ra', count: counts.upcoming },
    { id: 'past', label: 'Đã diễn ra', count: counts.past },
  ];

  const filteredActivities = useMemo(() => {
    const now = new Date();
    return allActivities.filter((act) => {
      // Search filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchTitle = act.title.toLowerCase().includes(q);
        const matchLocation = (act.meeting_location || act.location_name || '').toLowerCase().includes(q);
        if (!matchTitle && !matchLocation) return false;
      }

      if (activeFilter === 'hosting') {
        return act.host_id === user?.id;
      }

      if (activeFilter === 'upcoming') {
        return new Date(act.end_time) >= now;
      }

      if (activeFilter === 'past') {
        return new Date(act.end_time) < now;
      }

      return true;
    });
  }, [allActivities, activeFilter, searchQuery, user?.id]);

  return (
    <>
      <CollectionLayout
        title="Hoạt động của tôi"
        gridColumns={2}
        tabs={tabs}
        activeTab={activeFilter}
        onTabChange={(tabId) => {
          if (tabId === activeFilter && tabId !== 'all') {
            setActiveFilter('all');
          } else {
            setActiveFilter(tabId as FilterType);
          }
        }}
        searchPlaceholder="Tìm theo tên hoạt động hoặc địa điểm..."
        searchValue={searchQuery}
        onSearchChange={setSearchQuery}
        loading={loading}
        loadingMessage="Đang tải hoạt động..."
        isEmpty={filteredActivities.length === 0}
        emptyTitle={
          allActivities.length === 0
            ? 'Chưa có hoạt động nào'
            : 'Không tìm thấy hoạt động phù hợp'
        }
        emptyMessage={
          allActivities.length === 0
            ? 'Bạn chưa tham gia hay tổ chức hoạt động nào. Hãy khám phá các sự kiện thú vị quanh bạn!'
            : 'Không có hoạt động nào khớp với bộ lọc hoặc từ khóa tìm kiếm.'
        }
        emptyAction={
          allActivities.length === 0 ? (
            <Link to="/dashboard">
              <Button variant="secondary">Khám phá hoạt động</Button>
            </Link>
          ) : (
            <Button
              variant="secondary"
              onClick={() => {
                setActiveFilter('all');
                setSearchQuery('');
              }}
            >
              Xem tất cả
            </Button>
          )
        }
      >
        {filteredActivities.map((activity) => (
          <ActivityCard
            key={activity.id}
            activity={activity}
            isRegistered={true}
            onDelete={
              activity.host_id === user?.id && new Date(activity.end_time) >= new Date()
                ? handleDeleteActivity
                : undefined
            }
            onShare={handleShare}
            onCertificate={(actId) => setSelectedCertificateActivityId(actId)}
          />
        ))}
      </CollectionLayout>

      {/* Certificate Modal */}
      {selectedCertificateActivityId && (
        <CertificateModal
          isOpen={!!selectedCertificateActivityId}
          onClose={() => setSelectedCertificateActivityId(null)}
          activityId={selectedCertificateActivityId}
        />
      )}
    </>
  );
}
