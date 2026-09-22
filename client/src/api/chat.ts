import { api } from './client';
import type { ActivityResponse } from './activities';

export interface ChatEventCardDTO {
  activity_id: string;
  title: string;
  start_time: string;
  end_time: string;
  meeting_location?: string;
  location_name: string;
  social_work_days?: number | null;
  distance_meters?: number | null;
  distance_status: 'nearby' | 'moderate' | 'far' | 'unknown';
  conflict_status: 'none' | 'soft_conflict' | 'hard_conflict';
  registration_status: 'available' | 'registered' | 'capacity_full' | 'deadline_passed';
  eligibility_status: 'eligible' | 'not_eligible';
}

export interface ChatMessageDTO {
  id: string;
  role: 'user' | 'assistant' | 'model';
  content: string;
  cards?: ChatEventCardDTO[] | null;
  created_at: string;
}

export interface ChatRequest {
  conversation_id?: string;
  message?: string;
  messages?: { role: string; content: string }[];
  user_lat?: number;
  user_lng?: number;
}

export interface ChatResponse {
  conversation_id: string;
  message: ChatMessageDTO;
  reply: string;
  recommended_activities?: ActivityResponse[] | null;
  suggestions: string[];
}

export const chatApi = {
  chatWithBot: (data: ChatRequest) => 
    api.post<ChatResponse>('/chat', data),
};
