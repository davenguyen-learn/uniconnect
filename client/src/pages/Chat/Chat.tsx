import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  Send, 
  Loader2, 
  AlertCircle,
  RotateCcw
} from 'lucide-react';
import { chatApi } from '../../api/chat';
import { useToast } from '../../components/Toast/ToastContext';
import { mapChatMessageToViewModel, type ChatMessageViewModel } from '../../types/chat-mapper';
import { ChatEventCard } from '../../components/chat/ChatEventCard';
import './Chat.css';

const DEFAULT_SUGGESTIONS = [
  'Cuối tuần này có hoạt động CTXH nào không?',
  'Kiểm tra xem lịch thứ 7 của mình có trống không?',
  'Nhóm nào đang tuyển thành viên mới?',
];

export default function Chat() {
  const navigate = useNavigate();
  const toast = useToast();
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessageViewModel[]>([
    {
      id: 'init-0',
      role: 'assistant',
      content: 'Xin chào! Mình là Trợ lý AI UniConnect. Mình có thể giúp bạn tìm các hoạt động ngoại khóa, đối soát lịch học rảnh để không bị trùng giờ, hoặc giới thiệu các nhóm đang tuyển thành viên!',
      cards: [],
      timeFormatted: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>(DEFAULT_SUGGESTIONS);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend || inputValue).trim();
    if (!text || loading) return;

    const userMessage: ChatMessageViewModel = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      cards: [],
      timeFormatted: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages(prev => [...prev, userMessage]);
    if (!textToSend) setInputValue('');
    setLoading(true);
    setError(null);

    // Optional GPS
    let lat: number | undefined;
    let lng: number | undefined;
    if (navigator.geolocation) {
      try {
        const pos = await new Promise<GeolocationPosition>((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 2000 });
        });
        lat = pos.coords.latitude;
        lng = pos.coords.longitude;
      } catch {
        // Proceed without coordinates
      }
    }

    try {
      const historyPayload = messages.map(m => ({
        role: m.role,
        content: m.content,
      }));
      historyPayload.push({ role: 'user', content: text });

      const response = await chatApi.chatWithBot({
        conversation_id: conversationId || undefined,
        message: text,
        messages: historyPayload,
        user_lat: lat,
        user_lng: lng,
      });

      if (response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      if (response.suggestions && response.suggestions.length > 0) {
        setSuggestions(response.suggestions);
      }

      const assistantMsg = mapChatMessageToViewModel(response.message);
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Không thể kết nối với Trợ lý AI');
      toast.error('Lỗi trợ lý AI');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleReset = () => {
    setConversationId(null);
    setMessages([
      {
        id: 'init-new',
        role: 'assistant',
        content: 'Cuộc trò chuyện mới đã bắt đầu! Bạn muốn tìm hiểu hoạt động nào hôm nay?',
        cards: [],
        timeFormatted: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
    setSuggestions(DEFAULT_SUGGESTIONS);
    setError(null);
  };

  return (
    <div className="container full-chat-page">
      <div className="full-chat-card glass">
        {/* Header */}
        <div className="full-chat-header">
          <div className="flex items-center gap-3">
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                Trợ Lý AI Sinh Viên Thông Minh
              </h2>
              <p className="text-xs text-slate-500">
                Tìm kiếm hoạt động, kiểm tra trùng lịch học và tư vấn nhóm hoạt động quanh khuôn viên
              </p>
            </div>
          </div>

          <button
            onClick={handleReset}
            className="chat-reset-btn inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-xl"
            title="Bắt đầu cuộc trò chuyện mới"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Làm mới
          </button>
        </div>

        {/* Message Stream */}
        <div className="full-chat-messages">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[80%] space-y-3 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                <div
                  className={`p-4 rounded-2xl text-sm leading-relaxed inline-block chat-message-bubble shadow-sm ${
                    msg.role === 'user'
                      ? 'rounded-br-none'
                      : 'rounded-bl-none'
                  }`}
                >
                  <div className="prose prose-sm max-w-none text-left" style={{ color: '#000000' }}>
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        a: ({ href, children, ...props }) => {
                          const isInternal = href && (href.startsWith('/') || href.startsWith(window.location.origin));
                          const path = href ? (href.startsWith('/') ? href : href.replace(window.location.origin, '')) : '#';
                          return (
                            <a
                              href={href}
                              onClick={(e) => {
                                if (isInternal) {
                                  e.preventDefault();
                                  navigate(path);
                                }
                              }}
                              className="chat-link"
                              {...props}
                            >
                              {children}
                            </a>
                          );
                        },
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                  {msg.timeFormatted && (
                    <div className="text-[10px] mt-1 text-right chat-message-time">
                      {msg.timeFormatted}
                    </div>
                  )}
                </div>

                {/* Event Cards Grid */}
                {msg.cards && msg.cards.length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1 w-full text-left">
                    {msg.cards.map((card) => (
                      <ChatEventCard key={card.activityId} card={card} />
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-3 py-2 text-slate-400 text-xs">
              <div className="w-8 h-8 rounded-full bg-indigo-50 flex items-center justify-center">
                <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
              </div>
              <span>Trợ lý AI đang tra cứu sự kiện và đối soát lịch bận...</span>
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 p-3 rounded-xl bg-rose-50 text-rose-600 text-xs border border-rose-200">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggestion Chips */}
        <div className="full-chat-chips">
          {suggestions.map((chip, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(chip)}
              disabled={loading}
              className="chat-prompt-chip"
            >
              {chip}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div className="full-chat-input-container">
          <textarea
            ref={textareaRef}
            className="full-chat-textarea"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Hỏi về hoạt động CTXH cuối tuần, kiểm tra lịch học, tìm nhóm..."
            disabled={loading}
            rows={2}
          />
          <button
            onClick={() => handleSend()}
            disabled={!inputValue.trim() || loading}
            className="full-chat-send-btn"
            aria-label="Gửi tin nhắn"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
          </button>
        </div>
      </div>
    </div>
  );
}
