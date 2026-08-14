import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { activitiesApi, type ActivityResponse } from '../../api/activities';
import { participationApi, type JoinRequestResponse, type JoinRequestCreate } from '../../api/participation';
import { interactionsApi, type CommentResponse } from '../../api/interactions';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../components/Toast/ToastContext';
import Button from '../../components/Button/Button';
import LikeButton from '../../components/LikeButton/LikeButton';
import CommentSection from '../../components/CommentSection/CommentSection';
import { ReportModal } from '../../components/ReportModal/ReportModal';
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

  // Interactions state
  const [liked, setLiked] = useState(false);
  const [likeCount, setLikeCount] = useState(0);
  const [comments, setComments] = useState<CommentResponse[]>([]);
  const [commentTotal, setCommentTotal] = useState(0);
  const [commentHasMore, setCommentHasMore] = useState(false);
  const [commentOffset, setCommentOffset] = useState(0);
  const COMMENT_LIMIT = 20;

  useEffect(() => {
    if (id) {
      loadData();
    }
  }, [id]);

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
      }

      // Fetch participants list for everyone
      try {
        const parts = await participationApi.listParticipants(id!);
        setParticipants(parts);
      } catch {
        // ignore
      }

      // Load interactions data
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

  async function handleJoinRequest(e: React.FormEvent) {
    e.preventDefault();
    if (!id) return;
    try {
      const data: JoinRequestCreate = {};
      if (requestMessage.trim()) {
        data.message = requestMessage.trim();
      }
      if (Object.keys(formResponses).length > 0) {
        data.form_responses = formResponses;
      }
      const req = await participationApi.requestToJoin(id, data);
      setMyRequest(req);
      if (activity?.require_approval) {
        toast.success('Đã gửi yêu cầu tham gia thành công!');
      } else {
        toast.success('Đã tham gia hoạt động thành công!');
        loadData(); // Refresh to update participant count
      }
    } catch (error) {
      toast.error('Không thể gửi yêu cầu. Hoạt động có thể đã đầy.');
    }
  }

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

  return (
    <div className="activity-detail-container">
      <div className="activity-header glass">
        <div className="category-badge">{activity.category || 'Chung'}</div>
        <h1 className="activity-title">{activity.title}</h1>
        <div className="activity-meta">
          <span>Được tổ chức bởi <Link to={`/profile/${activity.host_id}`} className="activity-host-link">@{activity.host?.username}</Link></span>
          <span className="meta-dot">•</span>
          <span>{new Date(activity.start_time).toLocaleString('vi-VN')}</span>
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
              <h4>
                🔓 Nội dung dành cho thành viên
              </h4>
              <p className="text-pre-wrap">{activity.private_description}</p>
            </div>
          ) : activity.privacy === 'private' && !isHost && (
            <div className="callout callout--muted">
              🔒 Thông tin riêng tư (Chỉ được tiết lộ cho người tổ chức và người tham gia được phê duyệt)
            </div>
          )}

          <div className="activity-stats">
            <div className="stat-box">
              <span className="stat-label">Địa điểm</span>
              <span className="stat-value">{activity.location_name || 'TBD'}</span>
            </div>
            <div className="stat-box">
              <span className="stat-label">Người tham gia</span>
              <span className="stat-value">
                {activity.current_participants} / {activity.max_participants}
              </span>
            </div>
            <div className="stat-box">
              <span className="stat-label">Quyền riêng tư</span>
              <span className="stat-value">{activity.privacy}</span>
            </div>
            <div className="stat-box">
              <span className="stat-label">Trạng thái</span>
              <span className="stat-value">
                {isFull ? 'Đã đầy' : 'Đang mở'}
              </span>
            </div>
          </div>

          {participants.length > 0 && (
            <div className="participants-section">
              <h3>Người tham gia</h3>
              <div className="participants-list">
                <div 
                  className="participant-chip participant-chip--host"
                  title="Host"
                >
                  ⭐ @{activity.host?.username}
                </div>
                {participants.filter(p => p.user?.username !== activity.host?.username).map(p => (
                  <div 
                    key={p.id} 
                    className="participant-chip"
                  >
                    @{p.user?.username}
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
              <div className="host-actions">
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
                  <h3>{activity.require_approval ? 'Yêu cầu tham gia' : 'Tham gia hoạt động'}</h3>
                  
                  {activity.custom_form && activity.custom_form.fields.length > 0 && (
                    <div className="custom-form-section">
                      <h4>{activity.custom_form.title || 'Thông tin bắt buộc'}</h4>
                      {activity.custom_form.description && <p className="custom-form-hint">{activity.custom_form.description}</p>}
                      
                      {activity.custom_form.fields.map(field => (
                        <div key={field.id} className="custom-form-field">
                          <label className="custom-form-field-label">
                            {field.label} {field.is_required && <span className="required">*</span>}
                          </label>
                          {field.field_type === 'checkbox' ? (
                            <input 
                              type="checkbox" 
                              required={field.is_required}
                              onChange={(e) => setFormResponses(prev => ({ ...prev, [field.id!]: e.target.checked }))}
                            />
                          ) : (
                            <input 
                              type={field.field_type === 'number' ? 'number' : 'text'}
                              className="form-input"
                              required={field.is_required}
                              onChange={(e) => setFormResponses(prev => ({ ...prev, [field.id!]: field.field_type === 'number' ? Number(e.target.value) : e.target.value }))}
                            />
                          )}
                        </div>
                      ))}
                    </div>
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
                    disabled={isFull}
                  >
                    {isFull ? 'Hoạt động đã đầy' : (activity.require_approval ? 'Gửi yêu cầu' : 'Tham gia hoạt động')}
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
    </div>
  );
}
