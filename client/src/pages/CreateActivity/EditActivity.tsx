import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { activitiesApi, type ActivityUpdate } from '../../api/activities';
import { calendarApi, type ReschedulePreviewResponse } from '../../api/calendar';
import { trophiesApi, type TrophyResponse } from '../../api/trophies';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../components/Toast/ToastContext';
import { Trophy, UserCheck, Clock, QrCode, ShieldCheck, AlertTriangle, CheckCircle2, BarChart2 } from 'lucide-react';
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
  const { user } = useAuth();
  const isOrg = user?.role === 'edu_org' || user?.role === 'admin';
  
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  
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
  const [customFormFields, setCustomFormFields] = useState<Array<{ id: string; label: string; field_type: string; is_required: boolean }>>([]);

  const [attemptedSubmit, setAttemptedSubmit] = useState(false);

  const isTitleMissing = attemptedSubmit && !formData.title.trim();
  const isDescriptionMissing = attemptedSubmit && !formData.description.trim();
  const isMeetingLocationMissing = attemptedSubmit && !(formData.meeting_location || formData.location_name || '').trim();
  const isMaxParticipantsMissing = attemptedSubmit && (!formData.max_participants || Number(formData.max_participants) < 2);
  const isStartTimeMissing = attemptedSubmit && !formData.start_time;
  const isEndTimeMissing = attemptedSubmit && !formData.end_time;
  const isLocationMissing = attemptedSubmit && !location;

  useEffect(() => {
    if (isOrg) {
      trophiesApi.list().then(res => setAvailableTrophies(res)).catch(() => {});
    }
  }, [isOrg]);

  useEffect(() => {
    if (id) {
      activitiesApi.getById(id)
        .then(act => {
          setFormData({
            title: act.title,
            description: act.description || '',
            category: act.category || '',
            meeting_location: act.meeting_location || act.location_name || '',
            location_name: act.meeting_location || act.location_name || '',
            start_time: formatForInput(act.start_time),
            end_time: formatForInput(act.end_time),
            max_participants: act.max_participants,
            privacy: act.privacy as 'public' | 'private',
            require_approval: act.require_approval ?? true,
          });
          if (act.custom_form?.fields) {
            const sorted = [...act.custom_form.fields].sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
            setCustomFormFields(
              sorted.map((f) => ({
                id: f.id || Math.random().toString(),
                label: f.label,
                field_type: f.field_type === 'boolean' ? 'checkbox' : f.field_type,
                is_required: f.is_required,
              }))
            );
          }
          if (act.trophy) {
            setHasTrophy(true);
            setSelectedTrophyId(act.trophy.id);
          }
          if (act.attendance_mode) {
            setAttendanceMode(act.attendance_mode);
          }
          if (act.check_in_radius) {
            setCheckInRadius(act.check_in_radius);
          }
          setLocation([act.latitude, act.longitude]);
          setInitialLoading(false);
        })
        .catch(() => {
          toast.error('Failed to load activity');
          navigate('/dashboard');
        });
    }
  }, [id]);

  const [reschedulePreview, setReschedulePreview] = useState<ReschedulePreviewResponse | null>(null);

  useEffect(() => {
    if (id && !initialLoading && formData.start_time && formData.end_time) {
      const s = new Date(formData.start_time);
      const e = new Date(formData.end_time);
      if (e > s) {
        calendarApi
          .previewReschedule(id, {
            new_start_time: s.toISOString(),
            new_end_time: e.toISOString(),
          })
          .then((res) => {
            if (res.total_participants > 0) {
              setReschedulePreview(res);
            } else {
              setReschedulePreview(null);
            }
          })
          .catch(() => setReschedulePreview(null));
      } else {
        setReschedulePreview(null);
      }
    }
  }, [id, initialLoading, formData.start_time, formData.end_time]);

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
    if (!id) return;
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

    try {
      setLoading(true);
      const data: ActivityUpdate = {
        title: formData.title,
        description: formData.description,
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
      };

      if (isOrg) {
        data.trophy_id = (hasTrophy && selectedTrophyId) ? selectedTrophyId : null;
      }
      data.attendance_mode = attendanceMode;
      data.check_in_radius = attendanceMode === 'qr_code' ? checkInRadius : 300;

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
            order: idx,
          })),
        };
      } else {
        data.custom_form = null;
      }

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
      <div className="create-activity-container">
        <h1 className="create-activity-title">Chỉnh sửa hoạt động</h1>
        <p className="create-activity-subtitle">Cập nhật thông tin chi tiết về sự kiện của bạn.</p>

        <form noValidate onSubmit={handleSubmit} className="create-activity-form">
          <div className="form-group">
            <label htmlFor="title">Tiêu đề <span className="required">*</span></label>
            <input
              type="text"
              id="title"
              name="title"
              className={`form-input ${isTitleMissing ? 'input-error' : ''}`}
              value={formData.title}
              onChange={handleChange}
              required
              placeholder="Ví dụ: Cùng nhau học tập tại KTX"
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

          {reschedulePreview && (
            <div
              style={{
                fontSize: '0.85rem',
                padding: '12px 14px',
                borderRadius: '10px',
                marginTop: '-6px',
                marginBottom: '16px',
                background: reschedulePreview.safe_to_reschedule ? 'rgba(34, 197, 94, 0.08)' : 'rgba(245, 158, 11, 0.08)',
                border: `1px solid ${reschedulePreview.safe_to_reschedule ? 'rgba(34, 197, 94, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
              }}
            >
              <div style={{ fontWeight: 600, marginBottom: '4px', color: reschedulePreview.safe_to_reschedule ? '#16a34a' : '#d97706', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <BarChart2 size={16} />
                <span>Tình trạng lịch của thành viên ({reschedulePreview.total_participants} người đã duyệt):</span>
              </div>
              <div style={{ color: 'var(--color-text-secondary)', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                {reschedulePreview.safe_to_reschedule ? (
                  <>
                    <CheckCircle2 size={15} className="text-green-600 shrink-0" />
                    <span>Tuyệt vời! Tất cả thành viên đều rảnh trong khung giờ mới này.</span>
                  </>
                ) : (
                  <>
                    <AlertTriangle size={15} className="text-amber-600 shrink-0" />
                    <span>Có {reschedulePreview.conflicted_count}/{reschedulePreview.total_participants} thành viên sẽ bị trùng lịch ({reschedulePreview.free_percentage}% rảnh).</span>
                  </>
                )}
              </div>
              {reschedulePreview.conflicted_members.length > 0 && (
                <ul style={{ paddingLeft: '20px', margin: '4px 0 0', fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                  {reschedulePreview.conflicted_members.slice(0, 5).map((m, i) => (
                    <li key={i}>
                      <strong>{m.full_name}</strong>: {m.reason}
                    </li>
                  ))}
                  {reschedulePreview.conflicted_members.length > 5 && (
                    <li>...và {reschedulePreview.conflicted_members.length - 5} thành viên khác</li>
                  )}
                </ul>
              )}
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

          {/* Phương thức điểm danh (Áp dụng cho mọi hoạt động) */}
          <div className="form-group flex flex-col gap-2">
            <label className="font-semibold text-[var(--color-text-primary)] block">
              Phương thức điểm danh người tham gia
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              <label className={`p-3.5 rounded-xl border cursor-pointer text-sm transition-all ${attendanceMode === 'manual' ? 'border-primary-500 bg-primary-500/5 shadow-sm font-semibold' : 'border-[var(--color-border-subtle)] bg-[var(--color-bg-primary)] hover:border-gray-300'}`}>
                <input
                  type="radio"
                  name="attendance_mode"
                  value="manual"
                  className="sr-only"
                  checked={attendanceMode === 'manual'}
                  onChange={() => setAttendanceMode('manual')}
                />
                <div className="flex items-center gap-2 text-[var(--color-text-primary)]">
                  <UserCheck size={16} className={attendanceMode === 'manual' ? 'text-primary-600' : 'text-gray-400'} />
                  <span>Thủ công</span>
                </div>
                <div className="text-xs text-[var(--color-text-secondary)] mt-1.5 font-normal">Host tự tick duyệt trong danh sách người tham gia</div>
              </label>

              <label className={`p-3.5 rounded-xl border cursor-pointer text-sm transition-all ${attendanceMode === 'auto' ? 'border-primary-500 bg-primary-500/5 shadow-sm font-semibold' : 'border-[var(--color-border-subtle)] bg-[var(--color-bg-primary)] hover:border-gray-300'}`}>
                <input
                  type="radio"
                  name="attendance_mode"
                  value="auto"
                  className="sr-only"
                  checked={attendanceMode === 'auto'}
                  onChange={() => setAttendanceMode('auto')}
                />
                <div className="flex items-center gap-2 text-[var(--color-text-primary)]">
                  <Clock size={16} className={attendanceMode === 'auto' ? 'text-primary-600' : 'text-gray-400'} />
                  <span>Tự động</span>
                </div>
                <div className="text-xs text-[var(--color-text-secondary)] mt-1.5 font-normal">Tự động xác nhận có mặt khi hết giờ sự kiện</div>
              </label>

              <label className={`p-3.5 rounded-xl border cursor-pointer text-sm transition-all ${attendanceMode === 'qr_code' ? 'border-primary-500 bg-primary-500/5 shadow-sm font-semibold' : 'border-[var(--color-border-subtle)] bg-[var(--color-bg-primary)] hover:border-gray-300'}`}>
                <input
                  type="radio"
                  name="attendance_mode"
                  value="qr_code"
                  className="sr-only"
                  checked={attendanceMode === 'qr_code'}
                  onChange={() => setAttendanceMode('qr_code')}
                />
                <div className="flex items-center gap-2 text-[var(--color-text-primary)]">
                  <QrCode size={16} className={attendanceMode === 'qr_code' ? 'text-primary-600' : 'text-gray-400'} />
                  <span>Quét QR + GPS</span>
                </div>
                <div className="text-xs text-[var(--color-text-secondary)] mt-1.5 font-normal">QR động đổi 30s & kiểm tra vị trí GPS tại sự kiện</div>
              </label>
            </div>

            {attendanceMode === 'qr_code' && (
              <div className="flex flex-col gap-1 p-3.5 bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-subtle)] mt-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-[var(--color-text-primary)]">Bán kính GPS cho phép check-in:</span>
                  <select
                    className="form-input !w-36 text-sm !py-1 !px-2 rounded-lg"
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
                <span className="text-xs text-[var(--color-text-secondary)] flex items-center gap-1.5 mt-0.5">
                  <ShieldCheck size={14} className="text-primary-600 shrink-0" />
                  <span>Người tham gia ở ngoài bán kính này sẽ bị từ chối điểm danh để chống gian lận ở nhà.</span>
                </span>
              </div>
            )}
          </div>

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
                    <span className="approval-toggle-title">Hoạt động cấp Danh hiệu / Trophy vinh danh</span>
                    <span className="approval-toggle-desc">Tặng huy hiệu và điểm thưởng thành tích cho người tham gia hoàn thành</span>
                  </div>
                </div>
                <div className={`approval-switch ${hasTrophy ? 'on' : ''}`}>
                  <span className="approval-switch-handle" />
                </div>
              </div>

              {hasTrophy && (
                <div className="flex flex-col gap-3 p-4 border border-amber-500/20 bg-amber-500/5 rounded-xl">
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
                            {t.name} (+{t.points} điểm)
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

            {formData.require_approval && (
              <div className="mb-3 p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl text-xs text-amber-600 flex items-start gap-2">
                <AlertTriangle size={16} className="shrink-0 mt-0.5" />
                <span>
                  <strong>Lưu ý:</strong> Đối với hoạt động cần phê duyệt, nếu lưu biểu mẫu có trường <strong>bắt buộc</strong> (*), hệ thống sẽ tự động hủy phê duyệt của các thành viên đã đăng ký trước đó và gửi thông báo yêu cầu họ điền lại biểu mẫu để nộp lại yêu cầu tham gia.
                </span>
              </div>
            )}

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
              {loading ? 'Đang lưu...' : 'Lưu thay đổi'}
            </Button>
          </div>
        </form>
      </div>

      {showCreateTrophyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-fade-in">
          <div className="glass bg-[var(--color-bg-surface)] p-6 rounded-2xl max-w-md w-full border border-white/20 shadow-2xl">
            <h3 className="text-xl font-bold text-[var(--color-text-primary)] mb-4 flex items-center gap-2">
              <Trophy size={20} className="text-amber-500" />
              <span>Tạo Trophy mới</span>
            </h3>
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
