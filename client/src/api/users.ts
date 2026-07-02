import { api } from './client';

export interface UserProfile {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  bio: string | null;
  university: string | null;
  role: string;
  created_at: string;
}

export interface UserUpdate {
  full_name?: string;
  bio?: string;
  university?: string;
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

export const usersApi = {
  getMe: () => api.get<UserProfile>('/users/me'),

  updateMe: (data: UserUpdate) =>
    api.patch<UserProfile>('/users/me', data),

  getUser: (userId: string) => api.get<UserProfile>(`/users/${userId}`),
  
  followUser: (userId: string) => api.post(`/users/${userId}/follow`),
  
  unfollowUser: (userId: string) => api.delete(`/users/${userId}/follow`),
  
  getFollowStatus: (userId: string) => api.get<FollowStatus>(`/users/${userId}/follow-status`),
  
  getFollowers: (userId: string, params?: { limit?: number; offset?: number }) => 
    api.get<UserFollowResponse>(`/users/${userId}/followers?limit=${params?.limit || 20}&offset=${params?.offset || 0}`),
    
  getFollowing: (userId: string, params?: { limit?: number; offset?: number }) => 
    api.get<UserFollowResponse>(`/users/${userId}/following?limit=${params?.limit || 20}&offset=${params?.offset || 0}`),
};
