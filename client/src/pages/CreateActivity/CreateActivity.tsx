import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { activitiesApi, type ActivityCreate } from '../../api/activities';
import { useToast } from '../../components/Toast/ToastContext';
import Button from '../../components/Button/Button';
import LocationPicker from '../../components/Map/LocationPicker';
import './CreateActivity.css';

export default function CreateActivity() {
  const navigate = useNavigate();
  const toast = useToast();
  
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    private_description: '',
    category: '',
    location_name: '',
    start_time: '',
    end_time: '',
    max_participants: 10,
    privacy: 'public' as 'public' | 'private',
    require_approval: true,
  });
  
  const [location, setLocation] = useState<[number, number] | null>(null);
  
  // Custom Form Builder state
  const [customFormFields, setCustomFormFields] = useState<Array<{ id: string, label: string, field_type: string, is_required: boolean }>>([]);
  const [showFormBuilder, setShowFormBuilder] = useState(false);

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
      const data: ActivityCreate = {
        title: formData.title,
        description: formData.description,
        private_description: formData.private_description || undefined,
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

      if (customFormFields.length > 0) {
        data.custom_form = {
          title: "Join Application Form",
          description: "Please fill out this form to join.",
          fields: customFormFields.map((f, idx) => ({
            label: f.label,
            field_type: f.field_type as any,
            is_required: f.is_required,
            order: idx
          }))
        };
      }

      const newActivity = await activitiesApi.create(data);
      toast.success('Đã tạo hoạt động thành công!');
      navigate(`/activities/${newActivity.id}`);
    } catch (error) {
      toast.error('Không thể tạo hoạt động');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="create-activity-page">
      <div className="create-activity-container glass">
        <h1 className="create-activity-title">Tổ chức hoạt động</h1>
        <p className="create-activity-subtitle">Tạo sự kiện mới và mời những người khác tham gia.</p>

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

          {formData.privacy === 'private' && (
            <div className="form-group private-field-callout">
              <label htmlFor="private_description">Mô tả riêng tư (Chỉ dành cho thành viên) 🔒</label>
              <textarea
                id="private_description"
                name="private_description"
                className="form-input"
                value={formData.private_description}
                onChange={handleChange}
                placeholder="Hướng dẫn bí mật, link Zoom, hoặc địa chỉ chính xác (chỉ được tiết lộ cho người tham gia được phê duyệt)..."
                rows={3}
              />
            </div>
          )}

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

          <div className="form-group">
            <div className="form-builder-toggle">
              <label>Biểu mẫu tham gia tùy chỉnh</label>
              <Button type="button" size="sm" variant="secondary" onClick={() => setShowFormBuilder(!showFormBuilder)}>
                {showFormBuilder ? 'Ẩn công cụ tạo biểu mẫu' : 'Thêm trường biểu mẫu'}
              </Button>
            </div>
            {showFormBuilder && (
              <div className="form-builder-container">
                <p className="form-builder-hint">
                  Yêu cầu người dùng điền các trường cụ thể khi tham gia.
                </p>
                {customFormFields.map((field, index) => (
                  <div key={field.id} className="form-builder-row">
                    <div className="form-builder-row__field">
                      <label className="form-builder-label">Nhãn trường</label>
                      <input 
                        type="text" 
                        className="form-input" 
                        value={field.label} 
                        onChange={(e) => {
                          const newFields = [...customFormFields];
                          newFields[index].label = e.target.value;
                          setCustomFormFields(newFields);
                        }} 
                      />
                    </div>
                    <div className="form-builder-row__type--wide">
                      <label className="form-builder-label">Loại</label>
                      <select 
                        className="form-input" 
                        value={field.field_type}
                        onChange={(e) => {
                          const newFields = [...customFormFields];
                          newFields[index].field_type = e.target.value;
                          setCustomFormFields(newFields);
                        }}
                      >
                        <option value="text">Văn bản</option>
                        <option value="number">Số</option>
                        <option value="boolean">Hộp kiểm</option>
                      </select>
                    </div>
                    <div className="form-builder-row__req">
                      <label className="form-builder-req-label">
                        <input 
                          type="checkbox" 
                          checked={field.is_required}
                          onChange={(e) => {
                            const newFields = [...customFormFields];
                            newFields[index].is_required = e.target.checked;
                            setCustomFormFields(newFields);
                          }}
                        /> Bắt buộc
                      </label>
                    </div>
                    <Button 
                      type="button" 
                      variant="secondary" 
                      onClick={() => setCustomFormFields(customFormFields.filter((_, i) => i !== index))}
                    >
                      X
                    </Button>
                  </div>
                ))}
                <Button 
                  type="button" 
                  size="sm" 
                  onClick={() => setCustomFormFields([...customFormFields, { id: Math.random().toString(), label: '', field_type: 'text', is_required: true }])}
                >
                  + Thêm trường
                </Button>
              </div>
            )}
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
              {loading ? 'Đang tạo...' : 'Tạo hoạt động'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
