import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Calendar as CalendarIcon,
  MapPin,
  GraduationCap,
  Trophy,
  Lock,
  Unlock,
  CheckCircle2,
  AlertTriangle,
  FileText,
  QrCode,
  Sparkles,
  Users,
} from 'lucide-react';
import { activitiesApi, type ActivityResponse } from '../../api/activities';
import { participationApi, type JoinRequestResponse, type JoinRequestCreate } from '../../api/participation';
import { calendarApi, type ConflictInfo } from '../../api/calendar';
import { interactionsApi, type CommentResponse } from '../../api/interactions';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../components/Toast/ToastContext';
import Button from '../../components/Button/Button';
import LikeButton from '../../components/LikeButton/LikeButton';
import CommentSection from '../../components/CommentSection/CommentSection';
import { ReportModal } from '../../components/ReportModal/ReportModal';
import { CertificateModal } from '../../components/CertificateModal/CertificateModal';
import { DynamicFormRenderer } from '../../components/DynamicForm/DynamicFormRenderer';
import { ConflictModal } from '../../components/ConflictModal/ConflictModal';
import { CheckInModal } from '../../components/CheckInModal/CheckInModal';
import {
  mapActivityToDetailViewModel,
  validateDynamicForm,
} from '../../types/activity-detail-mapper';
import './ActivityDetail.css';

export default function ActivityDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const toast = useToast();

  const [activity, setActivity] = useState<ActivityResponse | null>(null);
  const [requests, setRequests] = useState<JoinRequestResponse[]>([]);
  const [participants, setParticipants] = useState<JoinRequestResponse[]>([]);
  const [myRequest, setMyRequest] = useState<JoinRequestResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [requestMessage, setRequestMessage] = useState('');
  const [formResponses, setFormResponses] = useState<Record<string, any>>({});
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [conflictInfo, setConflictInfo] = useState<ConflictInfo | null>(null);

  // Registration & Conflict State Machine
  const [isSubmittingRegistration, setIsSubmittingRegistration] = useState(false);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [showConflictModal, setShowConflictModal] = useState(false);
  const [conflictModalData, setConflictModalData] = useState<{ message: string; isSwap: boolean } | null>(null);

  // Interactions state
  const [liked, setLiked] = useState(false);
  const [likeCount, setLikeCount] = useState(0);
  const [comments, setComments] = useState<CommentResponse[]>([]);
  const [commentTotal, setCommentTotal] = useState(0);
  const [commentHasMore, setCommentHasMore] = useState(false);
  const [commentOffset, setCommentOffset] = useState(0);
  const COMMENT_LIMIT = 20;

  // Attendance & Dynamic QR Code state
  const [showHostQrModal, setShowHostQrModal] = useState(false);
  const [hostQrData, setHostQrData] = useState<{
    check_in_code: string;
    rotating_token: string;
    expires_in_seconds: number;
    check_in_radius: number;
  } | null>(null);
  const [qrCountdown, setQrCountdown] = useState(30);

  const [showCheckInModal, setShowCheckInModal] = useState(false);
  const [updatingAttendanceUserId, setUpdatingAttendanceUserId] = useState<string | null>(null);

  // Certificate Modal state
  const [showCertificateModal, setShowCertificateModal] = useState(false);
  const [certificateTargetUserId, setCertificateTargetUserId] = useState<string | undefined>(undefined);

  useEffect(() => {
    if (id === 'create' || id === 'new') {
      navigate('/activities/create', { replace: true });
      return;
    }
    if (id) {
      loadData();
    }
  }, [id, navigate]);

  useEffect(() => {
    let timer: any;
    if (showHostQrModal && id) {
      activitiesApi.getCheckInCode(id)
        .then(data => {
          setHostQrData(data);
          setQrCountdown(data.expires_in_seconds || 30);
        })
        .catch(() => toast.error('Không thể lấy mã QR'));

      timer = setInterval(() => {
        setQrCountdown(prev => {
          if (prev <= 1) {
            activitiesApi.getCheckInCode(id)
              .then(data => {
                setHostQrData(data);
                return data.expires_in_seconds || 30;
              })
              .catch(() => 30);
            return 30;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [showHostQrModal, id]);

  async function loadData() {
    try {
      setLoading(true);
      const act = await activitiesApi.getById(id!);
      setActivity(act);

      // Check if user is host
      const isHost = user?.id === act.host_id;

      if (isHost) {
        // Fetch all pending requests for this activity
        const reqs = await participationApi.listByActivity(id!);
        // filter pending locally if API doesn't filter
        setRequests(reqs.filter(r => r.status === 'pending'));
      } else {
        // If not host, fetch my own request status
        const myReqs = await participationApi.listByActivity(id!);
        if (myReqs.length > 0) {
          setMyRequest(myReqs[0]);
        }

        // Check schedule conflict
        if (user) {
          calendarApi
            .checkConflict({
              start_time: act.start_time,
              end_time: act.end_time,
              exclude_activity_id: act.id,
            })
            .then((res) => setConflictInfo(res.has_conflict ? res : null))
            .catch(() => setConflictInfo(null));
        }
      }

      // Fetch participants list for everyone
      try {
        const parts = await participationApi.listParticipants(id!);
        setParticipants(parts);
      } catch {
        // Non-critical: participants list failed to load
      }

      // Fetch interactions (like status, comments)
      try {
        const [likeStatus, commentsData] = await Promise.all([
          interactionsApi.getLikeStatus('activities', id!),
          interactionsApi.listComments('activities', id!, { limit: COMMENT_LIMIT, offset: 0 }),
        ]);
        setLiked(likeStatus.liked);
        setLikeCount(likeStatus.total_likes);
        setComments(commentsData.items);
        setCommentTotal(commentsData.total);
        setCommentHasMore(commentsData.has_more);
        setCommentOffset(0);
      } catch {
        // Non-critical: interactions data failed to load
      }
    } catch (error) {
      toast.error('Không thể tải chi tiết hoạt động');
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  }

  const executeJoin = async (confirmSwap = false) => {
    if (!id || !activity) return;

    // Validate dynamic form if custom_form exists
    if (activity.custom_form && activity.custom_form.fields.length > 0) {
      const parsedFields = (activity.custom_form.fields || []).map((f, idx) => ({
        id: f.id || `field_${idx}`,
        label: f.label,
        fieldType: (f.field_type as any) || 'text',
        isRequired: !!f.is_required,
        order: f.order ?? idx,
      }));
      const { isValid, errors } = validateDynamicForm(parsedFields, formResponses);
      if (!isValid) {
        setFormErrors(errors);
        toast.error('Vui lòng hoàn thành các trường bắt buộc trong biểu mẫu');
        return;
      }
      setFormErrors({});
    }

    try {
      setIsSubmittingRegistration(true);
      const data: JoinRequestCreate = {};
      if (requestMessage.trim()) {
        data.message = requestMessage.trim();
      }
      if (Object.keys(formResponses).length > 0) {
        data.form_responses = formResponses;
      }
      const req = await participationApi.requestToJoin(id, data, confirmSwap);
      setMyRequest(req);
      setShowConflictModal(false);
      if (activity?.require_approval) {
        toast.success('Đã gửi yêu cầu tham gia thành công!');
      } else {
        toast.success('Đã tham gia hoạt động thành công!');
        loadData();
      }
    } catch (error: any) {
      const msg = error.message || error.response?.data?.detail || '';
      if (msg.includes('confirm_swap=true')) {
        setConflictModalData({
          message: msg.replace('?confirm_swap=true', ''),
          isSwap: true,
        });
        setShowConflictModal(true);
      } else {
        toast.error(msg || 'Không thể gửi yêu cầu. Hoạt động có thể đã đầy.');
        loadData();
      }
    } finally {
      setIsSubmittingRegistration(false);
    }
  };

  const handleJoinRequest = (e: React.FormEvent) => {
    e.preventDefault();
    if (conflictInfo?.has_conflict) {
      setConflictModalData({
        message: `Hoạt động này trùng giờ với lịch đã có: "${conflictInfo.conflicting_with?.title || 'Sự kiện khác'}" (${conflictInfo.warning_message}). Bạn có chắc chắn muốn tiếp tục đăng ký không?`,
        isSwap: false,
      });
      setShowConflictModal(true);
    } else {
      executeJoin(false);
    }
  };

  async function handleCancelRequest() {
    if (!myRequest) return;
    try {
      await participationApi.cancel(myRequest.id);
      setMyRequest(null);
      toast.success('Đã hủy yêu cầu');
    } catch (error) {
      toast.error('Không thể hủy yêu cầu');
    }
  }

  async function handleRespond(requestId: string, status: 'approved' | 'declined') {
    try {
      if (status === 'approved') {
        await participationApi.approve(requestId);
      } else {
        await participationApi.decline(requestId);
      }
      toast.success(`Yêu cầu đã được ${status === 'approved' ? 'phê duyệt' : 'từ chối'}`);
      // Refresh data to update participant count and remove request from list
      loadData();
    } catch (error) {
      toast.error(`Không thể ${status === 'approved' ? 'phê duyệt' : 'từ chối'} yêu cầu`);
    }
  }

  async function handleLeaveActivity() {
    if (!id) return;
    try {
      await participationApi.leaveActivity(id);
      setMyRequest(null);
      toast.success('Bạn đã rời khỏi hoạt động');
      loadData(); // Refresh participant count
    } catch (error) {
      toast.error('Không thể rời khỏi hoạt động');
    }
  }

  const handleOpenCheckInModal = () => {
    setShowCheckInModal(true);
  };

  const handleToggleAttendance = async (participantUserId: string, currentStatus: boolean) => {
    if (!id) return;
    try {
      setUpdatingAttendanceUserId(participantUserId);
      const res = await activitiesApi.updateAttendance(id, participantUserId, !currentStatus);
      toast.success(res.message);
      setParticipants(prev =>
        prev.map(p => p.user_id === participantUserId ? { ...p, attendance_confirmed: !currentStatus } : p)
      );
    } catch {
      toast.error('Không thể cập nhật điểm danh');
    } finally {
      setUpdatingAttendanceUserId(null);
    }
  };

  async function handleDeleteActivity() {
    if (!id) return;
    const confirm = window.confirm('Bạn có chắc chắn muốn xóa hoạt động này?');
    if (!confirm) return;

    try {
      await activitiesApi.delete(id);
      toast.success('Đã xóa hoạt động');
      navigate('/dashboard');
    } catch (error) {
      toast.error('Không thể xóa hoạt động');
    }
  }

  const loadComments = useCallback(async () => {
    if (!id) return;
    try {
      const data = await interactionsApi.listComments('activities', id, { limit: COMMENT_LIMIT, offset: 0 });
      setComments(data.items);
      setCommentTotal(data.total);
      setCommentHasMore(data.has_more);
      setCommentOffset(0);
    } catch {
      toast.error('Không thể tải lại bình luận');
    }
  }, [id]);

  async function loadMoreComments() {
    if (!id) return;
    const newOffset = commentOffset + COMMENT_LIMIT;
    try {
      const data = await interactionsApi.listComments('activities', id, { limit: COMMENT_LIMIT, offset: newOffset });
      setComments(prev => [...prev, ...data.items]);
      setCommentTotal(data.total);
      setCommentHasMore(data.has_more);
      setCommentOffset(newOffset);
    } catch {
      toast.error('Không thể tải thêm bình luận');
    }
  }

  if (loading || !activity) {
    return <div className="activity-detail-loading">Đang tải...</div>;
  }

  const isHost = user?.id === activity.host_id;
  const isFull = activity.current_participants >= activity.max_participants;
  const vm = mapActivityToDetailViewModel({
    activity,
    currentUserId: user?.id,
    myRequest,
    conflictInfo,
  });

  return (
    <div className="activity-detail-container">
      <div className="activity-header glass">
        <div className="activity-badges-row">
          <div className="category-badge">{activity.category || 'Chung'}</div>
          {activity.social_work_days && activity.social_work_days > 0 && (
            <div className="social-work-badge flex items-center gap-1">
              <GraduationCap size={14} />
              {activity.social_work_days} ngày CTXH
            </div>
          )}
        </div>
        <h1 className="activity-title">{activity.title}</h1>
        <div className="activity-meta">
          <span>Được tổ chức bởi <Link to={`/profile/${activity.host_id}`} className="activity-host-link">@{activity.host?.username}</Link></span>
          <span className="meta-dot">•</span>
          <span className="flex items-center gap-1">
            <CalendarIcon size={14} />
            {new Date(activity.start_time).toLocaleString('vi-VN')}
          </span>
        </div>
        <div className="activity-header-actions">
          <LikeButton targetType="activities" targetId={id!} initialLiked={liked} initialCount={likeCount} />
          {!isHost && (
            <Button size="sm" variant="secondary" onClick={() => setIsReportModalOpen(true)}>
              Báo cáo
            </Button>
          )}
        </div>
      </div>

      <ReportModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        targetType="activity"
        targetId={id!}
      />

      <div className="activity-content-grid">
        <div className="activity-main glass">
          <h3>Mô tả</h3>
          <p className="activity-description">{activity.description}</p>

          {activity.private_description ? (
            <div className="callout">
              <h4 className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-semibold">
                <Unlock size={16} /> Nội dung dành cho thành viên
              </h4>
              <p className="text-pre-wrap">{activity.private_description}</p>
            </div>
          ) : activity.privacy === 'private' && !isHost && (
            <div className="callout callout--muted flex items-center gap-1.5">
              <Lock size={16} /> Thông tin riêng tư (Chỉ được tiết lộ cho người tổ chức và người tham gia được phê duyệt)
            </div>
          )}

          <div className="flex-col gap-3">
            <div className="stat-box">
              <span className="stat-label">Điểm hẹn / Địa điểm</span>
              <span className="stat-value flex items-center gap-1">
                <MapPin size={15} className="text-red-500" />
                {activity.meeting_location || activity.location_name || 'TBD'}
              </span>
            </div>
            <div className="flex-row gap-3">
              <div className="stat-box">
                <span className="stat-label">Quyền riêng tư</span>
                <span className="stat-value">{activity.privacy?.toUpperCase()}</span>
              </div>
              <div className="stat-box">
                <span className="stat-label">Trạng thái</span>
                <span className={`stat-value ${isFull ? 'stat-status--full' : 'stat-status--open'}`}>
                  {isFull ? 'Đã đầy' : 'Đang mở'}
                </span>
              </div>
            </div>

          </div>

          {participants.length > 0 && (
            <div className="participants-section">
              <h3 className="flex items-center gap-1.5">
                <Users size={18} />
                Người tham gia
              </h3>
              <span className="stat-value">
                {activity.current_participants} / {activity.max_participants}
              </span>
              <div className="participants-list">
                <div
                  className="participant-chip participant-chip--host"
                  title="Host"
                >
                  <Sparkles size={13} className="inline mr-1 text-amber-500" /> @{activity.host?.username}
                </div>
                {participants.filter(p => p.user?.username !== activity.host?.username).map(p => (
                  <div
                    key={p.id}
                    className={`participant-chip flex items-center gap-2 ${p.attendance_confirmed ? 'border-emerald-500 bg-emerald-500/10' : ''}`}
                  >
                    <span>@{p.user?.username}</span>
                    {p.attendance_confirmed ? (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950/70 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 font-semibold flex items-center gap-1" title="Đã xác nhận có mặt">
                        <CheckCircle2 size={12} className="text-emerald-600 dark:text-emerald-400" /> Đã đến
                      </span>
                    ) : (
                      <span className="text-xs px-1.5 py-0.5 rounded bg-gray-500/10 text-gray-500 font-normal">
                        Chưa điểm danh
                      </span>
                    )}
                    {isHost && (
                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          className={`text-xs px-2 py-0.5 rounded border transition-colors ${p.attendance_confirmed ? 'border-amber-300 text-amber-700 bg-amber-50 hover:bg-amber-100' : 'border-indigo-300 text-indigo-700 bg-indigo-50 hover:bg-indigo-100'}`}
                          disabled={updatingAttendanceUserId === p.user_id}
                          onClick={() => handleToggleAttendance(p.user_id, !!p.attendance_confirmed)}
                        >
                          {updatingAttendanceUserId === p.user_id ? '...' : p.attendance_confirmed ? 'Hủy duyệt' : 'Xác nhận'}
                        </button>
                        {p.attendance_confirmed && (
                          <button
                            type="button"
                            className="text-xs px-1.5 py-0.5 rounded border border-gray-300 bg-white hover:bg-gray-100 dark:bg-black/20"
                            title="Xem giấy chứng nhận"
                            onClick={() => {
                              setCertificateTargetUserId(p.user_id);
                              setShowCertificateModal(true);
                            }}
                          >
                            <FileText size={13} />
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="activity-sidebar glass">
          {activity.trophy && (
            <div className="trophy-card">
              <h3 className="trophy-card__title">Kiếm cúp!</h3>
              <div className="trophy-card__icon">
                {activity.trophy.icon || '🏆'}
              </div>
              <h4 className="trophy-card__name">{activity.trophy.name}</h4>
              {activity.trophy.description && (
                <p className="trophy-card__description">
                  {activity.trophy.description}
                </p>
              )}
              <div className="trophy-card__points">
                +{activity.trophy.points} Điểm
              </div>
            </div>
          )}

          {isHost ? (
            <div className="host-management">
              <div className="host-actions flex flex-col gap-2">
                {activity.attendance_mode === 'qr_code' && (
                  <Button
                    variant="primary"
                    fullWidth
                    onClick={() => setShowHostQrModal(true)}
                  >
                    <QrCode size={16} className="inline mr-1.5" /> Hiển thị QR Điểm danh
                  </Button>
                )}
                <Button
                  variant="secondary"
                  fullWidth
                  onClick={() => navigate(`/activities/${id}/edit`)}
                >
                  Chỉnh sửa
                </Button>
                <Button
                  fullWidth
                  onClick={handleDeleteActivity}
                  className="btn-danger-subtle"
                >
                  Xóa
                </Button>
              </div>

              <h3>Yêu cầu tham gia</h3>
              {requests.length === 0 ? (
                <p className="no-requests">Không có yêu cầu đang chờ xử lý.</p>
              ) : (
                <div className="request-list">
                  {requests.map((req) => (
                    <div key={req.id} className="request-item">
                      <div className="request-user">
                        <strong>@{req.user?.username}</strong> muốn tham gia
                      </div>
                      {req.message && (
                        <p className="request-message">"{req.message}"</p>
                      )}
                      <div className="request-actions">
                        <Button
                          size="sm"
                          onClick={() => handleRespond(req.id, 'approved')}
                          disabled={isFull}
                        >
                          Phê duyệt
                        </Button>
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => handleRespond(req.id, 'declined')}
                        >
                          Từ chối
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="participant-actions">
              {myRequest ? (
                <div className="my-request-status">
                  <h3>Yêu cầu của bạn</h3>
                  <div className={`status-badge ${myRequest.status}`}>
                    {myRequest.status.toUpperCase()}
                  </div>
                  {myRequest.status === 'pending' && (
                    <Button
                      variant="secondary"
                      fullWidth
                      className="mt-4"
                      onClick={handleCancelRequest}
                    >
                      Hủy yêu cầu
                    </Button>
                  )}
                  {myRequest.status === 'approved' && (
                    <>
                      {myRequest.attendance_confirmed ? (
                        <div className="mt-4 p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-300 dark:border-emerald-800 text-center">
                          <CheckCircle2 size={32} className="text-emerald-600 dark:text-emerald-400 mx-auto mb-1" />
                          <div className="font-bold text-emerald-800 dark:text-emerald-200">Đã xác nhận có mặt!</div>
                          {activity.trophy && (
                            <div className="text-xs text-[var(--color-text-secondary)] mt-1 flex items-center justify-center gap-1">
                              <Trophy size={14} className="text-amber-500" /> Đã nhận Trophy: <strong>{activity.trophy.name}</strong> (+{activity.trophy.points} điểm).
                            </div>
                          )}
                          <Button
                            variant="primary"
                            fullWidth
                            className="mt-3"
                            onClick={() => {
                              setCertificateTargetUserId(undefined);
                              setShowCertificateModal(true);
                            }}
                          >
                            <FileText size={16} className="inline mr-1.5" /> Xuất Giấy chứng nhận / Minh chứng (PDF)
                          </Button>
                        </div>
                      ) : (
                        <div className="mt-4 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-center">
                          <div className="text-sm font-semibold text-amber-700 dark:text-amber-400">Chưa xác nhận điểm danh</div>
                          {activity.attendance_mode === 'qr_code' && (
                            <div className="mt-2 flex flex-col gap-2">
                              <p className="text-xs text-[var(--color-text-secondary)]">Quét mã QR hoặc nhập mã do Host hiển thị tại sự kiện.</p>
                              <Button
                                variant="primary"
                                fullWidth
                                onClick={handleOpenCheckInModal}
                              >
                                📍 Quét QR / Điểm danh tại sự kiện
                              </Button>
                            </div>
                          )}
                          {activity.attendance_mode === 'auto' && (
                            <p className="text-xs text-[var(--color-text-secondary)] mt-1">
                              🟢 Điểm danh tự động: Hệ thống sẽ tự ghi nhận tham gia sau khi sự kiện kết thúc.
                            </p>
                          )}
                          {activity.attendance_mode === 'manual' && (
                            <p className="text-xs text-[var(--color-text-secondary)] mt-1">
                              👤 Vui lòng liên hệ Host tại sự kiện để được xác nhận điểm danh thủ công.
                            </p>
                          )}
                        </div>
                      )}

                      <p className="success-message mt-4">Bạn đã tham gia! Kiểm tra vị trí chính xác trên bản đồ.</p>
                      <Button
                        variant="secondary"
                        fullWidth
                        className="mt-4"
                        onClick={handleLeaveActivity}
                      >
                        Rời khỏi hoạt động
                      </Button>
                    </>
                  )}
                </div>
              ) : (
                <form onSubmit={handleJoinRequest} className="join-form">
                  {vm.conflictMessage && (
                    <div
                      role="alert"
                      style={{
                        fontSize: '0.85rem',
                        padding: '12px 14px',
                        borderRadius: '8px',
                        marginBottom: '14px',
                        background: conflictInfo?.level === 'hard_conflict' ? 'rgba(239, 68, 68, 0.08)' : 'rgba(245, 158, 11, 0.08)',
                        border: `1px solid ${conflictInfo?.level === 'hard_conflict' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
                        color: conflictInfo?.level === 'hard_conflict' ? '#dc2626' : '#d97706',
                        lineHeight: '1.4',
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '8px',
                      }}
                    >
                      <AlertTriangle size={18} className="shrink-0 mt-0.5" />
                      <div>
                        <strong>{conflictInfo?.level === 'hard_conflict' ? 'Trùng lịch của bạn: ' : 'Lưu ý lịch trình: '}</strong>
                        {vm.conflictMessage}
                      </div>
                    </div>
                  )}

                  <h3>{activity.require_approval ? 'Yêu cầu tham gia' : 'Tham gia hoạt động'}</h3>

                  {vm.dynamicForm && vm.dynamicForm.fields.length > 0 && (
                    <DynamicFormRenderer
                      fields={vm.dynamicForm.fields}
                      responses={formResponses}
                      errors={formErrors}
                      disabled={isSubmittingRegistration}
                      onChange={(fieldLabel, val) => {
                        setFormResponses(prev => ({ ...prev, [fieldLabel]: val }));
                        if (formErrors[fieldLabel]) {
                          setFormErrors(prev => {
                            const next = { ...prev };
                            delete next[fieldLabel];
                            return next;
                          });
                        }
                      }}
                    />
                  )}

                  {activity.require_approval && (
                    <>
                      <p className="join-hint">
                        Hãy cho người tổ chức biết lý do bạn muốn tham gia (không bắt buộc).
                      </p>
                      <textarea
                        value={requestMessage}
                        onChange={(e) => setRequestMessage(e.target.value)}
                        placeholder="Xin chào! Tôi rất muốn tham gia vì..."
                        className="form-input"
                        rows={4}
                      />
                    </>
                  )}
                  <Button
                    type="submit"
                    fullWidth
                    loading={isSubmittingRegistration}
                    disabled={vm.ctaDisabled || isSubmittingRegistration}
                  >
                    {isSubmittingRegistration ? 'Đang xử lý...' : vm.ctaText}
                  </Button>
                </form>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Comments Section */}
      <div className="activity-comments glass">
        <CommentSection
          targetType="activities"
          targetId={id!}
          comments={comments}
          total={commentTotal}
          hasMore={commentHasMore}
          onRefresh={loadComments}
          onLoadMore={loadMoreComments}
        />
      </div>

      {/* Host QR Code Modal */}
      {showHostQrModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-md animate-fade-in">
          <div className="glass bg-[var(--color-bg-surface)] p-6 rounded-3xl max-w-sm w-full border border-white/20 shadow-2xl flex flex-col items-center text-center">
            <div className="flex items-center justify-between w-full mb-2">
              <h3 className="text-lg font-bold text-[var(--color-text-primary)]">📱 Quét mã để điểm danh</h3>
              <button
                onClick={() => setShowHostQrModal(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-white text-xl font-bold p-1 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-[var(--color-text-secondary)] mb-4">
              Người tham gia hướng camera điện thoại vào mã này
            </p>

            <div className="p-3 bg-white rounded-2xl shadow-inner border border-gray-100 flex items-center justify-center">
              {hostQrData ? (
                <img
                  src={`https://api.qrserver.com/v1/create-qr-code/?size=240x240&data=${encodeURIComponent(hostQrData.rotating_token)}`}
                  alt="Check-in QR Code"
                  className="w-56 h-56 rounded-lg"
                />
              ) : (
                <div className="w-56 h-56 flex items-center justify-center text-gray-400">Đang tạo mã...</div>
              )}
            </div>

            {/* Rotating token countdown */}
            <div className="flex items-center gap-2 mt-4 px-3 py-1.5 rounded-full bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-300 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200 text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
              <span>Mã đổi sau: {qrCountdown}s</span>
            </div>

            {/* Token display */}
            <div className="mt-3">
              <span className="text-xs text-[var(--color-text-secondary)] uppercase tracking-wider block">Mã điểm danh trực tiếp:</span>
              <div className="text-3xl font-black tracking-widest text-indigo-600 dark:text-indigo-400 mt-1 font-mono">
                {hostQrData?.rotating_token || '------'}
              </div>
            </div>

            <div className="mt-4 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-700 dark:text-amber-300 text-left">
              🛡️ <strong>Chống gian lận từ xa:</strong> Hệ thống bắt buộc người quét phải ở trong bán kính <strong>{activity.check_in_radius || 300}m</strong> qua GPS & mã đổi liên tục mỗi 30s.
            </div>

            <Button
              variant="secondary"
              fullWidth
              className="mt-4"
              onClick={() => setShowHostQrModal(false)}
            >
              Đóng
            </Button>
          </div>
        </div>
      )}

      {/* Participant Check-In Modal with State Machine */}
      {id && (
        <CheckInModal
          isOpen={showCheckInModal}
          onClose={() => setShowCheckInModal(false)}
          onSuccess={() => {
            loadData();
          }}
          activityId={id}
          activityTitle={activity.title}
          checkInRadius={activity.check_in_radius || 200}
          trophyName={activity.trophy?.name}
          trophyPoints={activity.trophy?.points}
        />
      )}

      {/* Certificate Modal */}
      {id && (
        <CertificateModal
          isOpen={showCertificateModal}
          onClose={() => setShowCertificateModal(false)}
          activityId={id}
          userId={certificateTargetUserId}
        />
      )}

      {/* Conflict / Swap Confirmation Modal */}
      {conflictModalData && (
        <ConflictModal
          isOpen={showConflictModal}
          message={conflictModalData.message}
          isSwap={conflictModalData.isSwap}
          loading={isSubmittingRegistration}
          onConfirm={() => executeJoin(conflictModalData.isSwap)}
          onClose={() => {
            setShowConflictModal(false);
            setConflictModalData(null);
          }}
        />
      )}
    </div>
  );
}
