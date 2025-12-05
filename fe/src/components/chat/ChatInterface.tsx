import { useEffect, useState, useRef, type KeyboardEvent } from 'react';
import { SendIcon, ImageIcon, BarcodeIcon, Loader2Icon, RotateCcwIcon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import ChatBubble from './ChatBubble';
import { type Message, type Product } from '../../types';
import { fetchSearchProducts, type ProductMin } from '../../api/products';
import { fetchUserProfile } from '../../api/user';

const STORAGE_KEY_BASE = 'vc_chat_state_v1';
const GUEST_STORAGE_KEY = `${STORAGE_KEY_BASE}_guest`;

const buildInitialMessages = (): Message[] => [
  {
    id: 1,
    content:
      'Xin chào! Mình là trợ lý VietChoice. Bạn có thể nhập tên sản phẩm, quét mã vạch hoặc tải ảnh bao bì để tra cứu thông tin sản phẩm.',
    sender: 'bot',
    timestamp: new Date(),
  },
];

const ChatInterface = () => {
  const [messages, setMessages] = useState<Message[]>(buildInitialMessages());
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const [storageInfo, setStorageInfo] = useState<{ key: string; driver: 'local' | 'session' } | null>(null);
  const [hydrated, setHydrated] = useState(false);

  const messagesContainerRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const navigate = useNavigate();

  const canReset = messages.length > 1 || input.trim().length > 0;

  const scrollToBottom = () => {
    const el = messagesContainerRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    let cancelled = false;
    const checkAuth = async () => {
      try {
        const profile = await fetchUserProfile();
        if (cancelled) return;
        setIsAuthenticated(true);
        setStorageInfo({ key: `${STORAGE_KEY_BASE}_${profile.id}`, driver: 'local' });
        try {
          sessionStorage.removeItem(GUEST_STORAGE_KEY);
        } catch {}
      } catch {
        if (cancelled) return;
        setIsAuthenticated(false);
        setStorageInfo({ key: GUEST_STORAGE_KEY, driver: 'session' });
      } finally {
        if (!cancelled) setAuthChecked(true);
      }
    };
    void checkAuth();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!storageInfo || storageInfo.driver !== 'session') return;
    const handler = () => {
      try {
        sessionStorage.removeItem(storageInfo.key);
      } catch {}
    };
    window.addEventListener('beforeunload', handler);
    return () => {
      window.removeEventListener('beforeunload', handler);
    };
  }, [storageInfo]);

  useEffect(() => {
    if (!authChecked || !storageInfo) return;
    setHydrated(false);
    const storage = storageInfo.driver === 'session' ? window.sessionStorage : window.localStorage;
    try {
      let raw = storage.getItem(storageInfo.key);
      if (!raw && storageInfo.driver === 'local') {
        const legacy = localStorage.getItem(STORAGE_KEY_BASE);
        if (legacy) {
          raw = legacy;
          localStorage.setItem(storageInfo.key, legacy);
          localStorage.removeItem(STORAGE_KEY_BASE);
        }
      }
      if (!raw) {
        setMessages(buildInitialMessages());
        setInput('');
        return;
      }
      const parsed = JSON.parse(raw) as { input?: string; messages?: Message[] };
      if (typeof parsed.input === 'string') {
        setInput(parsed.input);
      }
      if (Array.isArray(parsed.messages) && parsed.messages.length > 0) {
        setMessages(
          parsed.messages.map((m, idx) => ({
            ...m,
            id: m.id ?? idx + 1,
            timestamp: new Date(m.timestamp ?? new Date().toISOString()),
          }))
        );
      } else {
        setMessages(buildInitialMessages());
      }
    } catch {
      setMessages(buildInitialMessages());
      setInput('');
    } finally {
      setHydrated(true);
    }
  }, [authChecked, storageInfo]);

  useEffect(() => {
    if (!storageInfo || !hydrated) return;
    const storage = storageInfo.driver === 'session' ? window.sessionStorage : window.localStorage;
    try {
      const payload = {
        input,
        messages: messages.map((m) => ({
          ...m,
          timestamp: m.timestamp instanceof Date ? m.timestamp.toISOString() : m.timestamp,
        })),
      };
      storage.setItem(storageInfo.key, JSON.stringify(payload));
    } catch {
      // ignore
    }
  }, [storageInfo, hydrated, input, messages]);

  const mapToUiProduct = (p: ProductMin): Product => {
    const priceStr = typeof p.Price === 'number' ? `${p.Price.toLocaleString('vi-VN')} đ` : String((p as any).Price ?? '');
    const pos = (p as any).Positive_Percent as number | undefined;
    const sentiment = typeof pos === 'number' ? (pos >= 75 ? 'positive' : pos >= 40 ? 'neutral' : 'negative') : undefined;
    return {
      id: p.Product_ID,
      name: p.Product_Name,
      image: p.Image_URL,
      price: priceStr,
      rating: typeof p.Avg_Rating === 'number' ? p.Avg_Rating : 0,
      positivePercent: typeof pos === 'number' ? pos : 0,
      sentiment,
    };
  };

  const handleSendMessage = async () => {
    if (input.trim() === '') return;
    const userMessage: Message = {
      id: messages.length + 1,
      content: input,
      sender: 'user',
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setInput('');
    try {
      const response = await fetchSearchProducts(userMessage.content);
      const aiMessage = response.ai_message?.trim();
      const treatedAsChat =
        response.input_type === 'chat' || (!!aiMessage && (!response.results?.length || (response.count ?? 0) === 0));
      if (treatedAsChat) {
        const botResponse: Message = {
          id: messages.length + 2,
          content: aiMessage || 'Mình chỉ hỗ trợ sản phẩm thôi, bạn thử nhập cụ thể hơn nhé.',
          sender: 'bot',
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, botResponse]);
        return;
      }
      const suggestions: Product[] = response.results.map(mapToUiProduct);
      const keyword = (response.refined_query?.trim() || userMessage.content).trim();
      const total = typeof response.count === 'number' ? response.count : suggestions.length;
      const hasResults = suggestions.length > 0;
      const botResponse: Message = {
        id: messages.length + 2,
        content: hasResults
          ? `Mình đã tìm thấy ${total} sản phẩm phù hợp với từ khóa "${keyword}":`
          : `Mình chưa tìm thấy sản phẩm nào khớp với "${keyword}". Bạn thử mô tả cụ thể hơn nhé!`,
        sender: 'bot',
        timestamp: new Date(),
        suggestions: hasResults ? suggestions : undefined,
      };
      setMessages((prev) => [...prev, botResponse]);
    } catch {
      const botResponse: Message = {
        id: messages.length + 2,
        content: 'Xin lỗi, hiện không thể tìm kiếm. Vui lòng thử lại sau.',
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botResponse]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  const handleImageUpload = () => {
    try {
      localStorage.setItem('vc_scanner_tab_v1', 'image');
    } catch {}
    navigate('/scanner?tab=image');
  };

  const handleBarcodeScanner = () => {
    navigate('/scanner');
  };

  const handleResetConversation = () => {
    setMessages(buildInitialMessages());
    setInput('');
    if (storageInfo) {
      const storage = storageInfo.driver === 'session' ? window.sessionStorage : window.localStorage;
      try {
        storage.removeItem(storageInfo.key);
      } catch {}
    }
  };

  return (
    <div className="flex flex-col h-full min-h-0 bg-white rounded-lg shadow-lg">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <div>
          <p className="text-sm font-semibold text-emerald-700">Trợ lý VietChoice</p>
          <p className="text-xs text-gray-500">
            {isAuthenticated
              ? 'Hội thoại được lưu cho tài khoản của bạn.'
              : 'Hội thoại tạm thời, giữ nguyên khi bạn đang dùng - rời trang sẽ reset.'}
          </p>
        </div>
        <button
          type="button"
          onClick={handleResetConversation}
          disabled={!canReset}
          className={`flex items-center gap-1 text-xs font-medium px-3 py-1.5 rounded-md border ${
            canReset ? 'text-emerald-700 border-emerald-200 hover:bg-emerald-50' : 'text-gray-400 border-gray-200 cursor-not-allowed'
          }`}
        >
          <RotateCcwIcon className="h-4 w-4" />
          Đặt lại
        </button>
      </div>

      {/* Scrollable message area with a fixed height */}
      <div ref={messagesContainerRef} className="flex-grow overflow-y-auto p-4 space-y-4 min-h-0 max-h-[420px]">
        {messages.map((message) => (
          <ChatBubble key={message.id} message={message} suggestions={message.suggestions} />
        ))}
        {isLoading && (
          <div className="flex items-center justify-center p-4">
            <Loader2Icon className="animate-spin h-5 w-5 mr-2 text-emerald-600" />
            <span className="text-gray-600">Đang tìm kiếm...</span>
          </div>
        )}
      </div>

      <div className="border-t border-gray-200 p-4 flex-shrink-0 bg-white">
        <div className="flex flex-wrap sm:flex-nowrap items-center gap-2">
          <button
            onClick={handleBarcodeScanner}
            className="p-2 text-gray-500 hover:text-emerald-600 hover:bg-emerald-50 rounded-full flex-shrink-0"
            title="Quét mã vạch"
          >
            <BarcodeIcon className="h-5 w-5" />
          </button>
          <button
            onClick={handleImageUpload}
            className="p-2 text-gray-500 hover:text-emerald-600 hover:bg-emerald-50 rounded-full flex-shrink-0"
            title="Tải hình ảnh"
          >
            <ImageIcon className="h-5 w-5" />
          </button>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Nhập tên sản phẩm bạn muốn tìm..."
            className="flex-1 min-w-0 w-full sm:w-auto border border-gray-300 rounded-full px-4 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            ref={inputRef}
          />
          <button
            onClick={handleSendMessage}
            disabled={input.trim() === ''}
            className={`p-2 rounded-full ${
              input.trim() === '' ? 'bg-gray-200 text-gray-400' : 'bg-emerald-600 text-white hover:bg-emerald-700'
            }`}
          >
            <SendIcon className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
