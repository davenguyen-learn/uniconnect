import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { activitiesApi, type ActivityCreate } from '../../api/activities';
import { calendarApi, type ConflictInfo } from '../../api/calendar';
import { trophiesApi, type TrophyResponse } from '../../api/trophies';
import { useToast } from '../../components/Toast/ToastContext';
import { useAuth } from '../../contexts/AuthContext';
import Button from '../../components/Button/Button';
import LocationPicker from '../../components/Map/LocationPicker';
import './CreateActivity.css';

export default function CreateActivity() {
  const navigate = useNavigate();
  const toast = useToast();
  const { user } = useAuth();

  const isOrg = user?.role === 'edu_org' || user?.role === 'admin' || !!user?.is_verified;

  const [loading, setLoading] = useState(false);
  const [isSocialWork, setIsSocialWork] = useState(false);
  const [socialWorkDays, setSocialWorkDays] = useState<number>(1);

  // Trophy & Attendance state for Organization hosts
  const [hasTrophy, setHasTrophy] = useState(false);
  const [selectedTrophyId, setSelectedTrophyId] = useState('');
  const [availableTrophies, setAvailableTrophies] = useState<TrophyResponse[]>([]);
  const [attendanceMode, setAttendanceMode] = useState<'manual' | 'auto' | 'qr_code'>('manual');
  const [checkInRadius, setCheckInRadius] = useState<number>(300);
  const [showCreateTrophyModal, setShowCreateTrophyModal] = useState(false);
  const [creatingTrophy, setCreatingTrophy] = useState(false);
  const [newTrophy, setNewTrophy] = useState({
    name: '',
    icon: '🏆',
    points: 50,
    description: '',
  });

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    private_description: '',
    category: '',
    meeting_location: '',
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

  // Schedule conflict pre-validation state
  const [scheduleConflict, setScheduleConflict] = useState<ConflictInfo | null>(null);
  const [checkingConflict, setCheckingConflict] = useState(false);

  useEffect(() => {
    if (isOrg) {
      trophiesApi.list().then(res => {
        setAvailableTrophies(res);
        if (res.length > 0) {
          setSelectedTrophyId(res[0].id);
        }
      }).catch(() => {});
    }
  }, [isOrg]);

  useEffect(() => {
    if (formData.start_time && formData.end_time) {
      const s = new Date(formData.start_time);
      const e = new Date(formData.end_time);
      if (e > s) {
        setCheckingConflict(true);
        calendarApi
          .checkConflict({
            start_time: s.toISOString(),
            end_time: e.toISOString(),
          })
          .then((res) => setScheduleConflict(res.has_conflict ? res : null))
          .catch(() => setScheduleConflict(null))
          .finally(() => setCheckingConflict(false));
      } else {
        setScheduleConflict(null);
      }
    } else {
      setScheduleConflict(null);
    }
  }, [formData.start_time, formData.end_time]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    if (type === 'checkbox') {
      const { checked } = e.target as HTMLInputElement;
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleQuickCreateTrophy = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTrophy.name.trim()) {
      toast.error('Vui lòng nhập tên Trophy');
      return;
    }
    try {
      setCreatingTrophy(true);
      const created = await trophiesApi.create({
        name: newTrophy.name.trim(),
        description: newTrophy.description.trim() || undefined,
        points: Number(newTrophy.points) || 0,
        icon: newTrophy.icon || '🏆',
      });
      setAvailableTrophies(prev => [created, ...prev]);
      setSelectedTrophyId(created.id);
      setShowCreateTrophyModal(false);
      setNewTrophy({ name: '', icon: '🏆', points: 50, description: '' });
      toast.success('Đã tạo Trophy thành công!');
    } catch {
      toast.error('Không thể tạo Trophy (có thể tên đã tồn tại)');
    } finally {
      setCreatingTrophy(false);
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
      const canAssignSocialWork = user?.role === 'edu_org' || user?.role === 'admin';
      const data: ActivityCreate = {
        title: formData.title,
        description: formData.description,
        private_description: formData.private_description || undefined,
        category: formData.category || undefined,
        meeting_location: formData.meeting_location || formData.location_name || undefined,
        location_name: formData.meeting_location || formData.location_name || undefined,
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        max_participants: Number(formData.max_participants),
        privacy: formData.privacy,
        require_approval: formData.require_approval,
        latitude: location[0],
        longitude: location[1],
        social_work_days: (canAssignSocialWork && isSocialWork && socialWorkDays > 0) ? socialWorkDays : undefined,
        trophy_id: (isOrg && hasTrophy && selectedTrophyId) ? selectedTrophyId : undefined,
        attendance_mode: isOrg ? attendanceMode : 'manual',
        check_in_radius: (isOrg && attendanceMode === 'qr_code') ? checkInRadius : 300,
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

          {checkingConflict && (
            <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', marginTop: '-4px', marginBottom: '14px' }}>
              ⏳ Đang kiểm tra lịch của bạn...
            </div>
          )}

          {scheduleConflict && (
            <div
              style={{
                fontSize: '0.85rem',
                padding: '10px 14px',
                borderRadius: '8px',
                marginTop: '-4px',
                marginBottom: '14px',
                background: scheduleConflict.level === 'hard_conflict' ? 'rgba(239, 68, 68, 0.08)' : 'rgba(245, 158, 11, 0.08)',
                border: `1px solid ${scheduleConflict.level === 'hard_conflict' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
                color: scheduleConflict.level === 'hard_conflict' ? '#dc2626' : '#d97706',
                lineHeight: '1.4',
              }}
            >
              <strong>{scheduleConflict.level === 'hard_conflict' ? '⛔ Cảnh báo trùng lịch:' : '⚠️ Lưu ý lịch trình:'}</strong>{' '}
              {scheduleConflict.warning_message}
            </div>
          )}

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

          {(user?.role === 'edu_org' || user?.role === 'admin') && (
            <div className="form-group p-4 border border-emerald-500/30 bg-emerald-500/5 rounded-xl flex flex-col gap-2">
              <label className="flex items-center gap-2 cursor-pointer select-none font-semibold text-emerald-700 dark:text-emerald-400">
                <input
                  type="checkbox"
                  className="w-4 h-4 rounded accent-emerald-600 cursor-pointer"
                  checked={isSocialWork}
                  onChange={(e) => {
                    setIsSocialWork(e.target.checked);
                    if (e.target.checked && socialWorkDays <= 0) {
                      setSocialWorkDays(1);
                    }
                  }}
                />
                <span>Hoạt động cấp ngày Công tác Xã hội (CTXH)</span>
              </label>
              {isSocialWork && (
                <div className="flex items-center gap-3 pt-2">
                  <label htmlFor="social_work_days" className="text-sm font-medium text-[var(--color-text-primary)]">
                    Số ngày CTXH được cấp:
                  </label>
                  <input
                    type="number"
                    id="social_work_days"
                    step="0.5"
                    min="0.5"
                    max="30"
                    className="form-input !w-32 !border !border-gray-300 rounded-lg"
                    value={socialWorkDays}
                    onChange={(e) => setSocialWorkDays(parseFloat(e.target.value) || 0)}
                  />
                  <span className="text-sm text-[var(--color-text-secondary)]">ngày</span>
                </div>
              )}
            </div>
          )}

          {isOrg && (
            <div className="form-group p-4 border border-amber-500/30 bg-amber-500/5 rounded-xl flex flex-col gap-3">
              <label className="flex items-center gap-2 cursor-pointer select-none font-semibold text-amber-700 dark:text-amber-400">
                <input
                  type="checkbox"
                  className="w-4 h-4 rounded accent-amber-600 cursor-pointer"
                  checked={hasTrophy}
                  onChange={(e) => setHasTrophy(e.target.checked)}
                />
                <span>🏆 Hoạt động cấp Danh hiệu / Trophy vinh danh</span>
              </label>

              {hasTrophy && (
                <div className="flex flex-col gap-3 pl-6 pt-1 border-l-2 border-amber-400/40">
                  <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-[var(--color-text-primary)]">
                      Chọn Trophy trao tặng:
                    </label>
                    <div className="flex items-center gap-2">
                      <select
                        className="form-input flex-1 !border !border-gray-300 rounded-lg"
                        value={selectedTrophyId}
                        onChange={(e) => setSelectedTrophyId(e.target.value)}
                      >
                        {availableTrophies.map(t => (
                          <option key={t.id} value={t.id}>
                            {t.icon || '🏆'} {t.name} (+{t.points} điểm)
                          </option>
                        ))}
                      </select>
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        onClick={() => setShowCreateTrophyModal(true)}
                      >
                        + Tạo Trophy mới
                      </Button>
                    </div>
                  </div>

                  <div className="flex flex-col gap-2 pt-2 border-t border-amber-500/20">
                    <label className="text-sm font-medium text-[var(--color-text-primary)]">
                      Phương thức điểm danh nhận Trophy:
                    </label>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                      <label className={`p-3 rounded-lg border cursor-pointer text-sm transition-all ${attendanceMode === 'manual' ? 'border-indigo-600 bg-indigo-50/50 dark:bg-indigo-950/20 font-semibold' : 'border-gray-200 dark:border-gray-700'}`}>
                        <input
                          type="radio"
                          name="attendance_mode"
                          value="manual"
                          className="sr-only"
                          checked={attendanceMode === 'manual'}
                          onChange={() => setAttendanceMode('manual')}
                        />
                        <div>👤 Thủ công</div>
                        <div className="text-xs text-[var(--color-text-secondary)] mt-1 font-normal">Host tự tick duyệt trong danh sách</div>
                      </label>

                      <label className={`p-3 rounded-lg border cursor-pointer text-sm transition-all ${attendanceMode === 'auto' ? 'border-indigo-600 bg-indigo-50/50 dark:bg-indigo-950/20 font-semibold' : 'border-gray-200 dark:border-gray-700'}`}>
                        <input
                          type="radio"
                          name="attendance_mode"
                          value="auto"
                          className="sr-only"
                          checked={attendanceMode === 'auto'}
                          onChange={() => setAttendanceMode('auto')}
                        />
                        <div>🟢 Tự động</div>
                        <div className="text-xs text-[var(--color-text-secondary)] mt-1 font-normal">Tự động duyệt khi hết giờ sự kiện</div>
                      </label>

                      <label className={`p-3 rounded-lg border cursor-pointer text-sm transition-all ${attendanceMode === 'qr_code' ? 'border-indigo-600 bg-indigo-50/50 dark:bg-indigo-950/20 font-semibold' : 'border-gray-200 dark:border-gray-700'}`}>
                        <input
                          type="radio"
                          name="attendance_mode"
                          value="qr_code"
                          className="sr-only"
                          checked={attendanceMode === 'qr_code'}
                          onChange={() => setAttendanceMode('qr_code')}
                        />
                        <div>📱 Quét QR + GPS</div>
                        <div className="text-xs text-[var(--color-text-secondary)] mt-1 font-normal">QR động đổi 30s & kiểm tra vị trí GPS</div>
                      </label>
                    </div>
                  </div>

                  {attendanceMode === 'qr_code' && (
                    <div className="flex flex-col gap-1 p-3 bg-white/60 dark:bg-black/20 rounded-lg border border-indigo-200 dark:border-indigo-800">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium">Bán kính GPS cho phép check-in:</span>
                        <select
                          className="form-input !w-32 text-sm !py-1 !px-2 rounded"
                          value={checkInRadius}
                          onChange={(e) => setCheckInRadius(Number(e.target.value))}
                        >
                          <option value={100}>100 mét</option>
                          <option value={200}>200 mét</option>
                          <option value={300}>300 mét (Chuẩn)</option>
                          <option value={500}>500 mét</option>
                          <option value={1000}>1 km</option>
                        </select>
                      </div>
                      <span className="text-xs text-[var(--color-text-secondary)]">
                        🛡️ Người tham gia ở ngoài bán kính này sẽ bị từ chối điểm danh để chống gian lận ở nhà.
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="meeting_location">Điểm hẹn / Địa điểm tập trung</label>
            <input
              type="text"
              id="meeting_location"
              name="meeting_location"
              className="form-input"
              value={formData.meeting_location || formData.location_name}
              onChange={handleChange}
              placeholder="Ví dụ: Cổng 1 Lý Thường Kiệt, Hội trường A5, v.v."
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
                {customFormFields.map((field, index) => (
                  <div key={field.id} className="form-builder-row">
                    <div className="form-builder-row__field">
                      <label className="form-builder-label">Field name</label>
                      <input
                        type="text"
                        className="form-input !border !border-gray-300 rounded-lg focus:!border-indigo-600 focus:outline-none"
                        value={field.label}
                        placeholder="Enter field name..."
                        onChange={(e) => {
                          const newFields = [...customFormFields];
                          newFields[index].label = e.target.value;
                          setCustomFormFields(newFields);
                        }}
                      />
                    </div>
                    <div className="form-builder-row__type--wide">
                      <label className="form-builder-label">Type</label>
                      <select
                        className="form-input !border !border-gray-300 rounded-lg focus:!border-indigo-600 focus:outline-none"
                        value={field.field_type}
                        onChange={(e) => {
                          const newFields = [...customFormFields];
                          newFields[index].field_type = e.target.value;
                          setCustomFormFields(newFields);
                        }}
                      >
                        <option value="text">Text</option>
                        <option value="number">Number</option>
                        <option value="boolean">Checkbox</option>
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
                        /> Required
                      </label>
                    </div>
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => setCustomFormFields(customFormFields.filter((_, i) => i !== index))}
                    >
                      Remove
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

      {showCreateTrophyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-fade-in">
          <div className="glass bg-[var(--color-bg-surface)] p-6 rounded-2xl max-w-md w-full border border-white/20 shadow-2xl">
            <h3 className="text-xl font-bold text-[var(--color-text-primary)] mb-4">🏆 Tạo Trophy mới</h3>
            <form onSubmit={handleQuickCreateTrophy} className="flex flex-col gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Tên Trophy <span className="text-red-500">*</span></label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Ví dụ: Chiến binh Tình nguyện 2026"
                  value={newTrophy.name}
                  onChange={(e) => setNewTrophy({ ...newTrophy, name: e.target.value })}
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium mb-1">Biểu tượng (Icon/Emoji)</label>
                  <input
                    type="text"
                    className="form-input text-center text-xl"
                    value={newTrophy.icon}
                    onChange={(e) => setNewTrophy({ ...newTrophy, icon: e.target.value })}
                    maxLength={10}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Điểm thưởng</label>
                  <input
                    type="number"
                    className="form-input"
                    value={newTrophy.points}
                    onChange={(e) => setNewTrophy({ ...newTrophy, points: parseInt(e.target.value) || 0 })}
                    min={0}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Mô tả vinh danh</label>
                <textarea
                  className="form-input"
                  rows={2}
                  placeholder="Trao cho thành viên đã tham gia đầy đủ..."
                  value={newTrophy.description}
                  onChange={(e) => setNewTrophy({ ...newTrophy, description: e.target.value })}
                />
              </div>

              <div className="flex justify-end gap-2 mt-2">
                <Button type="button" variant="secondary" onClick={() => setShowCreateTrophyModal(false)}>
                  Hủy
                </Button>
                <Button type="submit" loading={creatingTrophy}>
                  Tạo & Sử dụng ngay
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
