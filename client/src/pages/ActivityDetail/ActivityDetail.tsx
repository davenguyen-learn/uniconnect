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
import './ActivityDetail.css';

export default function ActivityDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const toast = useToast();

  const [activity, setActivity] = useState<ActivityResponse | null>(null);
  const [requests, setRequests] = useState<JoinRequestResponse[]>([]);
  const [myRequest, setMyRequest] = useState<JoinRequestResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [requestMessage, setRequestMessage] = useState('');

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
      toast.error('Failed to load activity details');
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
      const req = await participationApi.requestToJoin(id, data);
      setMyRequest(req);
      if (activity?.require_approval) {
        toast.success('Join request sent successfully!');
      } else {
        toast.success('Successfully joined the activity!');
        loadData(); // Refresh to update participant count
      }
    } catch (error) {
      toast.error('Failed to send request. The activity might be full.');
    }
  }

  async function handleCancelRequest() {
    if (!myRequest) return;
    try {
      await participationApi.cancel(myRequest.id);
      setMyRequest(null);
      toast.success('Request cancelled');
    } catch (error) {
      toast.error('Failed to cancel request');
    }
  }

  async function handleRespond(requestId: string, status: 'approved' | 'declined') {
    try {
      if (status === 'approved') {
        await participationApi.approve(requestId);
      } else {
        await participationApi.decline(requestId);
      }
      toast.success(`Request ${status}`);
      // Refresh data to update participant count and remove request from list
      loadData();
    } catch (error) {
      toast.error(`Failed to ${status} request`);
    }
  }

  async function handleLeaveActivity() {
    if (!id) return;
    try {
      await participationApi.leaveActivity(id);
      setMyRequest(null);
      toast.success('You have left the activity');
      loadData(); // Refresh participant count
    } catch (error) {
      toast.error('Failed to leave activity');
    }
  }

  async function handleDeleteActivity() {
    if (!id) return;
    const confirm = window.confirm('Are you sure you want to delete this activity?');
    if (!confirm) return;
    
    try {
      await activitiesApi.delete(id);
      toast.success('Activity deleted');
      navigate('/dashboard');
    } catch (error) {
      toast.error('Failed to delete activity');
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
      toast.error('Failed to refresh comments');
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
      toast.error('Failed to load more comments');
    }
  }

  if (loading || !activity) {
    return <div className="activity-detail-loading">Loading...</div>;
  }

  const isHost = user?.id === activity.host_id;
  const isFull = activity.current_participants >= activity.max_participants;

  return (
    <div className="activity-detail-container">
      <div className="activity-header glass">
        <div className="category-badge">{activity.category || 'General'}</div>
        <h1 className="activity-title">{activity.title}</h1>
        <div className="activity-meta">
          <span>Hosted by <Link to={`/profile/${activity.host_id}`} style={{color: 'inherit', textDecoration: 'underline'}}>@{activity.host?.username}</Link></span>
          <span className="meta-dot">•</span>
          <span>{new Date(activity.start_time).toLocaleString()}</span>
        </div>
        <div className="activity-header-actions">
          <LikeButton targetType="activities" targetId={id!} initialLiked={liked} initialCount={likeCount} />
        </div>
      </div>

      <div className="activity-content-grid">
        <div className="activity-main glass">
          <h3>Description</h3>
          <p className="activity-description">{activity.description}</p>

          <div className="activity-stats">
            <div className="stat-box">
              <span className="stat-label">Location</span>
              <span className="stat-value" style={{ wordBreak: 'break-word' }}>{activity.location_name || 'TBD'}</span>
            </div>
            <div className="stat-box">
              <span className="stat-label">Participants</span>
              <span className="stat-value">
                {activity.current_participants} / {activity.max_participants}
              </span>
            </div>
            <div className="stat-box">
              <span className="stat-label">Privacy</span>
              <span className="stat-value">{activity.privacy}</span>
            </div>
            <div className="stat-box">
              <span className="stat-label">Status</span>
              <span className="stat-value">
                {isFull ? 'Full' : 'Open'}
              </span>
            </div>
          </div>
        </div>

        <div className="activity-sidebar glass">
          {isHost ? (
            <div className="host-management">
              <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
                <Button 
                  variant="secondary" 
                  fullWidth 
                  onClick={() => navigate(`/activities/${id}/edit`)}
                >
                  Edit
                </Button>
                <Button 
                  fullWidth 
                  onClick={handleDeleteActivity}
                  style={{ backgroundColor: 'rgba(239, 68, 68, 0.2)', color: '#f87171', border: '1px solid rgba(239, 68, 68, 0.3)' }}
                >
                  Delete
                </Button>
              </div>

              <h3>Join Requests</h3>
              {requests.length === 0 ? (
                <p className="no-requests">No pending requests.</p>
              ) : (
                <div className="request-list">
                  {requests.map((req) => (
                    <div key={req.id} className="request-item">
                      <div className="request-user">
                        <strong>@{req.user?.username}</strong> wants to join
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
                          Approve
                        </Button>
                        <Button 
                          size="sm" 
                          variant="secondary" 
                          onClick={() => handleRespond(req.id, 'declined')}
                        >
                          Decline
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
                  <h3>Your Request</h3>
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
                      Cancel Request
                    </Button>
                  )}
                  {myRequest.status === 'approved' && (
                    <>
                      <p className="success-message mt-4">You're in! Check the exact location on the map.</p>
                      <Button 
                        variant="secondary" 
                        fullWidth 
                        className="mt-4"
                        onClick={handleLeaveActivity}
                      >
                        Leave Activity
                      </Button>
                    </>
                  )}
                </div>
              ) : (
                <form onSubmit={handleJoinRequest} className="join-form">
                  <h3>{activity.require_approval ? 'Request to Join' : 'Join Activity'}</h3>
                  {activity.require_approval && (
                    <>
                      <p className="join-hint">
                        Let the host know why you want to join (optional).
                      </p>
                      <textarea
                        value={requestMessage}
                        onChange={(e) => setRequestMessage(e.target.value)}
                        placeholder="Hi! I'd love to join because..."
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
                    {isFull ? 'Activity Full' : (activity.require_approval ? 'Send Request' : 'Join Activity')}
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
