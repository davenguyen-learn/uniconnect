import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { chatApi } from '../../api/chat';
import { useToast } from '../../components/Toast/ToastContext';
import { ApiRequestError } from '../../api/client';
import Button from '../../components/Button/Button';
import ActivityCard from '../../components/ActivityCard/ActivityCard';
import { type ActivityResponse } from '../../api/activities';
import './Chat.css';

interface MessageBlock {
  role: 'user' | 'model';
  content: string;
  activities?: ActivityResponse[];
}

export default function Chat() {
  const navigate = useNavigate();
  const toast = useToast();
  const [messages, setMessages] = useState<MessageBlock[]>([
    {
      role: 'model',
      content: 'Xin chào! Tôi là trợ lý AI UniConnect của bạn. Tôi có thể giúp bạn tìm các hoạt động thú vị xung quanh khuôn viên trường dựa trên sở thích của bạn. Hãy thử hỏi tôi "Có sự kiện công nghệ nào đang diễn ra gần đây không?"'
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async () => {
    if (!inputValue.trim() || loading) return;

    const userMessage: MessageBlock = { role: 'user', content: inputValue.trim() };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInputValue('');
    setLoading(true);

    try {
      let lat: number | undefined;
      let lng: number | undefined;
      
      try {
        if ('geolocation' in navigator) {
          const position = await new Promise<GeolocationPosition>((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 3000 });
          });
          lat = position.coords.latitude;
          lng = position.coords.longitude;
        }
      } catch (geoErr) {
        console.warn("Could not get geolocation:", geoErr);
        // We will just proceed without coordinates if the user denies or it times out
      }

      // Build request payload (convert MessageBlock to ChatMessage)
      const payload = {
        messages: newMessages.map(m => ({ role: m.role, content: m.content })),
        user_lat: lat,
        user_lng: lng
      };
      
      const response = await chatApi.chatWithBot(payload);
      
      setMessages(prev => [
        ...prev, 
        { 
          role: 'model', 
          content: response.reply,
          activities: response.recommended_activities 
        }
      ]);
    } catch (err) {
      if (err instanceof ApiRequestError) {
        toast.error('Lỗi AI', err.message);
      } else {
        toast.error('Không thể giao tiếp với AI');
      }
      // Remove the user message if it failed completely
      setMessages(messages);
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

  return (
    <div className="container chat-container">
      <div className="chat-card glass">
        <div className="chat-header">
          <h2>Trợ lý khám phá AI</h2>
          <p>Hỏi tôi bất cứ điều gì về các hoạt động và sự kiện.</p>
        </div>
        
        <div className="chat-messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`chat-message ${msg.role}`}>
              <div className="chat-avatar">
                {msg.role === 'user' ? 'U' : 'AI'}
              </div>
              <div className="chat-content">
                <div className="chat-bubble">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                </div>
                {msg.activities && msg.activities.length > 0 && (
                  <div className="chat-activities">
                    {msg.activities.map(act => (
                      <div key={act.id} className="chat-activity-wrapper">
                        <ActivityCard activity={act} onClick={() => navigate(`/activities/${act.id}`)} />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="chat-message model">
              <div className="chat-avatar">AI</div>
              <div className="chat-content">
                <div className="chat-bubble typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        
        <div className="chat-input-area">
          <textarea
            className="input-field chat-textarea"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Tìm kiếm hoạt động..."
            disabled={loading}
            rows={2}
          />
          <Button onClick={handleSend} disabled={!inputValue.trim() || loading} className="chat-send-btn">
            Gửi
          </Button>
        </div>
      </div>
    </div>
  );
}
