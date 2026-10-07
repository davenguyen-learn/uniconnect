import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, Link, useSearchParams } from 'react-router-dom';
import {
  Calendar as CalendarIcon,
  Lock,
  CheckCircle2,
  AlertTriangle,
  FileText,
  QrCode,
  Users,
  Trash2,
  X,
  Building2,
  UserPlus,
  Loader2,
  Search,
  Download,
  Clock,
  MapPin,
} from 'lucide-react';
import { activitiesApi, type ActivityResponse } from '../../api/activities';
import { groupsApi, type GroupResponse, type CoHostInvitationResponse } from '../../api/groups';
import { participationApi, type JoinRequestResponse, type JoinRequestCreate } from '../../api/participation';
import { calendarApi, type ConflictInfo } from '../../api/calendar';
import { interactionsApi, type CommentResponse } from '../../api/interactions';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../components/Toast/ToastContext';
import { getFormFieldResponse } from '../../utils/formResponses';
import Button from '../../components/Button/Button';
import Badge from '../../components/Badge/Badge';
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
import { normalizeCategoryName } from '../../types/activity-mapper';
import { formatCtxh } from '../../utils/format';
import './ActivityDetail.css';
import '../../components/groups/GroupModals.css';

export default function ActivityDetail() {
  const { id } = useParams<{ id: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const toast = useToast();

  const [autoCheckInCode, setAutoCheckInCode] = useState<string | null>(null);

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
  const [qrCountdown, setQrCountdown] = useState(60);

  // Live Location Check-In state (Host Broadcast Radius)
  const [liveSession, setLiveSession] = useState<{
    is_active: boolean;
    expires_at: string | null;
    remaining_seconds: number;
    radius: number;
    opened_by_name: string | null;
    attended_count?: number;
    total_approved?: number;
  } | null>(null);
  const [liveCountdown, setLiveCountdown] = useState(0);
  const [liveRadiusInput, setLiveRadiusInput] = useState(50);
  const [isOpeningLiveCheckIn, setIsOpeningLiveCheckIn] = useState(false);
  const [isClosingLiveCheckIn, setIsClosingLiveCheckIn] = useState(false);
  const [isVerifyingLive, setIsVerifyingLive] = useState(false);

  const [showCheckInModal, setShowCheckInModal] = useState(false);
  const [updatingAttendanceUserId, setUpdatingAttendanceUserId] = useState<string | null>(null);

  // Certificate Modal state
  const [showCertificateModal, setShowCertificateModal] = useState(false);
  const [certificateTargetUserId, setCertificateTargetUserId] = useState<string | undefined>(undefined);

  // Manage Participants Modal state
  const [showParticipantsModal, setShowParticipantsModal] = useState(false);
  const [removingParticipantUserId, setRemovingParticipantUserId] = useState<string | null>(null);
  const [isExportingCsv, setIsExportingCsv] = useState(false);
  const [selectedReviewRequest, setSelectedReviewRequest] = useState<JoinRequestResponse | null>(null);

  // Invite Co-Host Modal state
  const [showInviteCoHostModal, setShowInviteCoHostModal] = useState(false);
  const [coHostSearchQuery, setCoHostSearchQuery] = useState('');
  const [coHostSearchResults, setCoHostSearchResults] = useState<GroupResponse[]>([]);
  const [coHostSearchLoading, setCoHostSearchLoading] = useState(false);
  const [invitingGroupId, setInvitingGroupId] = useState<string | null>(null);
  const [coHostMessage, setCoHostMessage] = useState('');
  const [coHostInvitations, setCoHostInvitations] = useState<CoHostInvitationResponse[]>([]);
  const [coHostInvitationsLoading, setCoHostInvitationsLoading] = useState(false);

  const fetchCoHostInvitations = useCallback(async () => {
    if (!id) return;
    try {
      setCoHostInvitationsLoading(true);
      const res = await groupsApi.getActivityCoHostInvitations(id);
      setCoHostInvitations(res || []);
    } catch {
      // Ignored if user not authorized
    } finally {
      setCoHostInvitationsLoading(false);
    }
  }, [id]);

  const fetchCoHostCandidates = useCallback(async (query: string = '') => {
    if (!id) return;
    setCoHostSearchLoading(true);
    try {
      const results = await groupsApi.searchCoHostCandidates(id, {
        search: query.trim() || undefined,
        limit: 15,
      });
      setCoHostSearchResults(results);
    } catch {
      setCoHostSearchResults([]);
    } finally {
      setCoHostSearchLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (showInviteCoHostModal && id) {
      fetchCoHostCandidates(coHostSearchQuery);
      fetchCoHostInvitations();
    }
  }, [showInviteCoHostModal, id, fetchCoHostCandidates, fetchCoHostInvitations]);

  useEffect(() => {
    if (id === 'create' || id === 'new') {
      navigate('/activities/create', { replace: true });
      return;
    }
    if (id) {
      loadData();
    }
  }, [id, navigate]);

  // Auto-trigger check-in when scanned QR code opens page with ?checkin_code=
  useEffect(() => {
    const codeFromUrl = searchParams.get('checkin_code') || searchParams.get('code');
    if (codeFromUrl && activity) {
      setAutoCheckInCode(codeFromUrl.toUpperCase());
      setShowCheckInModal(true);
      const newParams = new URLSearchParams(searchParams);
      newParams.delete('checkin_code');
      newParams.delete('code');
      setSearchParams(newParams, { replace: true });
    }
  }, [searchParams, activity]);

  const fetchLiveCheckInStatus = useCallback(async () => {
    if (!id) return;
    try {
      const res = await participationApi.getLiveCheckInStatus(id);
      setLiveSession(res);
      if (res.is_active && res.remaining_seconds > 0) {
        setLiveCountdown(res.remaining_seconds);
      }
    } catch {
      // ignore
    }
  }, [id]);

  useEffect(() => {
    fetchLiveCheckInStatus();
    const interval = setInterval(() => {
      fetchLiveCheckInStatus();
    }, 8000);
    return () => clearInterval(interval);
  }, [fetchLiveCheckInStatus]);

  useEffect(() => {
    if (!liveSession?.is_active || liveCountdown <= 0) return;
    const t = setInterval(() => {
      setLiveCountdown(prev => {
        if (prev <= 1) {
          fetchLiveCheckInStatus();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(t);
  }, [liveSession?.is_active, liveCountdown, fetchLiveCheckInStatus]);

  useEffect(() => {
    let timer: any;
    if (showHostQrModal && id) {
      activitiesApi.getCheckInCode(id)
        .then(data => {
          setHostQrData(data);
          setQrCountdown(data.expires_in_seconds || 60);
        })
        .catch(() => toast.error('Không thể lấy mã QR'));

      timer = setInterval(() => {
        setQrCountdown(prev => {
          if (prev <= 1) {
            activitiesApi.getCheckInCode(id)
              .then(data => {
                setHostQrData(data);
                return data.expires_in_seconds || 60;
              })
              .catch(() => 60);
            return 60;
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

      if (isHost || user?.role === 'admin' || user?.role === 'edu_org') {
        // Fetch all pending requests for this activity
        const reqs = await participationApi.listByActivity(id!);
        // filter pending locally if API doesn't filter
        setRequests(reqs.filter(r => r.status === 'pending'));

        // Fetch co-host invitations for this activity
        groupsApi.getActivityCoHostInvitations(id!)
          .then(res => setCoHostInvitations(res || []))
          .catch(() => { });
      } else {
        // If not host, fetch my own request status safely
        try {
          const myReqs = await participationApi.listByActivity(id!);
          if (myReqs && myReqs.length > 0) {
            setMyRequest(myReqs[0]);
          }
        } catch {
          // Non-host users do not have full requests permission, which is expected
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
    } catch (error: any) {
      if (error?.response?.status === 403 || error?.status === 403) {
        toast.error('Hoạt động này là nội bộ, chỉ dành riêng cho thành viên nhóm.');
      } else {
        toast.error('Không thể tải chi tiết hoạt động');
      }
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

  const handleOpenLiveCheckIn = () => {
    if (!id) return;
    if (!navigator.geolocation) {
      toast.error('Trình duyệt không hỗ trợ định vị GPS.');
      return;
    }
    setIsOpeningLiveCheckIn(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const { latitude, longitude } = pos.coords;
          const radius = Math.max(5, Number(liveRadiusInput) || 50);
          const res = await participationApi.openLiveCheckIn(id, {
            latitude,
            longitude,
            radius,
            duration_seconds: 300,
          });
          toast.success(res.message);
          setLiveSession({
            is_active: true,
            expires_at: res.expires_at,
            remaining_seconds: res.remaining_seconds,
            radius: res.radius,
            opened_by_name: user?.username || null,
          });
          setLiveCountdown(res.remaining_seconds);
        } catch (err: any) {
          toast.error(err?.message || err.response?.data?.detail || 'Không thể mở phiên điểm danh.');
        } finally {
          setIsOpeningLiveCheckIn(false);
        }
      },
      (err) => {
        setIsOpeningLiveCheckIn(false);
        if (err.code === err.PERMISSION_DENIED) {
          toast.error('Bạn đã từ chối quyền truy cập GPS.');
        } else {
          toast.error('Không thể lấy toạ độ GPS. Vui lòng thử lại.');
        }
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const handleCloseLiveCheckIn = async () => {
    if (!id) return;
    try {
      setIsClosingLiveCheckIn(true);
      const res = await participationApi.closeLiveCheckIn(id);
      toast.success(res.message);
      setLiveSession(null);
      setLiveCountdown(0);
    } catch (err: any) {
      toast.error(err?.message || err.response?.data?.detail || 'Không thể đóng phiên.');
    } finally {
      setIsClosingLiveCheckIn(false);
    }
  };

  const handleVerifyLiveCheckIn = () => {
    if (!id) return;
    if (!navigator.geolocation) {
      toast.error('Trình duyệt không hỗ trợ định vị GPS.');
      return;
    }
    setIsVerifyingLive(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const { latitude, longitude, accuracy } = pos.coords;
          const res = await participationApi.verifyLiveCheckIn(id, {
            latitude,
            longitude,
            accuracy,
          });
          toast.success(res.message);
          await loadData();
          fetchLiveCheckInStatus();
        } catch (err: any) {
          toast.error(err?.message || err.response?.data?.detail || 'Điểm danh không thành công.');
        } finally {
          setIsVerifyingLive(false);
        }
      },
      (err) => {
        setIsVerifyingLive(false);
        if (err.code === err.PERMISSION_DENIED) {
          toast.error('Vui lòng cho phép quyền truy cập vị trí GPS để xác nhận khoảng cách.');
        } else {
          toast.error('Không thể xác định vị trí GPS.');
        }
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const handleSetAttendance = async (participantUserId: string, attended: boolean) => {
    if (!id) return;
    try {
      setUpdatingAttendanceUserId(participantUserId);
      const res = await activitiesApi.updateAttendance(id, participantUserId, attended);
      toast.success(res.message);
      setParticipants(prev =>
        prev.map(p => p.user_id === participantUserId ? { ...p, attendance_confirmed: attended } : p)
      );
    } catch {
      toast.error('Không thể cập nhật trạng thái điểm danh');
    } finally {
      setUpdatingAttendanceUserId(null);
    }
  };

  const handleRemoveParticipant = async (participantUserId: string, username: string) => {
    if (!id) return;
    const confirm = window.confirm(`Bạn có chắc muốn xóa @${username} khỏi hoạt động này?`);
    if (!confirm) return;

    try {
      setRemovingParticipantUserId(participantUserId);
      await participationApi.removeParticipant(id, participantUserId);
      toast.success(`Đã xóa @${username} khỏi hoạt động`);
      setParticipants(prev => prev.filter(p => p.user_id !== participantUserId));
      setActivity(prev => prev ? { ...prev, current_participants: Math.max(1, prev.current_participants - 1) } : null);
    } catch (error: any) {
      toast.error(error?.message || 'Không thể xóa người tham gia');
    } finally {
      setRemovingParticipantUserId(null);
    }
  };

  async function handleDeleteActivity() {
    if (!id) return;
    const confirm = window.confirm('Bạn có chắc chắn muốn hủy hoạt động này? Hành động này không thể hoàn tác.');
    if (!confirm) return;

    try {
      await activitiesApi.delete(id);
      toast.success('Đã hủy hoạt động thành công');
      navigate('/dashboard');
    } catch (error: any) {
      toast.error(error?.message || 'Không thể hủy hoạt động');
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

  const isHost = Boolean(
    user && (
      String(user.id) === String(activity.host_id) ||
      (user.username && activity.host?.username && user.username.toLowerCase() === activity.host.username.toLowerCase())
    )
  );
  const isAdmin = user?.role === 'admin' || user?.role === 'edu_org';
  const canExport = Boolean(isHost || isAdmin);
  const canManage = isHost || isAdmin;
  const currentAttendedCount = liveSession?.attended_count ?? participants.filter(p => p.attendance_confirmed).length;
  const currentTotalApproved = liveSession?.total_approved ?? (participants.length || activity?.current_participants || 0);

  const handleExportCsv = async () => {
    if (!id || !activity) return;
    setIsExportingCsv(true);
    try {
      const blob = await activitiesApi.exportParticipantsCsv(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const cleanTitle = (activity.title || 'hoat_dong').toLowerCase().replace(/[^\w\s-]/g, '').trim().replace(/[-\s]+/g, '_').slice(0, 30);
      const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '');
      a.download = `danh_sach_tham_gia_${cleanTitle || 'hoat_dong'}_${dateStr}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      toast.success('Đã xuất danh sách CSV thành công!');
    } catch (error: any) {
      toast.error(error?.message || 'Không thể xuất danh sách người tham gia');
    } finally {
      setIsExportingCsv(false);
    }
  };
  const isFull = activity.current_participants >= activity.max_participants;
  const vm = mapActivityToDetailViewModel({
    activity,
    currentUserId: user?.id,
    myRequest,
    conflictInfo,
  });

  const allDisplayParticipants = [...participants]
    .filter(p => p.user?.username && p.user?.username !== activity.host?.username)
    .sort((a, b) => (a.user?.username || '').localeCompare(b.user?.username || '', 'vi', { sensitivity: 'base' }));

  const formatEventTime = (startStr: string, endStr?: string) => {
    const start = new Date(startStr);
    const end = endStr ? new Date(endStr) : null;

    const startT = start.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    const startD = start.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });

    if (!end) {
      return `${startT} • ${startD}`;
    }

    const endT = end.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    const endD = end.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });

    if (startD === endD) {
      return `${startT} - ${endT} • ${startD}`;
    }
    return `${startT} ${startD} - ${endT} ${endD}`;
  };

  return (
    <div className="activity-detail-container">
      <ReportModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        targetType="activity"
        targetId={id!}
      />

      <div className="activity-content-grid">
        <div className="activity-main glass">
          {/* Header section inside the main card */}
          <div className="activity-header-section">
            <div className="activity-badges-row">
              <Badge text={normalizeCategoryName(activity.category)} bg="var(--color-primary, #2563eb)" />
              {activity.privacy === 'private' && (
                <Badge text="Nội bộ nhóm" bg="#ef4444" />
              )}
              {activity.require_approval && (
                <Badge text="Cần phê duyệt" bg="#7c3aed" />
              )}
              {typeof activity.social_work_days === 'number' && activity.social_work_days > 0 ? (
                <Badge text={`${formatCtxh(activity.social_work_days)} ngày CTXH`} bg="#16a34a" />
              ) : null}
              {activity.trophy && (
                <Badge
                  text={activity.trophy.points > 0 ? `${activity.trophy.name} (+${activity.trophy.points}đ)` : activity.trophy.name}
                  bg="#d97706"
                  title={activity.trophy.name}
                />
              )}
            </div>

            <h1 className="activity-title">{activity.title}</h1>

            <div className="activity-meta">
              <span>Được tổ chức bởi <Link to={`/profile/${activity.host_id}`} className="activity-host-link">@{activity.host?.username}</Link></span>
              {activity.group && (
                <>
                  <span className="meta-dot">•</span>
                  <Link to={`/groups/${activity.group.id}`} className="activity-group-link">
                    <Building2 size={14} />
                    {activity.group.name}
                  </Link>
                </>
              )}
              {activity.co_hosts && activity.co_hosts.length > 0 && (
                <>
                  <span className="meta-dot">•</span>
                  <span className="text-xs text-slate-500 font-medium">Đồng tổ chức:</span>
                  {activity.co_hosts.map(ch => (
                    <Link key={ch.id} to={`/groups/${ch.id}`} className="activity-group-link">
                      <Building2 size={14} />
                      {ch.name}
                    </Link>
                  ))}
                </>
              )}
              {canManage && coHostInvitations.some(inv => inv.status === 'pending') && (
                <>
                  <span className="meta-dot">•</span>
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 shadow-sm hover:bg-amber-100 transition-colors"
                    onClick={() => setShowInviteCoHostModal(true)}
                    title="Nhấn để xem các lời mời đang chờ phản hồi"
                  >
                    <Clock size={12} />
                    {coHostInvitations.filter(inv => inv.status === 'pending').length} lời mời đang đợi chấp nhận
                  </button>
                </>
              )}
              <span className="meta-dot">•</span>
              <span className="flex items-center gap-1.5">
                <CalendarIcon size={14} />
                {formatEventTime(activity.start_time, activity.end_time)}
              </span>
            </div>

            <div className="activity-header-actions">
              <LikeButton targetType="activities" targetId={id!} initialLiked={liked} initialCount={likeCount} />
              {canManage && (
                <>
                  {activity.group && (
                    <Button
                      size="sm"
                      variant="secondary"
                      className="activity-invite-cohost-btn"
                      onClick={() => setShowInviteCoHostModal(true)}
                    >
                      <UserPlus size={14} className="inline mr-1" /> Mời nhóm đồng tổ chức hoạt động
                    </Button>
                  )}
                  <Button
                    size="sm"
                    className="activity-edit-btn"
                    onClick={() => navigate(`/activities/${id}/edit`)}
                  >
                    Chỉnh sửa
                  </Button>
                  <Button
                    size="sm"
                    variant="danger"
                    className="activity-delete-btn"
                    onClick={handleDeleteActivity}
                  >
                    <Trash2 size={14} className="inline mr-1" /> Hủy hoạt động
                  </Button>
                </>
              )}
              {!isHost && (
                <Button size="sm" variant="secondary" className="activity-report-btn" onClick={() => setIsReportModalOpen(true)}>
                  Báo cáo
                </Button>
              )}
            </div>
          </div>

          <div className="activity-card-divider" />

          {/* Description & Member content */}
          <div className="activity-body-section">
            <h3>Mô tả</h3>
            <p className="activity-description">{activity.description}</p>

            {activity.private_description ? (
              <div className="activity-member-private-box">
                <h4 className="activity-member-private-title">
                  Nội dung dành cho thành viên
                </h4>
                <p className="activity-member-private-content">{activity.private_description}</p>
              </div>
            ) : activity.privacy === 'private' && !isHost && (
              <div className="callout callout--muted flex items-center gap-1.5">
                <Lock size={16} /> Thông tin riêng tư (Chỉ được tiết lộ cho người tổ chức và người tham gia được phê duyệt)
              </div>
            )}

            {/* Clean text metadata: Điểm hẹn, Quyền riêng tư, Trạng thái */}
            <div className="activity-info-list">
              <div className="activity-info-item">
                <span className="activity-info-label">Địa điểm:</span>
                <span className="activity-info-value">
                  {activity.meeting_location || activity.location_name || 'TBD'}
                </span>
              </div>
              <div className="activity-info-item">
                <span className="activity-info-label">Hình thức tham gia:</span>
                <span className={`activity-info-value ${activity.require_approval ? 'text-indigo-600' : 'text-emerald-600'}`}>
                  {activity.require_approval ? 'Cần xét duyệt' : 'Công khai'}
                </span>
              </div>
              <div className="activity-info-item">
                <span className="activity-info-label">Quyền riêng tư:</span>
                <span className="activity-info-value">
                  {activity.privacy?.toLowerCase() === 'private' ? 'Riêng tư' : 'Công khai'}
                </span>
              </div>
              <div className="activity-info-item">
                <span className="activity-info-label">Trạng thái:</span>
                <span className={`activity-info-value ${isFull ? 'stat-status--full' : 'stat-status--open'}`}>
                  {isFull ? 'Đã đầy' : 'Đang mở'}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="activity-sidebar glass">
          {canManage ? (
            <div className="host-management">
              {isHost && (
                <div className="host-actions mb-4">
                  <button
                    type="button"
                    onClick={() => setShowHostQrModal(true)}
                    className="w-full h-full p-4 rounded-2xl bg-[var(--color-primary)] text-white shadow-md hover:opacity-95 transition-all flex flex-col items-center !justify-center text-center gap-1.5 cursor-pointer border-0"
                  >
                    <div className="flex items-center gap-2 font-bold text-sm">
                      <QrCode size={18} />
                      <span>Hiển thị QR Điểm danh</span>
                    </div>
                    <span className="text-[11px] text-white/80 font-normal">
                      Mã QR xoay vòng 60s & quét camera
                    </span>
                  </button>

                  {/* Điểm danh theo phạm vi (Live GPS Proximity) */}
                  <div className="p-4 rounded-2xl bg-white shadow-md text-left flex flex-col justify-between h-full border-0">
                    <div className="text-xs font-bold text-slate-800 mb-1.5 flex items-center justify-between">
                      <span className="flex items-center gap-1.5">
                        Điểm danh theo phạm vi
                      </span>
                      {liveSession?.is_active && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full shadow-xs">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
                          {Math.floor(liveCountdown / 60)}:{String(liveCountdown % 60).padStart(2, '0')}
                        </span>
                      )}
                    </div>

                    {liveSession?.is_active ? (
                      <div className="flex flex-col justify-between flex-1 gap-2">
                        <p className="text-[11px] text-slate-600 leading-tight">
                          Đang mở phạm vi <strong>{liveSession.radius}m</strong> quanh vị trí của bạn (5 phút). Thành viên lân cận có thể tự bấm xác nhận.
                        </p>
                        <div className="flex items-center justify-between px-2.5 py-1.5 rounded-xl bg-slate-50 text-xs shadow-2xs">
                          <span className="text-slate-600 flex items-center gap-1 font-medium text-[11px]">
                            <Users size={12} className="text-indigo-600" />
                            Đã điểm danh:
                          </span>
                          <span className="font-bold text-slate-800 text-[11px]">
                            <span className="text-emerald-600 font-extrabold">{currentAttendedCount}</span> / {currentTotalApproved}
                          </span>
                        </div>
                        <Button
                          size="sm"
                          variant="secondary"
                          fullWidth
                          className="!text-rose-600 hover:!bg-rose-100 shadow-xs py-1.5 text-xs font-semibold mt-auto !border-0 bg-rose-50/80"
                          onClick={handleCloseLiveCheckIn}
                          disabled={isClosingLiveCheckIn}
                        >
                          {isClosingLiveCheckIn ? 'Đang đóng...' : 'Đóng phiên điểm danh này'}
                        </Button>
                      </div>
                    ) : (
                      <div className="flex flex-col justify-between flex-1 gap-2">
                        <div className="flex items-center justify-between text-[11px] text-slate-500 leading-tight">
                          <span>Mở phiên GPS 5 phút.</span>
                          <span className="font-semibold text-slate-700">
                            <span className="text-emerald-600 font-bold">{currentAttendedCount}</span>/{currentTotalApproved} đã có mặt
                          </span>
                        </div>
                        <div className="flex items-center gap-2 mt-auto">
                          <div className="relative w-20 shrink-0">
                            <input
                              type="number"
                              min={5}
                              max={5000}
                              value={liveRadiusInput}
                              onChange={(e) => setLiveRadiusInput(Math.max(5, Number(e.target.value)))}
                              placeholder="50"
                              title="Bán kính cho phép (mét)"
                              className="w-full text-xs font-semibold px-2.5 py-1.5 pr-5 rounded-lg bg-slate-50 shadow-xs focus:outline-none focus:ring-1 focus:ring-indigo-500 border-0"
                            />
                            <span className="absolute right-1.5 top-1/2 -translate-y-1/2 text-[11px] font-semibold text-slate-400">
                              m
                            </span>
                          </div>
                          <Button
                            size="sm"
                            variant="primary"
                            className="flex-1 bg-indigo-600 hover:bg-indigo-700 whitespace-nowrap text-xs font-bold shadow-xs py-1.5 border-0"
                            disabled={isOpeningLiveCheckIn}
                            onClick={handleOpenLiveCheckIn}
                          >
                            Bắt đầu
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {isHost && (
                <>
                  <h3>Yêu cầu tham gia</h3>
                  {requests.length === 0 ? (
                    <p className="no-requests">Không có yêu cầu đang chờ xử lý.</p>
                  ) : (
                    <div className="request-list">
                      {requests.map((req) => (
                        <div key={req.id} className="request-item">
                          <div className="request-user">
                            <strong>@{req.user?.username}</strong> {req.user?.full_name ? `(${req.user.full_name})` : ''} muốn tham gia
                          </div>
                          {req.message && (
                            <p className="request-message">"{req.message}"</p>
                          )}
                          {req.form_responses && Object.keys(req.form_responses).length > 0 && (
                            <button
                              type="button"
                              className="text-xs font-semibold text-primary-600 hover:text-primary-700 flex items-center gap-1.5 mt-1.5 mb-2 bg-primary-50 hover:bg-primary-100 py-1 px-2.5 rounded-lg shadow-sm transition-colors w-fit cursor-pointer"
                              onClick={() => setSelectedReviewRequest(req)}
                            >
                              <FileText size={13} />
                              <span>Xem câu trả lời biểu mẫu</span>
                            </button>
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
                </>
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
                        <div className="mt-4 p-4 rounded-xl bg-emerald-50 shadow-sm text-center">
                          <CheckCircle2 size={32} className="text-emerald-600 mx-auto mb-1" />
                          <div className="font-bold text-emerald-800">Đã xác nhận có mặt!</div>
                          {activity.trophy && (
                            <div className="text-xs text-[var(--color-text-secondary)] mt-1 flex items-center justify-center gap-1">
                              Đã nhận Danh hiệu: <strong>{activity.trophy.name}</strong>
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
                            Xuất giấy xác nhận đã tham gia (PDF)
                          </Button>
                        </div>
                      ) : (
                        (() => {
                          const now = new Date();
                          const startTime = new Date(activity.start_time);
                          const endTime = new Date(activity.end_time);
                          const earliestCheckIn = new Date(startTime.getTime() - 30 * 60 * 1000);
                          const latestCheckIn = new Date(endTime.getTime() + 2 * 60 * 60 * 1000);
                          const isCheckInOpen = now >= earliestCheckIn && now <= latestCheckIn;
                          const isCheckInClosed = now > latestCheckIn;

                          if (isCheckInOpen || liveSession?.is_active) {
                            return (
                              <div className="mt-4 space-y-3">
                                {/* Thẻ điểm danh theo phạm vi (Live Proximity) khi Host đang mở */}
                                {liveSession?.is_active && (
                                  <div className="p-4 rounded-2xl bg-gradient-to-br from-indigo-50/90 to-blue-50/90 border border-indigo-200/80 shadow-md text-left">
                                    <div className="flex items-center justify-between mb-1.5">
                                      <span className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-700 uppercase tracking-wide">
                                        <span className="w-2 h-2 rounded-full bg-indigo-600 animate-ping" />
                                        Điểm danh theo phạm vi
                                      </span>
                                      <span className="text-xs font-bold text-indigo-900 bg-white px-2.5 py-0.5 rounded-full shadow-2xs">
                                        {Math.floor(liveCountdown / 60)}:{String(liveCountdown % 60).padStart(2, '0')}
                                      </span>
                                    </div>
                                    <p className="text-xs text-slate-600 mb-3">
                                      Host đang mở điểm danh tại chỗ trong bán kính <strong>{liveSession.radius}m</strong>. Nhấn nút để hệ thống xác nhận bạn đang có mặt.
                                    </p>
                                    <Button
                                      variant="primary"
                                      fullWidth
                                      className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2.5 shadow-sm"
                                      onClick={handleVerifyLiveCheckIn}
                                      disabled={isVerifyingLive}
                                    >
                                      {isVerifyingLive ? (
                                        <>
                                          <Loader2 size={16} className="animate-spin inline mr-1.5" />
                                          Đang đo khoảng cách GPS...
                                        </>
                                      ) : (
                                        <>
                                          <MapPin size={16} className="inline mr-1.5" />
                                          Xác nhận vị trí của tôi (Bán kính {liveSession.radius}m)
                                        </>
                                      )}
                                    </Button>
                                  </div>
                                )}

                                {/* Thẻ điểm danh QR / Nhập mã thông thường */}
                                <div className="p-4 rounded-xl bg-amber-500/10 shadow-sm text-center">
                                  <div className="text-sm font-semibold text-amber-800">Chưa xác nhận điểm danh</div>
                                  {activity.attendance_mode !== 'auto' ? (
                                    <div className="mt-2.5 flex flex-col gap-2">
                                      <p className="text-xs text-[var(--color-text-secondary)]">
                                        Nhập mã điểm danh hoặc quét mã QR do Host hiển thị tại sự kiện.
                                      </p>
                                      <Button
                                        variant="primary"
                                        fullWidth
                                        onClick={handleOpenCheckInModal}
                                      >
                                        <QrCode size={16} className="inline mr-1.5" /> Quét QR / Điểm danh tại sự kiện
                                      </Button>
                                      {activity.attendance_mode === 'manual' && (
                                        <p className="text-[11px] text-[var(--color-text-secondary)] mt-0.5">
                                          (Hoặc liên hệ Host để được xác nhận điểm danh thủ công)
                                        </p>
                                      )}
                                    </div>
                                  ) : (
                                    <p className="text-xs text-[var(--color-text-secondary)] mt-1 flex items-center justify-center gap-1">
                                      <CheckCircle2 size={13} className="text-emerald-600 shrink-0 inline" />
                                      <span>Điểm danh tự động: Hệ thống sẽ tự ghi nhận tham gia sau khi sự kiện kết thúc.</span>
                                    </p>
                                  )}
                                </div>
                              </div>
                            );
                          }

                          if (isCheckInClosed) {
                            return (
                              <div className="mt-4 p-3 rounded-xl bg-slate-100 shadow-sm text-center">
                                <div className="text-xs font-semibold text-slate-500 flex items-center justify-center gap-1.5">
                                  <AlertTriangle size={14} className="text-amber-500 shrink-0 inline" />
                                  <span>Phiên điểm danh cho hoạt động này đã kết thúc.</span>
                                </div>
                              </div>
                            );
                          }

                          return (
                            <div className="mt-4 p-3 rounded-xl bg-slate-100 shadow-sm text-center">
                              <div className="text-xs font-medium text-slate-600 flex items-center justify-center gap-1.5">
                                <Clock size={14} className="text-slate-500 shrink-0 inline" />
                                <span>Phiên điểm danh sẽ mở lúc {earliestCheckIn.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })} (30 phút trước khi bắt đầu).</span>
                              </div>
                            </div>
                          );
                        })()
                      )}

                      {new Date() < new Date(activity.start_time) && !myRequest.attendance_confirmed && (
                        <Button
                          variant="secondary"
                          fullWidth
                          className="mt-4 btn-leave-activity"
                          onClick={handleLeaveActivity}
                        >
                          Rời khỏi hoạt động
                        </Button>
                      )}
                    </>
                  )}
                </div>
              ) : (vm.isPast || vm.isStarted) ? (
                <div className="p-4 rounded-2xl bg-slate-100 shadow-sm text-center">
                  <div className="text-xs font-semibold text-slate-600 flex items-center justify-center gap-1.5">
                    <Clock size={14} className="text-slate-500 shrink-0 inline" />
                    <span>
                      {vm.isPast
                        ? 'Hoạt động đã kết thúc • Đã đóng đăng ký.'
                        : 'Hoạt động đã bắt đầu • Đã đóng đăng ký tham gia.'}
                    </span>
                  </div>
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
                        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
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

          {/* Participants list in sidebar */}
          <div className="participants-section">
            <div className="flex items-center justify-between mb-2">
              <h3 className="flex items-center gap-1.5 mb-0">
                <Users size={18} />
                Người tham gia
              </h3>
              <span className="stat-value">
                {allDisplayParticipants.length || activity.current_participants} / {activity.max_participants}
              </span>
            </div>

            {(isHost || canExport) && (
              <Button
                variant="secondary"
                size="sm"
                fullWidth
                className="mb-3"
                onClick={() => setShowParticipantsModal(true)}
              >
                <Users size={14} className="inline mr-1.5" /> Quản lý người tham gia
              </Button>
            )}

            <div className="participants-list">
              <Link
                to={`/profile/${activity.host_id}`}
                className="participant-chip participant-chip--host"
                title="Người tổ chức (Host)"
              >
                @{activity.host?.username}
              </Link>
              {allDisplayParticipants.map((p) => (
                <Link
                  key={p.user_id}
                  to={`/profile/${p.user_id}`}
                  className="participant-chip"
                >
                  @{p.user?.username}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Post-Event Reviews Section */}
      <div className="activity-comments glass">
        <CommentSection
          targetType="activities"
          targetId={id!}
          comments={comments}
          total={commentTotal}
          hasMore={commentHasMore}
          onRefresh={loadComments}
          onLoadMore={loadMoreComments}
          isEnded={vm.isPast || (activity.end_time ? new Date() >= new Date(activity.end_time) : false)}
          canReview={isHost || Boolean(myRequest?.attendance_confirmed)}
          restrictionMessage="Chức năng đánh giá chỉ dành cho sinh viên đã tham gia và được điểm danh tại hoạt động."
        />
      </div>

      {/* Host QR Code Modal */}
      {showHostQrModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-md animate-fade-in">
          <div className="bg-white p-6 rounded-3xl max-w-sm w-full shadow-2xl flex flex-col items-center text-center">
            <div className="flex items-center justify-between w-full mb-2">
              <h3 className="text-lg font-bold text-slate-900">Quét mã để điểm danh</h3>
              <button
                onClick={() => setShowHostQrModal(false)}
                className="text-gray-400 hover:text-gray-600 p-1 cursor-pointer transition-colors"
                aria-label="Đóng"
              >
                <X size={20} />
              </button>
            </div>

            <div className="p-3 bg-white rounded-2xl shadow-sm flex items-center justify-center">
              {hostQrData ? (
                <img
                  src={`https://api.qrserver.com/v1/create-qr-code/?size=240x240&data=${encodeURIComponent(
                    `${window.location.origin}/activities/${id}?checkin_code=${hostQrData.rotating_token}`
                  )}`}
                  alt="Check-in QR Code"
                  className="w-56 h-56 rounded-lg"
                />
              ) : (
                <div className="w-56 h-56 flex items-center justify-center text-gray-400">Đang tạo mã...</div>
              )}
            </div>

            {/* Rotating token countdown */}
            <div className="flex items-center gap-2 mt-4 px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-800 text-xs font-semibold shadow-sm">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
              <span>Mã đổi sau: {qrCountdown}s</span>
            </div>

            {/* Token display */}
            <div className="mt-3">
              <span className="text-xs text-[var(--color-text-secondary)] uppercase tracking-wider block">Mã điểm danh trực tiếp:</span>
              <div className="text-3xl font-black tracking-widest text-indigo-600 mt-1 font-mono">
                {hostQrData?.rotating_token || '------'}
              </div>
            </div>

            {/* Live attendance count */}
            <div className="flex items-center justify-between w-full px-3.5 py-2 mt-3.5 rounded-2xl bg-slate-50 text-xs shadow-2xs">
              <span className="flex items-center gap-1.5 text-slate-500 font-medium">
                <Users size={14} className="text-indigo-600" />
                Tiến độ điểm danh:
              </span>
              <span className="font-bold text-slate-800">
                <span className="text-emerald-600 font-extrabold">{currentAttendedCount}</span> / {currentTotalApproved} đã có mặt
              </span>
            </div>

            <Button
              variant="secondary"
              fullWidth
              className="mt-4 !border-0 shadow-sm hover:shadow-md bg-white hover:bg-slate-50 font-semibold"
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
          onClose={() => {
            setShowCheckInModal(false);
            setAutoCheckInCode(null);
          }}
          onSuccess={() => {
            loadData();
          }}
          activityId={id}
          activityTitle={activity.title}
          checkInRadius={activity.check_in_radius || 200}
          trophyName={activity.trophy?.name}
          trophyPoints={activity.trophy?.points}
          initialCode={autoCheckInCode || ''}
          autoSubmit={!!autoCheckInCode}
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

      {/* Manage Participants Modal (Host Only) */}
      {showParticipantsModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn"
          onClick={() => setShowParticipantsModal(false)}
        >
          <div
            className="bg-[var(--color-bg-primary)] rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header - No hlines */}
            <div className="flex items-center justify-between p-5 pb-3">
              <div>
                <h3 className="text-lg font-bold text-[var(--color-text-primary)] flex items-center gap-2">
                  <Users size={20} className="text-primary-500" /> Quản lý người tham gia
                </h3>
                <p className="text-xs text-[var(--color-text-secondary)] mt-0.5">
                  Tổng cộng: {activity.current_participants} / {activity.max_participants} người tham gia
                </p>
              </div>
              <div className="flex items-center gap-2">
                {canExport && (
                  <button
                    type="button"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-primary-600 bg-primary-50 hover:bg-primary-100 rounded-lg transition-colors border border-primary-200 disabled:opacity-50 cursor-pointer"
                    disabled={isExportingCsv}
                    onClick={handleExportCsv}
                    title="Xuất danh sách đăng ký ra file CSV UTF-8"
                  >
                    <Download size={14} className={isExportingCsv ? 'animate-spin' : ''} />
                    <span>{isExportingCsv ? 'Đang xuất...' : 'Xuất danh sách CSV'}</span>
                  </button>
                )}
                <button
                  type="button"
                  className="p-1.5 rounded-lg text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-elevated)] transition-colors"
                  onClick={() => setShowParticipantsModal(false)}
                >
                  <X size={20} />
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="p-5 pt-2 overflow-y-auto space-y-3">
              {/* Host row - No avatar, shadow instead of border */}
              <div className="flex items-center justify-between p-3.5 px-4 rounded-xl bg-primary-500/10 shadow-sm">
                <div>
                  <div className="flex items-center gap-2">
                    <Link
                      to={`/profile/${activity.host_id}`}
                      className="font-semibold text-primary-600 hover:underline"
                    >
                      @{activity.host?.username}
                    </Link>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-primary-600 text-white font-semibold">
                      Host
                    </span>
                  </div>
                  {activity.host?.full_name && (
                    <p className="text-xs text-[var(--color-text-secondary)] mt-0.5">{activity.host.full_name}</p>
                  )}
                </div>
              </div>

              {/* Non-host participants - No avatar, shadow instead of border */}
              {allDisplayParticipants.length === 0 ? (
                <div className="text-center py-8 text-[var(--color-text-secondary)] text-sm">
                  Chưa có người tham gia nào khác.
                </div>
              ) : (
                allDisplayParticipants.map((p) => (
                  <div
                    key={p.id}
                    className="flex items-center justify-between p-3.5 px-4 rounded-xl bg-[var(--color-bg-elevated)] shadow-sm hover:shadow transition-shadow"
                  >
                    <div className="min-w-0 pr-3">
                      <Link
                        to={`/profile/${p.user_id}`}
                        className="font-semibold text-[var(--color-text-primary)] hover:underline truncate block"
                      >
                        @{p.user?.username}
                      </Link>
                      {p.user?.full_name && (
                        <p className="text-xs text-[var(--color-text-secondary)] truncate mt-0.5">
                          {p.user.full_name}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-3 flex-shrink-0">
                      {/* Switch Có mặt / Vắng */}
                      <button
                        type="button"
                        role="switch"
                        aria-checked={p.attendance_confirmed}
                        disabled={updatingAttendanceUserId === p.user_id}
                        onClick={() => handleSetAttendance(p.user_id, !p.attendance_confirmed)}
                        className="attendance-switch-control"
                        title={p.attendance_confirmed ? 'Đang có mặt (Nhấn để chuyển sang Vắng)' : 'Đang vắng (Nhấn để điểm danh Có mặt)'}
                      >
                        <span className={`attendance-switch-track ${p.attendance_confirmed ? 'is-checked' : ''}`}>
                          <span className="attendance-switch-thumb" />
                        </span>
                        <span className={`attendance-switch-label ${p.attendance_confirmed ? 'is-present' : 'is-absent'}`}>
                          {updatingAttendanceUserId === p.user_id ? '...' : (p.attendance_confirmed ? 'Có mặt' : 'Vắng')}
                        </span>
                      </button>

                      {/* Nút Xóa (nền đỏ chữ trắng) */}
                      <button
                        type="button"
                        className="btn-participant-action btn-participant-remove"
                        title="Xóa khỏi hoạt động"
                        disabled={removingParticipantUserId === p.user_id}
                        onClick={() => handleRemoveParticipant(p.user_id, p.user?.username || 'user')}
                      >
                        {removingParticipantUserId === p.user_id ? '...' : 'Xóa'}
                      </button>

                      {/* Minh chứng / chứng nhận nếu đã điểm danh */}
                      {p.attendance_confirmed && (
                        <button
                          type="button"
                          className="p-1.5 rounded-lg bg-[var(--color-bg-secondary)] hover:bg-[var(--color-bg-primary)] text-[var(--color-text-secondary)] shadow-sm transition-colors"
                          title="Xem minh chứng / chứng nhận"
                          onClick={() => {
                            setCertificateTargetUserId(p.user_id);
                            setShowCertificateModal(true);
                          }}
                        >
                          <FileText size={15} />
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Modal Footer - No hlines */}
            <div className="p-4 pt-2 flex justify-end">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setShowParticipantsModal(false)}
              >
                Đóng
              </Button>
            </div>
          </div>
        </div>
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

      {/* Invite Co-Host Modal */}
      {showInviteCoHostModal && (
        <div className="modal-overlay">
          <div className="group-modal-container" style={{ maxWidth: 520 }}>
            <div className="group-modal-header">
              <div className="group-modal-header-info">
                <div className="cohost-modal-icon-badge">
                  <UserPlus className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="group-modal-title">Mời nhóm đồng tổ chức hoạt động</h2>
                </div>
              </div>
              <button
                onClick={() => {
                  setShowInviteCoHostModal(false);
                  setCoHostSearchQuery('');
                  setCoHostSearchResults([]);
                  setCoHostMessage('');
                }}
                className="group-modal-close-btn"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="group-modal-body">
              {/* Search input */}
              <div className="cohost-search-box">
                <Search className="w-4 h-4" style={{ color: 'var(--color-text-tertiary)' }} />
                <input
                  type="text"
                  placeholder="Tìm kiếm nhóm..."
                  value={coHostSearchQuery}
                  onChange={(e) => {
                    const q = e.target.value;
                    setCoHostSearchQuery(q);
                    fetchCoHostCandidates(q);
                  }}
                  className="cohost-search-input"
                />
              </div>

              {/* Optional message */}
              <div style={{ marginTop: 'var(--space-3)' }}>
                <label className="cohost-message-label">Lời nhắn (tùy chọn)</label>
                <textarea
                  value={coHostMessage}
                  onChange={(e) => setCoHostMessage(e.target.value)}
                  placeholder="Ví dụ: Kính mời nhóm cùng phối hợp tổ chức..."
                  className="cohost-message-textarea"
                  rows={2}
                />
              </div>

              {/* Results */}
              <div className="cohost-results" style={{ marginTop: 'var(--space-4)' }}>
                {coHostSearchLoading ? (
                  <div className="cohost-empty-state">
                    <Loader2 className="w-6 h-6 animate-spin" style={{ color: 'var(--color-primary)' }} />
                    <p className="cohost-empty-desc" style={{ marginTop: 8 }}>Đang tìm kiếm...</p>
                  </div>
                ) : coHostSearchResults.length > 0 ? (
                  <div className="group-modal-list">
                    {coHostSearchResults.map((g) => (
                      <div key={g.id} className="cohost-group-row">
                        <div className="cohost-group-info">
                          <div className="cohost-group-avatar">
                            {g.name.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <div className="cohost-group-name">{g.name}</div>
                            <div className="cohost-group-meta">
                              {g.member_count} thành viên
                              {g.privacy === 'private' && (
                                <span className="cohost-private-tag"> • Riêng tư</span>
                              )}
                            </div>
                          </div>
                        </div>
                        <button
                          className="group-modal-btn group-modal-btn--primary"
                          disabled={invitingGroupId === g.id}
                          onClick={async () => {
                            if (!id) return;
                            setInvitingGroupId(g.id);
                            try {
                              await groupsApi.inviteCoHost(id, {
                                invited_group_id: g.id,
                                message: coHostMessage.trim() || undefined,
                              });
                              toast.success(`Đã gửi lời mời đồng tổ chức đến ${g.name}`);
                              // Remove from results and refresh invitations
                              setCoHostSearchResults(prev => prev.filter(r => r.id !== g.id));
                              await fetchCoHostInvitations();
                            } catch (err: any) {
                              toast.error(err?.response?.data?.detail || 'Không thể gửi lời mời');
                            } finally {
                              setInvitingGroupId(null);
                            }
                          }}
                        >
                          {invitingGroupId === g.id ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <UserPlus className="w-3.5 h-3.5" />
                          )}
                          Mời
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="cohost-empty-state">
                    <div className="cohost-empty-icon-wrap">
                      <Building2 className="w-5 h-5" />
                    </div>
                    <p className="cohost-empty-title">Không tìm thấy nhóm nào</p>
                    <p className="cohost-empty-desc">
                      {coHostSearchQuery.trim()
                        ? 'Thử từ khóa khác để tìm kiếm'
                        : 'Hiện chưa có nhóm khả dụng để mời'}
                    </p>
                  </div>
                )}
              </div>

              {/* Sent invitations list */}
              <div className="cohost-sent-section mt-5 pt-4 border-t border-slate-100">
                <div className="flex items-center justify-between mb-2.5">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Lời mời đã gửi ({coHostInvitations.length})
                  </h4>
                  {coHostInvitationsLoading && <Loader2 size={13} className="animate-spin text-slate-400" />}
                </div>

                {coHostInvitations.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">Chưa có lời mời đồng tổ chức nào được gửi cho hoạt động này.</p>
                ) : (
                  <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                    {coHostInvitations.map(inv => {
                      const isPending = inv.status === 'pending';
                      const isAccepted = inv.status === 'accepted';
                      return (
                        <div key={inv.id} className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 shadow-sm">
                          <div className="flex items-center gap-2.5">
                            <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-xs">
                              {inv.invited_group_name ? inv.invited_group_name.charAt(0).toUpperCase() : 'G'}
                            </div>
                            <div>
                              <div className="text-xs font-semibold text-slate-800">{inv.invited_group_name || 'Nhóm'}</div>
                              {inv.message && <div className="text-[11px] text-slate-400 truncate max-w-[200px]">"{inv.message}"</div>}
                            </div>
                          </div>
                          <div>
                            {isPending && (
                              <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 shadow-sm">
                                <Clock size={11} /> Đang đợi chấp nhận
                              </span>
                            )}
                            {isAccepted && (
                              <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 shadow-sm">
                                <CheckCircle2 size={11} /> Đã chấp thuận
                              </span>
                            )}
                            {!isPending && !isAccepted && (
                              <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 shadow-sm">
                                Đã từ chối
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>

            <div className="group-modal-footer">
              <button
                onClick={() => {
                  setShowInviteCoHostModal(false);
                  setCoHostSearchQuery('');
                  setCoHostSearchResults([]);
                  setCoHostMessage('');
                }}
                className="group-modal-btn group-modal-btn--ghost"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Form Response Review Modal (Feature B) */}
      {selectedReviewRequest && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn"
          onClick={() => setSelectedReviewRequest(null)}
        >
          <div
            className="bg-[var(--color-bg-primary)] rounded-2xl w-full max-w-lg max-h-[85vh] flex flex-col shadow-2xl overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-5 pb-3">
              <div>
                <h3 className="text-lg font-bold text-[var(--color-text-primary)] flex items-center gap-2">
                  <FileText size={20} className="text-primary-500" /> Câu trả lời biểu mẫu
                </h3>
                <p className="text-xs text-[var(--color-text-secondary)] mt-0.5">
                  Người đăng ký: <span className="font-semibold text-[var(--color-text-primary)]">@{selectedReviewRequest.user?.username}</span>
                  {selectedReviewRequest.user?.full_name && ` (${selectedReviewRequest.user.full_name})`}
                </p>
              </div>
              <button
                type="button"
                className="p-1.5 rounded-lg text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-elevated)] transition-colors"
                onClick={() => setSelectedReviewRequest(null)}
              >
                <X size={20} />
              </button>
            </div>

            {/* Content */}
            <div className="p-5 pt-2 overflow-y-auto space-y-4">
              {selectedReviewRequest.message && (
                <div className="p-3.5 rounded-xl bg-slate-50 shadow-sm">
                  <div className="text-xs font-semibold text-slate-500 mb-1">Lời nhắn đính kèm:</div>
                  <div className="text-sm text-slate-700 italic">"{selectedReviewRequest.message}"</div>
                </div>
              )}

              {activity.custom_form?.fields && activity.custom_form.fields.length > 0 ? (
                <div className="space-y-3">
                  {[...activity.custom_form.fields]
                    .sort((a, b) => a.order - b.order)
                    .map((field) => {
                      const answer = getFormFieldResponse(field, selectedReviewRequest.form_responses);
                      return (
                        <div
                          key={field.id}
                          className="p-3.5 rounded-xl bg-[var(--color-bg-elevated)] shadow-sm"
                        >
                          <div className="text-xs font-semibold text-[var(--color-text-secondary)] mb-1 flex items-center gap-1">
                            <span>{field.label}</span>
                            {field.is_required && <span className="text-red-500">*</span>}
                          </div>
                          <div className="text-sm font-medium text-[var(--color-text-primary)] whitespace-pre-wrap break-words">
                            {answer}
                          </div>
                        </div>
                      );
                    })}
                </div>
              ) : selectedReviewRequest.form_responses && Object.keys(selectedReviewRequest.form_responses).length > 0 ? (
                <div className="space-y-3">
                  {Object.entries(selectedReviewRequest.form_responses).map(([key, val]) => (
                    <div
                      key={key}
                      className="p-3.5 rounded-xl bg-[var(--color-bg-elevated)] shadow-sm"
                    >
                      <div className="text-xs font-semibold text-[var(--color-text-secondary)] mb-1">
                        {key}
                      </div>
                      <div className="text-sm font-medium text-[var(--color-text-primary)] whitespace-pre-wrap break-words">
                        {typeof val === 'boolean' ? (val ? 'Có' : 'Không') : String(val ?? 'Chưa trả lời')}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-sm text-[var(--color-text-secondary)]">
                  Người dùng không để lại câu trả lời biểu mẫu nào.
                </div>
              )}
            </div>

            {/* Footer with action buttons */}
            <div className="p-4 pt-3 flex items-center justify-between border-t border-[var(--color-border-subtle)] bg-[var(--color-bg-secondary)]">
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="primary"
                  onClick={async () => {
                    const reqId = selectedReviewRequest.id;
                    setSelectedReviewRequest(null);
                    await handleRespond(reqId, 'approved');
                  }}
                  disabled={isFull}
                >
                  Phê duyệt
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={async () => {
                    const reqId = selectedReviewRequest.id;
                    setSelectedReviewRequest(null);
                    await handleRespond(reqId, 'declined');
                  }}
                >
                  Từ chối
                </Button>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedReviewRequest(null)}
              >
                Đóng
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
