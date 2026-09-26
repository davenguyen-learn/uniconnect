import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  Sparkles, 
  X, 
  Send, 
  Maximize2, 
  Loader2, 
  Bot, 
  User, 
  AlertCircle
} from 'lucide-react';
import { chatApi } from '../../api/chat';
import { mapChatMessageToViewModel, type ChatMessageViewModel } from '../../types/chat-mapper';
import { ChatEventCard } from './ChatEventCard';
import './FloatingAIAssistant.css';

const DEFAULT_CHIPS = [
  'Cuối tuần này có hoạt động CTXH nào không?',
  'Kiểm tra xem lịch thứ 7 của mình có trống không?',
  'Nhóm nào đang tuyển thành viên mới?',
];

export const FloatingAIAssistant: React.FC = () => {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessageViewModel[]>([
    {
      id: 'init-welcome',
      role: 'assistant',
      content: 'Xin chào! Mình là Trợ lý AI UniConnect. Bạn cần tìm hoạt động CTXH, kiểm tra lịch học rảnh hay tìm nhóm phù hợp cứ hỏi mình nhé!',
      cards: [],
      timeFormatted: '',
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>(DEFAULT_CHIPS);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
      inputRef.current?.focus();
    }
  }, [isOpen, messages, loading]);

  // Handle Escape key to close
  useEffect(() => {
    const handleKeyDown = (e: globalThis.KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  const handleSendMessage = useCallback(async (textToSend?: string) => {
    const text = (textToSend || inputValue).trim();
    if (!text || loading) return;

    const userMsg: ChatMessageViewModel = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      cards: [],
      timeFormatted: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages(prev => [...prev, userMsg]);
    if (!textToSend) setInputValue('');
    setLoading(true);
    setError(null);

    // Optional GPS
    let userLat: number | undefined;
    let userLng: number | undefined;
    if (navigator.geolocation) {
      try {
        const pos = await new Promise<GeolocationPosition>((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 2000 });
        });
        userLat = pos.coords.latitude;
        userLng = pos.coords.longitude;
      } catch {
        // Untrusted GPS fallback - proceed without coords
      }
    }

    try {
      const historyPayload = messages.map(m => ({
        role: m.role,
        content: m.content,
      }));
      historyPayload.push({ role: 'user', content: text });

      const res = await chatApi.chatWithBot({
        conversation_id: conversationId || undefined,
        message: text,
        messages: historyPayload,
        user_lat: userLat,
        user_lng: userLng,
      });

      if (res.conversation_id) {
        setConversationId(res.conversation_id);
      }

      if (res.suggestions && res.suggestions.length > 0) {
        setSuggestions(res.suggestions);
      }

      const assistantMsg = mapChatMessageToViewModel(res.message);
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Không thể kết nối với Trợ lý AI. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  }, [inputValue, loading, messages, conversationId]);

  return (
    <>
      {/* ── 1. Floating Gradient Orb Button ── */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="floating-ai-orb"
          aria-label="Mở Trợ lý AI Sinh viên UniConnect"
          title="Trợ lý AI UniConnect"
        >
          <div className="orb-pulse-ring" />
          <div className="orb-pulse-ring orb-pulse-ring--delay" />
          <div className="orb-core">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <span className="orb-badge">AI</span>
        </button>
      )}

      {/* ── 2. Floating Glassmorphism Chat Window ── */}
      {isOpen && (
        <div className="floating-ai-window glass animate-in fade-in zoom-in-95">
          {/* Header */}
          <div className="floating-ai-header">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 flex items-center justify-center shadow-sm">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5 leading-none">
                  Trợ Lý AI Campus
                  <span className="inline-block w-2 h-2 rounded-full bg-emerald-500" title="Đang trực tuyến" />
                </h3>
                <p className="text-[11px] text-slate-400 mt-1 leading-none">UniConnect Smart Assistant</p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={() => {
                  setIsOpen(false);
                  navigate('/chat');
                }}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition"
                title="Mở toàn màn hình"
                aria-label="Mở toàn màn hình"
              >
                <Maximize2 className="w-4 h-4" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition"
                title="Đóng cửa sổ"
                aria-label="Đóng cửa sổ"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Messages Stream */}
          <div className="floating-ai-body">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-2.5 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-7 h-7 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center shrink-0 mt-0.5 border border-indigo-200">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div className={`max-w-[85%] space-y-2.5 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                  <div
                    className={`p-3 rounded-2xl text-xs leading-relaxed inline-block ${
                      msg.role === 'user'
                        ? 'bg-indigo-600 text-white rounded-br-none shadow-sm'
                        : 'bg-slate-100 text-slate-800 rounded-bl-none border border-slate-200/60'
                    }`}
                  >
                    <div className="prose prose-xs max-w-none text-left">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  </div>

                  {/* Render Event Cards if any */}
                  {msg.cards && msg.cards.length > 0 && (
                    <div className="space-y-2 pt-1 w-full text-left">
                      {msg.cards.map((card) => (
                        <ChatEventCard key={card.activityId} card={card} />
                      ))}
                    </div>
                  )}
                </div>

                {msg.role === 'user' && (
                  <div className="w-7 h-7 rounded-full bg-slate-200 text-slate-600 flex items-center justify-center shrink-0 mt-0.5">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-2 text-xs text-slate-400 py-2">
                <Loader2 className="w-4 h-4 animate-spin text-indigo-500" />
                <span>Trợ lý AI đang tra cứu sự kiện và kiểm tra lịch...</span>
              </div>
            )}

            {error && (
              <div className="flex items-center gap-2 p-2.5 rounded-xl bg-rose-50 text-rose-600 text-xs border border-rose-200">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompt Chips */}
          <div className="floating-ai-chips">
            {suggestions.map((chip, idx) => (
              <button
                key={idx}
                onClick={() => handleSendMessage(chip)}
                disabled={loading}
                className="ai-prompt-chip"
              >
                {chip}
              </button>
            ))}
          </div>

          {/* Input Bar */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="floating-ai-footer"
          >
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Hỏi AI về hoạt động CTXH, lịch rảnh..."
              className="ai-chat-input"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={!inputValue.trim() || loading}
              className="ai-send-btn"
              aria-label="Gửi tin nhắn"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </form>
        </div>
      )}
    </>
  );
};
