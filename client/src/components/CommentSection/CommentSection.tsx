import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../Toast/ToastContext';
import { interactionsApi, type CommentResponse } from '../../api/interactions';
import './CommentSection.css';

interface CommentItemProps {
  comment: CommentResponse;
  currentUserId: string | undefined;
  onReply: (parentId: string) => void;
  onDelete: (commentId: string) => void;
  onUpdate: (commentId: string, content: string) => void;
  isReply?: boolean;
}

function CommentItem({ comment, currentUserId, onReply, onDelete, onUpdate, isReply }: CommentItemProps) {
  const [editing, setEditing] = useState(false);
  const [editContent, setEditContent] = useState(comment.content);

  const isAuthor = currentUserId === comment.user_id;
  const timeAgo = getTimeAgo(comment.created_at);
  const wasEdited = comment.created_at !== comment.updated_at;

  function handleSaveEdit() {
    if (editContent.trim() && editContent.trim() !== comment.content) {
      onUpdate(comment.id, editContent.trim());
    }
    setEditing(false);
  }

  function handleCancelEdit() {
    setEditContent(comment.content);
    setEditing(false);
  }

  return (
    <div className={`comment-item ${isReply ? 'comment-reply' : ''} ${comment.is_deleted ? 'comment-deleted' : ''}`}>
      <div className="comment-avatar">
        {comment.is_deleted ? '🗑' : (comment.user?.username?.[0]?.toUpperCase() || '?')}
      </div>
      <div className="comment-body">
        <div className="comment-header">
          <span className="comment-author">
            {comment.is_deleted ? 'Deleted' : `@${comment.user?.username || 'unknown'}`}
          </span>
          <span className="comment-time">
            {timeAgo}
            {wasEdited && !comment.is_deleted && <span className="comment-edited"> (edited)</span>}
          </span>
        </div>

        {editing ? (
          <div className="comment-edit-form">
            <textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              className="comment-edit-input"
              rows={3}
              maxLength={1000}
              autoFocus
            />
            <div className="comment-edit-actions">
              <button className="comment-btn comment-btn-save" onClick={handleSaveEdit}>
                Save
              </button>
              <button className="comment-btn comment-btn-cancel" onClick={handleCancelEdit}>
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <p className="comment-content">{comment.content}</p>
        )}

        {!comment.is_deleted && !editing && (
          <div className="comment-actions">
            {!isReply && (
              <button className="comment-btn" onClick={() => onReply(comment.id)}>
                Reply
              </button>
            )}
            {isAuthor && (
              <>
                <button className="comment-btn" onClick={() => setEditing(true)}>
                  Edit
                </button>
                <button className="comment-btn comment-btn-danger" onClick={() => onDelete(comment.id)}>
                  Delete
                </button>
              </>
            )}
          </div>
        )}

        {/* Replies */}
        {!isReply && comment.replies && comment.replies.length > 0 && (
          <div className="comment-replies">
            {comment.replies.map((reply) => (
              <CommentItem
                key={reply.id}
                comment={reply}
                currentUserId={currentUserId}
                onReply={onReply}
                onDelete={onDelete}
                onUpdate={onUpdate}
                isReply
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

interface CommentSectionProps {
  targetType: 'activities' | 'documents';
  targetId: string;
  comments: CommentResponse[];
  total: number;
  hasMore: boolean;
  onRefresh: () => void;
  onLoadMore: () => void;
}

export default function CommentSection({
  targetType,
  targetId,
  comments,
  total,
  hasMore,
  onRefresh,
  onLoadMore,
}: CommentSectionProps) {
  const { user } = useAuth();
  const toast = useToast();
  const [newComment, setNewComment] = useState('');
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [replyContent, setReplyContent] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmitComment(e: React.FormEvent) {
    e.preventDefault();
    if (!newComment.trim() || submitting) return;

    setSubmitting(true);
    try {
      await interactionsApi.createComment(targetType, targetId, { content: newComment.trim() });
      setNewComment('');
      onRefresh();
    } catch {
      toast.error('Failed to post comment');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSubmitReply(e: React.FormEvent) {
    e.preventDefault();
    if (!replyContent.trim() || !replyingTo || submitting) return;

    setSubmitting(true);
    try {
      await interactionsApi.createComment(targetType, targetId, {
        content: replyContent.trim(),
        parent_id: replyingTo,
      });
      setReplyContent('');
      setReplyingTo(null);
      onRefresh();
    } catch {
      toast.error('Failed to post reply');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(commentId: string) {
    if (!window.confirm('Delete this comment?')) return;
    try {
      await interactionsApi.deleteComment(commentId);
      onRefresh();
      toast.success('Comment deleted');
    } catch {
      toast.error('Failed to delete comment');
    }
  }

  async function handleUpdate(commentId: string, content: string) {
    try {
      await interactionsApi.updateComment(commentId, { content });
      onRefresh();
    } catch {
      toast.error('Failed to update comment');
    }
  }

  function handleReply(parentId: string) {
    setReplyingTo(replyingTo === parentId ? null : parentId);
    setReplyContent('');
  }

  return (
    <div className="comment-section">
      <h3 className="comment-section-title">
        Comments
        <span className="comment-count-badge">{total}</span>
      </h3>

      {/* New comment form */}
      <form onSubmit={handleSubmitComment} className="comment-form" id="comment-form">
        <div className="comment-form-avatar">
          {user?.username?.[0]?.toUpperCase() || '?'}
        </div>
        <div className="comment-form-input-wrapper">
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Write a comment..."
            className="comment-input"
            rows={3}
            maxLength={1000}
            id="comment-input"
          />
          <div className="comment-form-footer">
            <span className="comment-char-count">
              {newComment.length}/1000
            </span>
            <button
              type="submit"
              className="comment-submit-btn"
              disabled={!newComment.trim() || submitting}
              id="comment-submit-btn"
            >
              {submitting ? 'Posting...' : 'Post'}
            </button>
          </div>
        </div>
      </form>

      {/* Comment list */}
      <div className="comment-list">
        {comments.length === 0 ? (
          <p className="comment-empty">No comments yet. Be the first to comment!</p>
        ) : (
          <>
            {comments.map((comment) => (
              <div key={comment.id}>
                <CommentItem
                  comment={comment}
                  currentUserId={user?.id}
                  onReply={handleReply}
                  onDelete={handleDelete}
                  onUpdate={handleUpdate}
                />

                {/* Reply form (shown inline below the comment being replied to) */}
                {replyingTo === comment.id && (
                  <form onSubmit={handleSubmitReply} className="reply-form">
                    <textarea
                      value={replyContent}
                      onChange={(e) => setReplyContent(e.target.value)}
                      placeholder={`Reply to @${comment.user?.username || 'unknown'}...`}
                      className="comment-input reply-input"
                      rows={2}
                      maxLength={1000}
                      autoFocus
                    />
                    <div className="reply-form-actions">
                      <button
                        type="button"
                        className="comment-btn comment-btn-cancel"
                        onClick={() => setReplyingTo(null)}
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="comment-submit-btn reply-submit-btn"
                        disabled={!replyContent.trim() || submitting}
                      >
                        Reply
                      </button>
                    </div>
                  </form>
                )}
              </div>
            ))}

            {hasMore && (
              <button className="comment-load-more" onClick={onLoadMore} id="load-more-comments">
                Load more comments
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ── Helpers ──

function getTimeAgo(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString();
}
