import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  Sparkles, 
  Send, 
  Bot, 
  User, 
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
  'CLB nào đang tuyển thành viên mới?',
];

export default function Chat() {
  const toast = useToast();
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessageViewModel[]>([
    {
      id: 'init-0',
      role: 'assistant',
      content: 'Xin chào! Mình là Trợ lý AI UniConnect. Mình có thể giúp bạn tìm các hoạt động ngoại khóa, đối soát lịch học rảnh để không bị trùng giờ, hoặc giới thiệu các CLB đang tuyển quân!',
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
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 flex items-center justify-center shadow-md">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                Trợ Lý AI Sinh Viên Thông Minh
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400">
                  Online
                </span>
              </h2>
              <p className="text-xs text-slate-500">
                Tìm kiếm hoạt động, kiểm tra trùng lịch học và tư vấn câu lạc bộ quanh khuôn viên
              </p>
            </div>
          </div>

          <button
            onClick={handleReset}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition"
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
              className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center shrink-0 mt-0.5 border border-indigo-200 dark:border-indigo-900/50">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div className={`max-w-[80%] space-y-3 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                <div
                  className={`p-4 rounded-2xl text-sm leading-relaxed inline-block ${
                    msg.role === 'user'
                      ? 'bg-indigo-600 text-white rounded-br-none shadow-sm'
                      : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 rounded-bl-none border border-slate-200/80 dark:border-slate-700/80 shadow-sm'
                  }`}
                >
                  <div className="prose prose-sm dark:prose-invert max-w-none text-left">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                  {msg.timeFormatted && (
                    <div className={`text-[10px] mt-1 text-right ${msg.role === 'user' ? 'text-indigo-200' : 'text-slate-400'}`}>
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

              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 flex items-center justify-center shrink-0 mt-0.5">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-3 py-2 text-slate-400 text-xs">
              <div className="w-8 h-8 rounded-full bg-indigo-50 dark:bg-indigo-950/40 flex items-center justify-center">
                <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
              </div>
              <span>Trợ lý AI đang tra cứu sự kiện và đối soát lịch bận...</span>
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 text-xs border border-rose-200 dark:border-rose-900/50">
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
            placeholder="Hỏi về hoạt động CTXH cuối tuần, kiểm tra lịch học, tìm câu lạc bộ..."
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
