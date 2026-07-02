import { api } from './client';
import type { ActivityResponse } from './activities';

export interface ChatMessage {
  role: 'user' | 'model';
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  user_lat?: number;
  user_lng?: number;
}

export interface ChatResponse {
  reply: string;
  recommended_activities?: ActivityResponse[];
}

export const chatApi = {
  chatWithBot: (data: ChatRequest) => 
    api.post<ChatResponse>('/chat', data),
};
