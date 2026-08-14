import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { activitiesApi, type ActivityUpdate } from '../../api/activities';
import { useToast } from '../../components/Toast/ToastContext';
import Button from '../../components/Button/Button';
import LocationPicker from '../../components/Map/LocationPicker';
import './CreateActivity.css';

// Helper to format datetime string for datetime-local input
const formatForInput = (isoString: string) => {
  const d = new Date(isoString);
  const pad = (n: number) => n.toString().padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
};

export default function EditActivity() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const toast = useToast();
  
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: '',
    location_name: '',
    start_time: '',
    end_time: '',
    max_participants: 10,
    privacy: 'public' as 'public' | 'private',
    require_approval: true,
  });
  
  const [location, setLocation] = useState<[number, number] | null>(null);

  useEffect(() => {
    if (id) {
      activitiesApi.getById(id)
        .then(act => {
          setFormData({
            title: act.title,
            description: act.description || '',
            category: act.category || '',
            location_name: act.location_name || '',
            start_time: formatForInput(act.start_time),
            end_time: formatForInput(act.end_time),
            max_participants: act.max_participants,
            privacy: act.privacy as 'public' | 'private',
            require_approval: act.require_approval ?? true,
          });
          setLocation([act.latitude, act.longitude]);
          setInitialLoading(false);
        })
        .catch(() => {
          toast.error('Failed to load activity');
          navigate('/dashboard');
        });
    }
  }, [id]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    if (type === 'checkbox') {
      const { checked } = e.target as HTMLInputElement;
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    
    if (!location) {
      toast.error('Vui lòng chọn vị trí trên bản đồ');
      return;
    }

    const start = new Date(formData.start_time);
    const end = new Date(formData.end_time);

    if (end <= start) {
      toast.error('Thời gian kết thúc phải sau thời gian bắt đầu');
      return;
    }

    try {
      setLoading(true);
      const data: ActivityUpdate = {
        title: formData.title,
        description: formData.description,
        category: formData.category || undefined,
        location_name: formData.location_name || undefined,
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        max_participants: Number(formData.max_participants),
        privacy: formData.privacy,
        require_approval: formData.require_approval,
        latitude: location[0],
        longitude: location[1],
      };

      await activitiesApi.update(id, data);
      toast.success('Đã cập nhật hoạt động thành công!');
      navigate(`/activities/${id}`);
    } catch (error: any) {
      if (error.response?.data?.error?.message) {
        toast.error(error.response.data.error.message);
      } else {
        toast.error('Không thể cập nhật hoạt động');
      }
    } finally {
      setLoading(false);
    }
  };

  if (initialLoading) {
    return <div className="create-activity-page">Đang tải...</div>;
  }

  return (
    <div className="create-activity-page">
      <div className="create-activity-container glass">
        <h1 className="create-activity-title">Chỉnh sửa hoạt động</h1>
        <p className="create-activity-subtitle">Cập nhật thông tin chi tiết về sự kiện của bạn.</p>

        <form onSubmit={handleSubmit} className="create-activity-form">
          <div className="form-group">
            <label htmlFor="title">Tiêu đề <span className="required">*</span></label>
            <input
              type="text"
              id="title"
              name="title"
              className="form-input"
              value={formData.title}
              onChange={handleChange}
              required
              placeholder="Ví dụ: Cùng nhau học tập tại KTX"
              maxLength={100}
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">Mô tả <span className="required">*</span></label>
            <textarea
              id="description"
              name="description"
              className="form-input"
              value={formData.description}
              onChange={handleChange}
              required
              placeholder="Cho mọi người biết sự kiện này về điều gì..."
              rows={4}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="category">Danh mục</label>
              <input
                list="categories"
                id="category"
                name="category"
                className="form-input"
                value={formData.category}
                onChange={handleChange}
                placeholder="Chọn hoặc nhập danh mục"
                maxLength={50}
              />
              <datalist id="categories">
                <option value="Study" />
                <option value="Sports" />
                <option value="Social" />
                <option value="Gaming" />
                <option value="Music" />
              </datalist>
            </div>

            <div className="form-group">
              <label htmlFor="max_participants">Số người tham gia tối đa <span className="required">*</span></label>
              <input
                type="number"
                id="max_participants"
                name="max_participants"
                className="form-input"
                value={formData.max_participants}
                onChange={handleChange}
                required
                min={2}
                max={1000}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="start_time">Thời gian bắt đầu <span className="required">*</span></label>
              <input
                type="datetime-local"
                id="start_time"
                name="start_time"
                className="form-input"
                value={formData.start_time}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="end_time">Thời gian kết thúc <span className="required">*</span></label>
              <input
                type="datetime-local"
                id="end_time"
                name="end_time"
                className="form-input"
                value={formData.end_time}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="privacy">Quyền riêng tư</label>
            <select
              id="privacy"
              name="privacy"
              className="form-input"
              value={formData.privacy}
              onChange={handleChange}
            >
              <option value="public">Công khai (Mọi người đều có thể thấy)</option>
              <option value="private">Riêng tư (Chỉ dành cho người được mời hoặc ẩn)</option>
            </select>
          </div>

          <div className="form-group checkbox-group">
            <input
              type="checkbox"
              id="require_approval"
              name="require_approval"
              checked={formData.require_approval}
              onChange={handleChange}
            />
            <label htmlFor="require_approval">Yêu cầu phê duyệt để tham gia (Yêu cầu tham gia)</label>
          </div>

          <div className="form-group">
            <label htmlFor="location_name">Tên địa điểm</label>
            <input
              type="text"
              id="location_name"
              name="location_name"
              className="form-input"
              value={formData.location_name}
              onChange={handleChange}
              placeholder="Ví dụ: KTX Khu A, Sân bóng, v.v."
              maxLength={100}
            />
          </div>

          <div className="form-group map-group">
            <label>Vị trí trên bản đồ <span className="required">*</span></label>
            <LocationPicker 
              position={location} 
              onChange={(lat, lng) => setLocation([lat, lng])} 
            />
            {!location && <span className="error-text mt-1 text-sm block">Vui lòng nhấp vào bản đồ để chọn vị trí.</span>}
          </div>

          <div className="form-actions">
            <Button type="button" variant="secondary" onClick={() => navigate(-1)}>
              Hủy
            </Button>
            <Button type="submit" disabled={loading || !location}>
              {loading ? 'Đang lưu...' : 'Lưu thay đổi'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
