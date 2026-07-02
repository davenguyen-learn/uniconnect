import { api } from './client';

// ── Types ──

export interface UserInfo {
  username: string;
  full_name: string | null;
}

export interface CommentResponse {
  id: string;
  target_type: string;
  target_id: string;
  user_id: string;
  parent_id: string | null;
  content: string;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
  user: UserInfo | null;
  replies: CommentResponse[];
}

export interface CommentListResponse {
  items: CommentResponse[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface CommentCreate {
  content: string;
  parent_id?: string;
}

export interface CommentUpdate {
  content: string;
}

export interface LikeResponse {
  liked: boolean;
  total_likes: number;
}

export interface ContentStatsResponse {
  like_count: number;
  comment_count: number;
  is_liked: boolean;
}

// ── API ──

export const interactionsApi = {
  // Comments
  createComment: (targetType: string, targetId: string, data: CommentCreate) =>
    api.post<CommentResponse>(`/${targetType}/${targetId}/comments`, data),

  listComments: (targetType: string, targetId: string, params?: { limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.offset) query.set('offset', String(params.offset));
    const qs = query.toString();
    return api.get<CommentListResponse>(`/${targetType}/${targetId}/comments${qs ? `?${qs}` : ''}`);
  },

  updateComment: (commentId: string, data: CommentUpdate) =>
    api.patch<CommentResponse>(`/comments/${commentId}`, data),

  deleteComment: (commentId: string) =>
    api.delete<void>(`/comments/${commentId}`),

  // Likes
  toggleLike: (targetType: string, targetId: string) =>
    api.post<LikeResponse>(`/${targetType}/${targetId}/like`),

  getLikeStatus: (targetType: string, targetId: string) =>
    api.get<LikeResponse>(`/${targetType}/${targetId}/like`),

  // Stats
  getStats: (targetType: string, targetId: string) =>
    api.get<ContentStatsResponse>(`/${targetType}/${targetId}/stats`),
};
