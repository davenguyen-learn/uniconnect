import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { chatApi } from '../../api/chat';
import { useToast } from '../../components/Toast/ToastContext';
import { ApiRequestError } from '../../api/client';
import Button from '../../components/Button/Button';
import Input from '../../components/Input/Input';
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
      content: 'Hello! I am your UniConnect AI assistant. I can help you find interesting activities around campus based on your preferences. Try asking me "What tech events are happening nearby?"'
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
        toast.error('AI Error', err.message);
      } else {
        toast.error('Failed to communicate with AI');
      }
      // Remove the user message if it failed completely
      setMessages(messages);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  return (
    <div className="container chat-container">
      <div className="chat-card glass">
        <div className="chat-header">
          <h2>AI Discovery Assistant</h2>
          <p>Ask me anything about activities and events.</p>
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
          <Input 
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            disabled={loading}
          />
          <Button onClick={handleSend} disabled={!inputValue.trim() || loading}>
            Send
          </Button>
        </div>
      </div>
    </div>
  );
}
