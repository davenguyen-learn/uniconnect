import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Users, Calendar, Plus, Compass, ArrowRight } from 'lucide-react';
import { groupsApi, type GroupResponse } from '../../api/groups';
import { useToast } from '../../components/Toast/ToastContext';
import Button from '../../components/Button/Button';
import CollectionLayout from '../../components/Layout/CollectionLayout';
import { resolveAvatarUrl } from '../../utils/avatar';
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
    { id: 'discover', label: 'Khám phá nhóm mới' },
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
          <Button>
            <Plus className="w-4 h-4 mr-1.5" />
            Tạo nhóm mới
          </Button>
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
          ? 'Hãy sang mục Khám phá để tìm các nhóm hoạt động thú vị và tham gia nhé!'
          : 'Thử tìm kiếm bằng từ khóa khác hoặc đăng ký thành lập nhóm của riêng bạn.'
      }
      emptyAction={
        activeTab === 'my' ? (
          <Button variant="secondary" onClick={() => setActiveTab('discover')}>
            <Compass className="w-4 h-4 mr-1.5" />
            Khám phá nhóm mới
          </Button>
        ) : (
          <Link to="/groups/new">
            <Button>
              <Plus className="w-4 h-4 mr-1.5" />
              Tạo nhóm mới
            </Button>
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
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white font-bold flex items-center justify-center text-sm shadow-sm shrink-0 overflow-hidden">
                {group.avatar_url ? (
                  <img
                    src={resolveAvatarUrl(group.avatar_url)!}
                    alt={group.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  group.name.charAt(0).toUpperCase()
                )}
              </div>
              <h3 className="group-card-title">{group.name}</h3>
            </div>
            <span className="group-card-members flex items-center gap-1">
              <Users className="w-3.5 h-3.5" />
              {group.member_count}
            </span>
          </div>
          <p className="group-card-desc">{group.description || 'Không có mô tả.'}</p>
          <div className="group-card-footer flex items-center justify-between text-xs text-slate-400 mt-auto pt-3 border-t border-slate-100">
            <span className="flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5" />
              {new Date(group.created_at).toLocaleDateString('vi-VN')}
            </span>
            <span className="flex items-center gap-0.5 text-indigo-600 font-semibold group-hover:translate-x-0.5 transition">
              Chi tiết <ArrowRight className="w-3.5 h-3.5" />
            </span>
          </div>
        </div>
      ))}
    </CollectionLayout>
  );
}

