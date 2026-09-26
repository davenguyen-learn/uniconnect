import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { activitiesApi, type ActivityCreate } from '../../api/activities';
import { calendarApi, type ConflictInfo } from '../../api/calendar';
import { trophiesApi } from '../../api/trophies';
import { useToast } from '../../components/Toast/ToastContext';
import { useAuth } from '../../contexts/AuthContext';
import { Lock, Trophy, Clock, AlertCircle, AlertTriangle, HeartHandshake, UserCheck } from 'lucide-react';
import Button from '../../components/Button/Button';
import LocationPicker from '../../components/Map/LocationPicker';
import './CreateActivity.css';

export default function CreateActivity() {
  const navigate = useNavigate();
  const toast = useToast();
  const { user } = useAuth();

  const isOrg = user?.role === 'edu_org' || user?.role === 'admin';

  const [loading, setLoading] = useState(false);
  const [isSocialWork, setIsSocialWork] = useState(false);
  const [socialWorkDays, setSocialWorkDays] = useState<string>('1');

  // Trophy & Attendance state for Organization hosts
  const [hasTrophy, setHasTrophy] = useState(false);
  const [trophyName, setTrophyName] = useState('');
  const [trophyIcon, setTrophyIcon] = useState('🏆');
  const [trophyDescription, setTrophyDescription] = useState('');
  const [attendanceMode, setAttendanceMode] = useState<'manual' | 'auto'>('manual');

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

  // Schedule conflict pre-validation state
  const [scheduleConflict, setScheduleConflict] = useState<ConflictInfo | null>(null);
  const [checkingConflict, setCheckingConflict] = useState(false);
  const [attemptedSubmit, setAttemptedSubmit] = useState(false);

  const isTitleMissing = attemptedSubmit && !formData.title.trim();
  const isDescriptionMissing = attemptedSubmit && !formData.description.trim();
  const isMeetingLocationMissing = attemptedSubmit && !(formData.meeting_location || formData.location_name || '').trim();
  const isMaxParticipantsMissing = attemptedSubmit && (!formData.max_participants || Number(formData.max_participants) < 2);
  const isStartTimeMissing = attemptedSubmit && !formData.start_time;
  const isEndTimeMissing = attemptedSubmit && !formData.end_time;
  const isLocationMissing = attemptedSubmit && !location;



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



  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAttemptedSubmit(true);

    if (
      !formData.title.trim() ||
      !formData.description.trim() ||
      !(formData.meeting_location || formData.location_name || '').trim() ||
      !formData.max_participants ||
      Number(formData.max_participants) < 2 ||
      !formData.start_time ||
      !formData.end_time
    ) {
      toast.error('Vui lòng điền đầy đủ các thông tin bắt buộc (*)');
      return;
    }

    if (!location) {
      toast.error('Vui lòng nhấp vào bản đồ để chọn vị trí diễn ra hoạt động');
      return;
    }

    const start = new Date(formData.start_time);
    const end = new Date(formData.end_time);

    if (end <= start) {
      toast.error('Thời gian kết thúc phải sau thời gian bắt đầu');
      return;
    }

    const now = new Date();
    if (start.getTime() < now.getTime() - 2 * 60 * 1000) {
      toast.error('Thời gian bắt đầu phải ở trong tương lai (sau thời điểm hiện tại)');
      return;
    }

    try {
      setLoading(true);
      const canAssignSocialWork = user?.role === 'edu_org' || user?.role === 'admin';
      const parsedSocialWork = parseFloat(socialWorkDays);

      let createdTrophyId: string | undefined = undefined;
      if (isOrg && hasTrophy) {
        if (!trophyName.trim()) {
          toast.error('Vui lòng nhập tên Danh hiệu / Trophy');
          setLoading(false);
          return;
        }
        if (trophyName.trim().length < 2) {
          toast.error('Tên Danh hiệu / Trophy phải có ít nhất 2 ký tự');
          setLoading(false);
          return;
        }
        try {
          const createdTrophy = await trophiesApi.create({
            name: trophyName.trim(),
            description: trophyDescription.trim() || undefined,
            icon: trophyIcon.trim() || '🏆',
          });
          createdTrophyId = createdTrophy.id;
        } catch (err: any) {
          const detail = err.response?.data?.detail || 'Không thể tạo Danh hiệu / Trophy';
          toast.error(detail);
          setLoading(false);
          return;
        }
      }

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
        social_work_days: (canAssignSocialWork && isSocialWork && !isNaN(parsedSocialWork) && parsedSocialWork > 0) ? parsedSocialWork : undefined,
        trophy_id: createdTrophyId,
        attendance_mode: attendanceMode,
      };

      const filledCustomFields = customFormFields.filter(f => f.label.trim().length > 0);
      if (customFormFields.length > 0 && filledCustomFields.length < customFormFields.length) {
        toast.error('Vui lòng nhập nội dung câu hỏi hoặc nhấn nút "Xóa" câu hỏi còn trống');
        return;
      }

      if (filledCustomFields.length > 0) {
        data.custom_form = {
          title: "Join Application Form",
          description: "Please fill out this form to join.",
          fields: filledCustomFields.map((f, idx) => ({
            label: f.label.trim(),
            field_type: (f.field_type === 'boolean' ? 'checkbox' : f.field_type) as any,
            is_required: f.is_required,
            order: idx
          }))
        };
      }

      const newActivity = await activitiesApi.create(data);
      toast.success('Đã tạo hoạt động thành công!');
      navigate(`/activities/${newActivity.id}`);
    } catch (error: any) {
      const errData = error.response?.data?.error;
      if (errData?.details?.fields && errData.details.fields.length > 0) {
        const detailMsg = errData.details.fields.map((f: any) => `${f.field}: ${f.message}`).join(', ');
        toast.error(`Lỗi dữ liệu: ${detailMsg}`);
      } else if (errData?.message) {
        toast.error(errData.message);
      } else if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Không thể tạo hoạt động');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="create-activity-page">
      <div className="create-activity-container">
        <form noValidate onSubmit={handleSubmit} className="create-activity-form">
          <div className="title-input-wrapper">
            <input
              type="text"
              id="title"
              name="title"
              className={`activity-hero-title-input ${isTitleMissing ? 'input-error' : ''}`}
              value={formData.title}
              onChange={handleChange}
              required
              placeholder="Nhập tiêu đề hoạt động..."
              maxLength={100}
            />
            {isTitleMissing && <span className="field-error-msg">Vui lòng nhập tiêu đề hoạt động</span>}
          </div>

          <div className="form-group">
            <label htmlFor="description">Mô tả <span className="required">*</span></label>
            <textarea
              id="description"
              name="description"
              className={`form-input ${isDescriptionMissing ? 'input-error' : ''}`}
              value={formData.description}
              onChange={handleChange}
              required
              placeholder="Cho mọi người biết sự kiện này về điều gì..."
              rows={4}
            />
            {isDescriptionMissing && <span className="field-error-msg">Vui lòng nhập mô tả hoạt động</span>}
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
                <option value="Ăn uống" />
                <option value="Cà phê" />
                <option value="Học tập" />
                <option value="Workshop" />
                <option value="Thể thao" />
                <option value="Vận động" />
                <option value="Tình nguyện" />
                <option value="CTXH" />
                <option value="Nhóm" />
                <option value="Đội nhóm" />
                <option value="Hướng nghiệp" />
                <option value="Việc làm" />
                <option value="Xem phim" />
                <option value="Giải trí" />
                <option value="Âm nhạc" />
                <option value="Nghệ thuật" />
                <option value="Boardgame" />
                <option value="Game" />
                <option value="Esports" />
                <option value="Dã ngoại" />
                <option value="Phượt" />
                <option value="Giao lưu kết bạn" />
              </datalist>
            </div>

            <div className="form-group">
              <label htmlFor="max_participants">Số người tham gia tối đa <span className="required">*</span></label>
              <input
                type="number"
                id="max_participants"
                name="max_participants"
                className={`form-input ${isMaxParticipantsMissing ? 'input-error' : ''}`}
                value={formData.max_participants}
                onChange={handleChange}
                required
                min={2}
                max={1000}
              />
              {isMaxParticipantsMissing && <span className="field-error-msg">Số người tham gia tối thiểu là 2</span>}
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="start_time">Thời gian bắt đầu <span className="required">*</span></label>
              <input
                type="datetime-local"
                id="start_time"
                name="start_time"
                className={`form-input ${isStartTimeMissing ? 'input-error' : ''}`}
                value={formData.start_time}
                onChange={handleChange}
                required
              />
              {isStartTimeMissing && <span className="field-error-msg">Vui lòng chọn thời gian bắt đầu</span>}
            </div>

            <div className="form-group">
              <label htmlFor="end_time">Thời gian kết thúc <span className="required">*</span></label>
              <input
                type="datetime-local"
                id="end_time"
                name="end_time"
                className={`form-input ${isEndTimeMissing ? 'input-error' : ''}`}
                value={formData.end_time}
                onChange={handleChange}
                required
              />
              {isEndTimeMissing && <span className="field-error-msg">Vui lòng chọn thời gian kết thúc</span>}
            </div>
          </div>

          {checkingConflict && (
            <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', marginTop: '-4px', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Clock size={13} className="animate-spin text-indigo-500" />
              <span>Đang kiểm tra lịch của bạn...</span>
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
                display: 'flex',
                alignItems: 'flex-start',
                gap: '8px',
              }}
            >
              {scheduleConflict.level === 'hard_conflict' ? (
                <AlertCircle size={16} className="shrink-0 mt-0.5" />
              ) : (
                <AlertTriangle size={16} className="shrink-0 mt-0.5" />
              )}
              <div>
                <strong>{scheduleConflict.level === 'hard_conflict' ? 'Cảnh báo trùng lịch:' : 'Lưu ý lịch trình:'}</strong>{' '}
                {scheduleConflict.warning_message}
              </div>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="meeting_location">
              Địa điểm <span className="required">*</span>
            </label>
            <input
              type="text"
              id="meeting_location"
              name="meeting_location"
              className={`form-input ${isMeetingLocationMissing ? 'input-error' : ''}`}
              value={formData.meeting_location || formData.location_name}
              onChange={handleChange}
              placeholder="Ví dụ: Cổng 1 Lý Thường Kiệt, Hội trường A5, Quán cafe..."
              maxLength={100}
              required
            />
            {isMeetingLocationMissing && (
              <span className="field-error-msg">Vui lòng nhập địa điểm hoạt động</span>
            )}
          </div>

          <div className="form-group map-group">
            <label>Vị trí trên bản đồ <span className="required">*</span></label>
            <div className={isLocationMissing ? 'map-error-wrapper' : ''}>
              <LocationPicker
                position={location}
                onChange={(lat, lng) => setLocation([lat, lng])}
              />
            </div>
            {isLocationMissing ? (
              <span className="field-error-msg italic mt-1 block" style={{ fontStyle: 'italic' }}>Vui lòng nhấp vào bản đồ để chọn vị trí.</span>
            ) : !location ? (
              <span className="error-text italic mt-1 text-sm block" style={{ fontStyle: 'italic' }}>Vui lòng nhấp vào bản đồ để chọn vị trí.</span>
            ) : null}
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
              <option value="public">Công khai</option>
              <option value="private">Riêng tư</option>
            </select>
          </div>

          {formData.privacy === 'private' && (
            <div className="form-group private-field-callout">
              <label htmlFor="private_description" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span>Mô tả riêng tư (Chỉ dành cho thành viên)</span>
                <Lock size={13} className="text-gray-400" />
              </label>
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

          <div
            className={`approval-toggle-card ${formData.require_approval ? 'active' : ''}`}
            onClick={() => setFormData(prev => ({ ...prev, require_approval: !prev.require_approval }))}
          >
            <div className="approval-toggle-content">
              <div className="approval-toggle-icon">
                <UserCheck size={18} />
              </div>
              <div className="approval-toggle-info">
                <span className="approval-toggle-title">Yêu cầu phê duyệt để tham gia</span>
                <span className="approval-toggle-desc">Chỉ những thành viên được bạn xét duyệt mới có thể tham gia hoạt động</span>
              </div>
            </div>
            <div className={`approval-switch ${formData.require_approval ? 'on' : ''}`}>
              <span className="approval-switch-handle" />
            </div>
          </div>

          {/* Tự động điểm danh khi kết thúc hoạt động */}
          <div
            className={`approval-toggle-card approval-toggle-card--indigo ${attendanceMode === 'auto' ? 'active' : ''}`}
            onClick={() => setAttendanceMode(attendanceMode === 'auto' ? 'manual' : 'auto')}
          >
            <div className="approval-toggle-content">
              <div className="approval-toggle-icon">
                <Clock size={18} />
              </div>
              <div className="approval-toggle-info">
                <span className="approval-toggle-title">Tự động điểm danh người tham gia khi kết thúc hoạt động</span>
                <span className="approval-toggle-desc">Tự động xác nhận có mặt cho tất cả người tham gia hợp lệ khi hết giờ sự kiện</span>
              </div>
            </div>
            <div className={`approval-switch ${attendanceMode === 'auto' ? 'on' : ''}`}>
              <span className="approval-switch-handle" />
            </div>
          </div>

          {(user?.role === 'edu_org' || user?.role === 'admin') && (
            <div className="flex flex-col gap-3">
              <div
                className={`approval-toggle-card approval-toggle-card--emerald ${isSocialWork ? 'active' : ''}`}
                onClick={() => {
                  const nextState = !isSocialWork;
                  setIsSocialWork(nextState);
                  if (nextState && (!socialWorkDays || isNaN(parseFloat(socialWorkDays)) || parseFloat(socialWorkDays) <= 0)) {
                    setSocialWorkDays('1');
                  }
                }}
              >
                <div className="approval-toggle-content">
                  <div className="approval-toggle-icon">
                    <HeartHandshake size={18} />
                  </div>
                  <div className="approval-toggle-info">
                    <span className="approval-toggle-title">Hoạt động cấp ngày Công tác xã hội</span>
                    <span className="approval-toggle-desc">Ghi nhận số ngày CTXH cho sinh viên sau khi hoàn thành điểm danh</span>
                  </div>
                </div>
                <div className={`approval-switch ${isSocialWork ? 'on' : ''}`}>
                  <span className="approval-switch-handle" />
                </div>
              </div>

              {isSocialWork && (
                <div className="flex items-center gap-3 p-4 bg-emerald-500/5 border border-emerald-500/20 rounded-xl">
                  <label htmlFor="social_work_days" className="text-sm font-medium text-[var(--color-text-primary)]">
                    Số ngày CTXH được cấp:
                  </label>
                  <input
                    type="number"
                    id="social_work_days"
                    step="0.5"
                    min="0.5"
                    max="30"
                    placeholder="1"
                    className="form-input !w-32 rounded-lg"
                    value={socialWorkDays}
                    onChange={(e) => setSocialWorkDays(e.target.value)}
                    onBlur={() => {
                      if (!socialWorkDays || isNaN(parseFloat(socialWorkDays)) || parseFloat(socialWorkDays) <= 0) {
                        setSocialWorkDays('1');
                      }
                    }}
                  />
                  <span className="text-sm text-[var(--color-text-secondary)]">ngày</span>
                </div>
              )}
            </div>
          )}

          {isOrg && (
            <div className="flex flex-col gap-3">
              <div
                className={`approval-toggle-card approval-toggle-card--amber ${hasTrophy ? 'active' : ''}`}
                onClick={() => setHasTrophy(!hasTrophy)}
              >
                <div className="approval-toggle-content">
                  <div className="approval-toggle-icon">
                    <Trophy size={18} />
                  </div>
                  <div className="approval-toggle-info">
                    <span className="approval-toggle-title">Hoạt động cấp danh hiệu</span>
                    <span className="approval-toggle-desc">Tặng danh hiệu thành tích cho người tham gia hoàn thành</span>
                  </div>
                </div>
                <div className={`approval-switch ${hasTrophy ? 'on' : ''}`}>
                  <span className="approval-switch-handle" />
                </div>
              </div>

              {hasTrophy && (
                <div className="flex flex-col gap-3 p-4 border border-amber-500/20 bg-amber-500/5 rounded-xl">
                  <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                    <div className="sm:col-span-3 flex flex-col gap-1">
                      <label className="text-sm font-medium text-[var(--color-text-primary)]">
                        Tên Danh hiệu / Trophy <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        className="form-input rounded-lg"
                        placeholder="VD: Chiến sĩ tình nguyện xuất sắc, Top 1 Cuộc thi..."
                        value={trophyName}
                        onChange={(e) => setTrophyName(e.target.value)}
                        maxLength={100}
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-sm font-medium text-[var(--color-text-primary)]">
                        Biểu tượng
                      </label>
                      <input
                        type="text"
                        className="form-input rounded-lg text-center text-lg"
                        value={trophyIcon}
                        onChange={(e) => setTrophyIcon(e.target.value)}
                        placeholder="🏆"
                        maxLength={10}
                      />
                    </div>
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-[var(--color-text-primary)]">
                      Mô tả vinh danh <span className="text-xs text-[var(--color-text-secondary)] font-normal">(tùy chọn)</span>
                    </label>
                    <input
                      type="text"
                      className="form-input rounded-lg"
                      placeholder="Trao cho thành viên đã tham gia đầy đủ và tích cực..."
                      value={trophyDescription}
                      onChange={(e) => setTrophyDescription(e.target.value)}
                      maxLength={200}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="form-group">
            <div className="flex items-center justify-between mb-2">
              <div>
                <label className="font-semibold text-[var(--color-text-primary)] block">Biểu mẫu tham gia tùy chỉnh</label>
              </div>
              <Button
                type="button"
                size="sm"
                variant="secondary"
                onClick={() => setCustomFormFields([...customFormFields, { id: Math.random().toString(), label: '', field_type: 'text', is_required: true }])}
              >
                + Thêm câu hỏi
              </Button>
            </div>

            <div className="form-builder-container">
              {customFormFields.length === 0 ? (
                <div className="p-4 text-center text-sm text-[var(--color-text-secondary)]">
                  Chưa có câu hỏi nào. Nhấp <strong>"+ Thêm câu hỏi"</strong> ở trên nếu cần thu thập thêm thông tin từ người tham gia.
                </div>
              ) : (
                <>
                  {customFormFields.map((field, index) => (
                    <div key={field.id} className="form-builder-row">
                      <div className="form-builder-row__field">
                        <label className="form-builder-label">Câu hỏi</label>
                        <input
                          type="text"
                          className="form-input rounded-lg"
                          value={field.label}
                          placeholder="Ví dụ: MSSV, Khoa, Số điện thoại..."
                          onChange={(e) => {
                            const newFields = [...customFormFields];
                            newFields[index].label = e.target.value;
                            setCustomFormFields(newFields);
                          }}
                        />
                      </div>
                      <div className="form-builder-row__type--wide">
                        <label className="form-builder-label">Loại dữ liệu</label>
                        <select
                          className="form-input rounded-lg"
                          value={field.field_type === 'boolean' ? 'checkbox' : field.field_type}
                          onChange={(e) => {
                            const newFields = [...customFormFields];
                            newFields[index].field_type = e.target.value;
                            setCustomFormFields(newFields);
                          }}
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
                            onChange={(e) => {
                              const newFields = [...customFormFields];
                              newFields[index].is_required = e.target.checked;
                              setCustomFormFields(newFields);
                            }}
                          />
                          <div className={`form-builder-switch ${field.is_required ? 'on' : ''}`}>
                            <span className="form-builder-switch-handle" />
                          </div>
                          <span className="form-builder-switch-text">Bắt buộc</span>
                        </label>
                      </div>
                      <Button
                        type="button"
                        variant="secondary"
                        onClick={() => setCustomFormFields(customFormFields.filter((_, i) => i !== index))}
                      >
                        Xóa
                      </Button>
                    </div>
                  ))}
                </>
              )}
            </div>
          </div>

          <div className="form-actions">
            <Button type="button" variant="secondary" onClick={() => navigate(-1)}>
              Hủy
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Đang tạo...' : 'Tạo hoạt động'}
            </Button>
          </div>
        </form>
      </div>

    </div>
  );
}
