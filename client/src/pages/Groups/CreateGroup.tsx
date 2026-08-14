import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { groupsApi } from '../../api/groups';
import { useToast } from '../../components/Toast/ToastContext';
import Button from '../../components/Button/Button';
import Input, { Textarea } from '../../components/Input/Input';
import './CreateGroup.css';

export default function CreateGroup() {
  const navigate = useNavigate();
  const toast = useToast();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [publicDescription, setPublicDescription] = useState('');
  const [privateDescription, setPrivateDescription] = useState('');
  const [privacy, setPrivacy] = useState<'public' | 'private'>('public');
  const [requireApproval, setRequireApproval] = useState(true);
  const [allowActivities, setAllowActivities] = useState(true);
  const [allowDocuments, setAllowDocuments] = useState(true);

  // Custom Form Builder state for group membership
  const [customFormFields, setCustomFormFields] = useState<Array<{ id: string; label: string; field_type: string; is_required: boolean }>>([]);
  const [showFormBuilder, setShowFormBuilder] = useState(false);

  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setLoading(true);
    try {
      const payload: any = { 
        name, 
        description,
        public_description: publicDescription || undefined,
        private_description: privateDescription || undefined,
        privacy,
        require_approval: requireApproval,
        allow_member_activities: allowActivities,
        allow_member_documents: allowDocuments
      };

      if (customFormFields.length > 0) {
        payload.custom_form = {
          title: "Group Membership Form",
          description: "Please answer these questions to apply for group membership.",
          fields: customFormFields.map((f, idx) => ({
            label: f.label,
            field_type: f.field_type,
            is_required: f.is_required,
            order: idx
          }))
        };
      }

      const response = await groupsApi.createGroup(payload);
      toast.success('Tạo nhóm thành công!');
      navigate(`/groups/${response.id}`);
    } catch (err) {
      toast.error('Không thể tạo nhóm');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container create-group-page">
      <div className="glass create-group-card">
        <h1 className="create-group-title">Tạo nhóm</h1>
        
        <form onSubmit={handleSubmit} className="create-group-form">
          <Input 
            label="Tên nhóm" 
            placeholder="Ví dụ: Câu lạc bộ Khoa học Máy tính" 
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            maxLength={100}
          />
          
          <Textarea 
            label="Mô tả ngắn" 
            placeholder="Nhóm này về chủ đề gì?" 
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />

          <div className="form-group">
            <label htmlFor="privacy" className="form-label">Loại quyền riêng tư</label>
            <select
              id="privacy"
              className="form-select"
              value={privacy}
              onChange={(e) => setPrivacy(e.target.value as 'public' | 'private')}
            >
              <option value="public">Công khai (Bất kỳ ai cũng có thể xem và tham gia)</option>
              <option value="private">Riêng tư (Hạn chế thành viên, ẩn thông tin riêng tư)</option>
            </select>
          </div>

          <Textarea 
            label="Tổng quan công khai (Mọi người đều có thể thấy)" 
            placeholder="Quy tắc chi tiết, sứ mệnh, thông báo công khai..." 
            value={publicDescription}
            onChange={(e) => setPublicDescription(e.target.value)}
          />

          {privacy === 'private' && (
            <div className="callout callout--error">
              <Textarea 
                label="Mô tả riêng tư (Chỉ dành cho thành viên) 🔒" 
                placeholder="Link nhóm Discord/Zalo, link Google Drive riêng tư, mật mã cuộc họp (chỉ hiển thị cho thành viên được duyệt)..." 
                value={privateDescription}
                onChange={(e) => setPrivateDescription(e.target.value)}
              />
            </div>
          )}

          <div className="create-group-checkboxes">
            <label className="checkbox-label">
              <input 
                type="checkbox" 
                checked={requireApproval}
                onChange={(e) => setRequireApproval(e.target.checked)}
              />
              <span>Yêu cầu quản trị viên phê duyệt để tham gia (Yêu cầu tham gia)</span>
            </label>

            <label className="checkbox-label">
              <input 
                type="checkbox" 
                checked={allowActivities}
                onChange={(e) => setAllowActivities(e.target.checked)}
              />
              <span>Cho phép thành viên tạo hoạt động</span>
            </label>

            <label className="checkbox-label">
              <input 
                type="checkbox" 
                checked={allowDocuments}
                onChange={(e) => setAllowDocuments(e.target.checked)}
              />
              <span>Cho phép thành viên tải tài liệu lên</span>
            </label>
          </div>

          {/* Membership Custom Form Builder */}
          <div className="form-group">
            <div className="form-builder-toggle">
              <label className="form-label form-label--inline">Biểu mẫu đăng ký tham gia</label>
              <Button type="button" size="sm" variant="secondary" onClick={() => setShowFormBuilder(!showFormBuilder)}>
                {showFormBuilder ? 'Ẩn công cụ tạo biểu mẫu' : 'Thêm biểu mẫu đăng ký'}
              </Button>
            </div>

            {showFormBuilder && (
              <div className="form-builder-container">
                <p className="form-builder-hint">
                  Đặt câu hỏi cho các thành viên tương lai trước khi phê duyệt họ.
                </p>
                {customFormFields.map((field, index) => (
                  <div key={field.id} className="form-builder-row">
                    <div className="form-builder-row__field">
                      <label className="form-builder-label">Câu hỏi / Nhãn</label>
                      <input 
                        type="text" 
                        className="form-input" 
                        value={field.label} 
                        onChange={(e) => {
                          const newFields = [...customFormFields];
                          newFields[index].label = e.target.value;
                          setCustomFormFields(newFields);
                        }} 
                        placeholder="Ví dụ: Tại sao bạn muốn tham gia?"
                      />
                    </div>
                    <div className="form-builder-row__type">
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
                  + Thêm câu hỏi
                </Button>
              </div>
            )}
          </div>

          <div className="create-group-actions">
            <Button variant="ghost" type="button" onClick={() => navigate('/groups')}>
              Hủy
            </Button>
            <Button type="submit" loading={loading} disabled={!name.trim()}>
              Tạo nhóm
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
