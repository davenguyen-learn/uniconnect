import { api } from './client';

export interface UserProfile {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  bio: string | null;
  university: string | null;
  interests?: string[];
  role: string;
  is_verified?: boolean;
  created_at: string;
}

export interface UserUpdate {
  full_name?: string;
  bio?: string;
  university?: string;
  interests?: string[];
}

export interface FollowStatus {
  is_following: boolean;
  followers_count: number;
  following_count: number;
}

export interface UserFollowResponse {
  items: UserProfile[];
  total: number;
  has_more: boolean;
}

export interface PublicUserStats {
  user_id: string;
  total_ctxh_days: number;
  total_attended_activities: number;
  total_trophies_count: number;
  total_trophy_points: number;
  rank_title: string;
}

export interface MyUserStats extends PublicUserStats {
  target_ctxh_days: number;
  ctxh_completion_percent: number;
  remaining_ctxh_days: number;
  is_target_reached: boolean;
}

export const usersApi = {
  getMe: () => api.get<UserProfile>('/users/me'),

  getMyStats: () => api.get<MyUserStats>('/users/me/stats'),

  updateMe: (data: UserUpdate) =>
    api.patch<UserProfile>('/users/me', data),

  getUser: (userId: string) => api.get<UserProfile>(`/users/${userId}`),

  getUserStats: (userId: string) => api.get<PublicUserStats>(`/users/${userId}/stats`),
  
  followUser: (userId: string) => api.post(`/users/${userId}/follow`),
  
  unfollowUser: (userId: string) => api.delete(`/users/${userId}/follow`),
  
  getFollowStatus: (userId: string) => api.get<FollowStatus>(`/users/${userId}/follow-status`),
  
  getFollowers: (userId: string, params?: { limit?: number; offset?: number }) => 
    api.get<UserFollowResponse>(`/users/${userId}/followers?limit=${params?.limit || 20}&offset=${params?.offset || 0}`),
    
  getFollowing: (userId: string, params?: { limit?: number; offset?: number }) => 
    api.get<UserFollowResponse>(`/users/${userId}/following?limit=${params?.limit || 20}&offset=${params?.offset || 0}`),
};

