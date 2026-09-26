import { useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { groupsApi } from '../../api/groups';
import { useToast } from '../../components/Toast/ToastContext';
import Button from '../../components/Button/Button';
import {
  Users,
  UserCheck,
  Sparkles,
  FileText,
  Plus,
  Trash2,
  ArrowLeft,
  Info,
  ShieldCheck,
} from 'lucide-react';
import './CreateGroup.css';

export default function CreateGroup() {
  const navigate = useNavigate();
  const toast = useToast();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [publicDescription, setPublicDescription] = useState('');
  const [requireApproval, setRequireApproval] = useState(true);
  const [allowActivities, setAllowActivities] = useState(true);

  // Custom Form Builder state for group membership
  const [customFormFields, setCustomFormFields] = useState<
    Array<{ id: string; label: string; field_type: string; is_required: boolean }>
  >([]);

  const [loading, setLoading] = useState(false);
  const [attemptedSubmit, setAttemptedSubmit] = useState(false);

  const isNameMissing = attemptedSubmit && !name.trim();

  const handleAddField = () => {
    setCustomFormFields((prev) => [
      ...prev,
      {
        id: Math.random().toString(),
        label: '',
        field_type: 'text',
        is_required: true,
      },
    ]);
  };

  const handleRemoveField = (index: number) => {
    setCustomFormFields((prev) => prev.filter((_, i) => i !== index));
  };

  const handleFieldChange = (index: number, key: string, value: any) => {
    setCustomFormFields((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], [key]: value };
      return next;
    });
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setAttemptedSubmit(true);

    if (!name.trim()) {
      toast.error('Vui lòng nhập tên nhóm / câu lạc bộ');
      return;
    }

    const filledCustomFields = customFormFields.filter((f) => f.label.trim().length > 0);
    if (customFormFields.length > 0 && filledCustomFields.length < customFormFields.length) {
      toast.error('Vui lòng nhập đầy đủ câu hỏi cho các trường biểu mẫu hoặc nhấn nút xóa trường trống');
      return;
    }

    setLoading(true);
    try {
      const payload: any = {
        name: name.trim(),
        description: description.trim() || undefined,
        public_description: publicDescription.trim() || undefined,
        privacy: 'public',
        require_approval: requireApproval,
        allow_member_activities: allowActivities,
      };

      if (filledCustomFields.length > 0) {
        payload.custom_form = {
          title: 'Biểu mẫu xin gia nhập nhóm',
          description: 'Vui lòng trả lời các câu hỏi sau để Quản trị viên duyệt tham gia nhóm.',
          fields: filledCustomFields.map((f, idx) => ({
            label: f.label.trim(),
            field_type: f.field_type === 'boolean' ? 'checkbox' : f.field_type,
            is_required: f.is_required,
            order: idx,
          })),
        };
      }

      const response = await groupsApi.createGroup(payload);
      toast.success('Tạo nhóm thành công!');
      navigate(`/groups/${response.id}`);
    } catch (err: any) {
      const errData = err.response?.data?.error;
      if (errData?.details?.fields && errData.details.fields.length > 0) {
        const detailMsg = errData.details.fields.map((f: any) => `${f.field}: ${f.message}`).join(', ');
        toast.error(`Lỗi dữ liệu: ${detailMsg}`);
      } else if (errData?.message) {
        toast.error(errData.message);
      } else if (err.response?.data?.detail) {
        toast.error(err.response.data.detail);
      } else {
        toast.error('Không thể tạo nhóm');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="create-group-page">
      <div className="create-group-container">
        {/* Navigation & Header */}
        <div className="create-group-header">
          <Link to="/groups" className="create-group-back-btn">
            <ArrowLeft size={18} />
            <span>Danh sách nhóm</span>
          </Link>
          <div className="create-group-header-text">
            <h1 className="create-group-heading">Tạo nhóm mới</h1>
          </div>
        </div>

        <form noValidate onSubmit={handleSubmit} className="create-group-form">
          {/* Hero Name Input */}
          <div className="create-group-hero-section">
            <div className="create-group-hero-wrapper">
              <input
                type="text"
                id="group-name"
                name="name"
                className={`create-group-hero-input ${isNameMissing ? 'input-error' : ''}`}
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                placeholder="Nhập tên nhóm hoặc câu lạc bộ..."
                maxLength={100}
                autoFocus
              />
            </div>
            {isNameMissing && (
              <span className="field-error-msg">Vui lòng nhập tên nhóm / câu lạc bộ</span>
            )}
          </div>

          {/* Section 1: Thông tin cơ bản */}
          <div className="create-group-card">
            <div className="create-group-section-title">
              <div className="section-icon-wrap">
                <Info size={18} />
              </div>
              <div>
                <h3>Thông tin cơ bản</h3>
              </div>
            </div>

            <div className="create-group-fields">
              <div className="form-group">
                <label htmlFor="description" className="create-group-label">
                  Mô tả ngắn gọn
                </label>
                <textarea
                  id="description"
                  name="description"
                  className="form-input"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Mô tả súc tích về nhóm trong 1-2 câu (hiển thị trên thẻ nhóm và tìm kiếm)..."
                  rows={2}
                  maxLength={250}
                />
              </div>

              <div className="form-group">
                <label htmlFor="publicDescription" className="create-group-label">
                  Giới thiệu chi tiết
                </label>
                <textarea
                  id="publicDescription"
                  name="publicDescription"
                  className="form-input"
                  value={publicDescription}
                  onChange={(e) => setPublicDescription(e.target.value)}
                  placeholder="Mục tiêu hoạt động, sứ mệnh, quyền lợi khi tham gia, lịch sinh hoạt định kỳ..."
                  rows={4}
                />
              </div>
            </div>
          </div>

          {/* Section 2: Quản lý & Cấu hình */}
          <div className="create-group-card">
            <div className="create-group-section-title">
              <div className="section-icon-wrap">
                <ShieldCheck size={18} />
              </div>
              <div>
                <h3>Cấu hình nhóm</h3>
              </div>
            </div>

            {/* Switch 1: Approval */}
            <div
              className={`approval-toggle-card ${requireApproval ? 'active' : ''}`}
              onClick={() => setRequireApproval((prev) => !prev)}
              role="button"
              tabIndex={0}
            >
              <div className="approval-toggle-content">
                <div className="approval-toggle-icon">
                  <UserCheck size={18} />
                </div>
                <div className="approval-toggle-info">
                  <span className="approval-toggle-title">Yêu cầu xét duyệt thành viên</span>
                  <span className="approval-toggle-desc">
                    Quản trị viên cần duyệt đơn xin gia nhập trước khi sinh viên trở thành thành viên chính thức.
                  </span>
                </div>
              </div>
              <div className={`approval-switch ${requireApproval ? 'on' : ''}`}>
                <span className="approval-switch-handle" />
              </div>
            </div>

            {/* Switch 2: Member Activities */}
            <div
              className={`approval-toggle-card ${allowActivities ? 'active' : ''}`}
              onClick={() => setAllowActivities((prev) => !prev)}
              role="button"
              tabIndex={0}
            >
              <div className="approval-toggle-content">
                <div className="approval-toggle-icon activity-icon">
                  <Sparkles size={18} />
                </div>
                <div className="approval-toggle-info">
                  <span className="approval-toggle-title">Cho phép thành viên tự tạo hoạt động</span>
                  <span className="approval-toggle-desc">
                    Thành viên có thể chủ động tạo và lên lịch các hoạt động cho nhóm (nếu tắt, chỉ Ban quản trị mới có quyền tạo).
                  </span>
                </div>
              </div>
              <div className={`approval-switch ${allowActivities ? 'on' : ''}`}>
                <span className="approval-switch-handle" />
              </div>
            </div>
          </div>

          {/* Section 3: Biểu mẫu đăng ký tham gia */}
          <div className="create-group-card">
            <div className="create-group-section-title">
              <div className="section-icon-wrap">
                <FileText size={18} />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-semibold">Biểu mẫu đăng ký gia nhập</h3>
                  <Button
                    type="button"
                    size="sm"
                    variant="secondary"
                    onClick={handleAddField}
                  >
                    <Plus size={15} className="mr-1" />
                    Thêm câu hỏi
                  </Button>
                </div>
              </div>
            </div>

            <div className="form-builder-container">
              {customFormFields.length === 0 ? (
                <div className="form-builder-empty">
                  <p>Chưa có câu hỏi đăng ký nào.</p>
                  <span className="text-xs text-[var(--color-text-secondary)]">
                    Nhấn <strong>"+ Thêm câu hỏi"</strong> ở trên nếu bạn muốn người xin vào nhóm trả lời một số câu hỏi trước khi duyệt.
                  </span>
                </div>
              ) : (
                <div className="form-builder-list">
                  {customFormFields.map((field, index) => (
                    <div key={field.id} className="form-builder-row">
                      <div className="form-builder-row__field">
                        <label className="form-builder-label">Câu hỏi</label>
                        <input
                          type="text"
                          className="form-input rounded-lg"
                          value={field.label}
                          placeholder="Ví dụ: MSSV, Khoa, Lý do muốn tham gia..."
                          onChange={(e) => handleFieldChange(index, 'label', e.target.value)}
                        />
                      </div>
                      <div className="form-builder-row__type--wide">
                        <label className="form-builder-label">Loại câu trả lời</label>
                        <select
                          className="form-input rounded-lg"
                          value={field.field_type === 'boolean' ? 'checkbox' : field.field_type}
                          onChange={(e) => handleFieldChange(index, 'field_type', e.target.value)}
                        >
                          <option value="text">Văn bản</option>
                          <option value="number">Số</option>
                          <option value="checkbox">Có / Không</option>
                        </select>
                      </div>
                      <div className="form-builder-row__req">
                        <label className="form-builder-switch-label-wrap">
                          <input
                            type="checkbox"
                            className="sr-only"
                            checked={field.is_required}
                            onChange={(e) => handleFieldChange(index, 'is_required', e.target.checked)}
                          />
                          <div className={`form-builder-switch ${field.is_required ? 'on' : ''}`}>
                            <span className="form-builder-switch-handle" />
                          </div>
                          <span className="form-builder-switch-text">Bắt buộc</span>
                        </label>
                      </div>
                      <button
                        type="button"
                        className="form-builder-delete-btn"
                        onClick={() => handleRemoveField(index)}
                        title="Xóa câu hỏi này"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Form Actions Footer */}
          <div className="create-group-actions">
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate('/groups')}
            >
              Hủy
            </Button>
            <Button
              type="submit"
              disabled={loading || !name.trim()}
              loading={loading}
              className="create-group-submit-btn"
            >
              <Users size={16} className="mr-1.5" />
              <span>{loading ? 'Đang tạo...' : 'Tạo nhóm'}</span>
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
