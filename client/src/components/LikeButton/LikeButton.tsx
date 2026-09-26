import { useState, useEffect } from 'react';
import { interactionsApi } from '../../api/interactions';
import { useToast } from '../Toast/ToastContext';
import './LikeButton.css';

interface LikeButtonProps {
  targetType: 'activities' | 'documents';
  targetId: string;
  initialLiked?: boolean;
  initialCount?: number;
  autoFetch?: boolean;
  compact?: boolean;
}

export default function LikeButton({
  targetType,
  targetId,
  initialLiked = false,
  initialCount = 0,
  autoFetch = false,
  compact = false,
}: LikeButtonProps) {
  const [liked, setLiked] = useState(initialLiked);
  const [count, setCount] = useState(initialCount);
  const [animating, setAnimating] = useState(false);
  const toast = useToast();

  useEffect(() => {
    setLiked(initialLiked);
  }, [initialLiked]);

  useEffect(() => {
    setCount(initialCount);
  }, [initialCount]);

  useEffect(() => {
    if (!autoFetch) return;
    const token = localStorage.getItem('token');
    if (!token) return;

    let isMounted = true;
    interactionsApi
      .getLikeStatus(targetType, targetId)
      .then((result) => {
        if (isMounted) {
          setLiked(result.liked);
          setCount(result.total_likes);
        }
      })
      .catch(() => {});

    return () => {
      isMounted = false;
    };
  }, [autoFetch, targetType, targetId]);

  async function handleToggle(e: React.MouseEvent) {
    e.stopPropagation();

    const token = localStorage.getItem('token');
    if (!token) {
      toast.info('Vui lòng đăng nhập để thích hoạt động');
      return;
    }

    // Optimistic update
    const wasLiked = liked;
    const prevCount = count;
    setLiked(!wasLiked);
    setCount(wasLiked ? Math.max(0, prevCount - 1) : prevCount + 1);

    if (!wasLiked) {
      setAnimating(true);
      setTimeout(() => setAnimating(false), 600);
    }

    try {
      const result = await interactionsApi.toggleLike(targetType, targetId);
      setLiked(result.liked);
      setCount(result.total_likes);
    } catch {
      // Revert on error
      setLiked(wasLiked);
      setCount(prevCount);
      toast.error('Không thể cập nhật lượt thích');
    }
  }

  return (
    <button
      type="button"
      className={`like-button ${compact ? 'like-button--compact' : ''} ${liked ? 'liked' : ''} ${animating ? 'like-animating' : ''}`}
      onClick={handleToggle}
      aria-label={liked ? 'Bỏ thích hoạt động' : 'Thích hoạt động'}
      title={liked ? 'Bỏ thích' : 'Thích'}
    >
      <span className="like-icon">
        {liked ? (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
          </svg>
        ) : (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
          </svg>
        )}
      </span>
      {count > 0 && <span className="like-count">{count}</span>}
    </button>
  );
}
