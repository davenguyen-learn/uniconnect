import { api } from './client';

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  full_name?: string;
  university?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export const authApi = {
  register: (data: RegisterRequest) =>
    api.post<TokenResponse>('/auth/register', data),

  login: (data: LoginRequest) =>
    api.post<TokenResponse>('/auth/login', data),
};
