import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { groupsApi, type GroupResponse } from '../../api/groups';
import { useToast } from '../../components/Toast/ToastContext';
import Button from '../../components/Button/Button';
import CollectionLayout from '../../components/Layout/CollectionLayout';
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
    } catch {
      toast.error('Failed to load groups');
    } finally {
      setLoading(false);
    }
  }, [activeTab, search, sortBy, toast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const currentGroups = activeTab === 'my' ? myGroups : discoverGroups;

  const tabs = [
    { id: 'my', label: 'Nhóm của tôi', count: myGroups.length },
    { id: 'discover', label: 'Khám phá' },
  ];

  const sortOptions = [
    { label: 'Mới nhất', value: 'newest' },
    { label: 'Cũ nhất', value: 'oldest' },
    { label: 'Nhiều thành viên nhất', value: 'most_members' },
  ];

  return (
    <CollectionLayout
      title="Nhóm"
      action={
        <Link to="/groups/new">
          <Button>Tạo Nhóm</Button>
        </Link>
      }
      tabs={tabs}
      activeTab={activeTab}
      onTabChange={(tabId) => setActiveTab(tabId as 'my' | 'discover')}
      searchPlaceholder={activeTab === 'discover' ? 'Tìm kiếm nhóm theo tên...' : undefined}
      searchValue={activeTab === 'discover' ? search : undefined}
      onSearchChange={activeTab === 'discover' ? setSearch : undefined}
      sortOptions={activeTab === 'discover' ? sortOptions : undefined}
      sortValue={activeTab === 'discover' ? sortBy : undefined}
      onSortChange={activeTab === 'discover' ? setSortBy : undefined}
      loading={loading}
      loadingMessage="Đang tải danh sách nhóm..."
      isEmpty={currentGroups.length === 0}
      emptyTitle={activeTab === 'my' ? "Bạn chưa tham gia nhóm nào." : "Không tìm thấy nhóm nào."}
      emptyMessage={
        activeTab === 'my'
          ? 'Hãy sang mục Khám phá để tìm các nhóm thú vị và tham gia nhé!'
          : 'Thử tìm kiếm bằng từ khóa khác hoặc tạo nhóm của riêng bạn.'
      }
      emptyAction={
        activeTab === 'my' ? (
          <Button variant="secondary" onClick={() => setActiveTab('discover')}>Khám phá nhóm</Button>
        ) : (
          <Link to="/groups/new">
            <Button>Tạo Nhóm</Button>
          </Link>
        )
      }
    >
      {currentGroups.map((group) => (
        <div
          key={group.id}
          className="group-card glass"
          onClick={() => navigate(`/groups/${group.id}`)}
        >
          <div className="group-card-header">
            <h3 className="group-card-title">{group.name}</h3>
            <span className="group-card-members">{group.member_count} thành viên</span>
          </div>
          <p className="group-card-desc">{group.description || 'Không có mô tả.'}</p>
          <div className="group-card-footer">
            <span>Tạo ngày {new Date(group.created_at).toLocaleDateString('vi-VN')}</span>
          </div>
        </div>
      ))}
    </CollectionLayout>
  );
}
