import { useEffect, useState, useRef, type KeyboardEvent } from 'react';
import { SendIcon, ImageIcon, BarcodeIcon, Loader2Icon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import ChatBubble from './ChatBubble';
import { type Message, type Product } from '../../types';
import { fetchSearchProducts, type ProductMin } from '../../api/products';

const ChatInterface = () => {
  const STORAGE_KEY = 'vc_chat_state_v1';
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      content:
        'Xin chÃ o! MÃ¬nh lÃ  trá»£ lÃ½ VietChoice. Báº¡n cÃ³ thá»ƒ nháº­p tÃªn sáº£n pháº©m, quÃ©t mÃ£ váº¡ch hoáº·c táº£i lÃªn hÃ¬nh áº£nh Ä‘á»ƒ tra cá»©u thÃ´ng tin sáº£n pháº©m.',
      sender: 'bot',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const messagesContainerRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const navigate = useNavigate();
  const scrollToBottom = () => {
    const el = messagesContainerRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
  };
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load persisted chat state on mount
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as { input?: string; messages?: Message[] };
        if (typeof parsed.input === 'string') {
          setInput(parsed.input);
        }
        if (Array.isArray(parsed.messages) && parsed.messages.length > 0) {
          setMessages(
            parsed.messages.map((m, idx) => ({
              ...m,
              id: m.id ?? idx + 1,
              timestamp: m.timestamp ?? new Date(),
            }))
          );
        }
      }
    } catch {
      // ignore storage errors
    }
    inputRef.current?.focus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Persist chat state whenever input or messages change
  useEffect(() => {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ input, messages })
      );
    } catch {
      // ignore storage quota
    }
  }, [input, messages]);

  const mapToUiProduct = (p: ProductMin): Product => {
    const priceStr = typeof p.Price === 'number' ? `${p.Price.toLocaleString('vi-VN')}â‚«` : String((p as any).Price ?? '');
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
      const { products } = await fetchSearchProducts(userMessage.content);
      const suggestions: Product[] = products.map(mapToUiProduct);
      const botResponse: Message = {
        id: messages.length + 2,
        content: 'MÃ¬nh Ä‘Ã£ tÃ¬m tháº¥y má»™t sá»‘ sáº£n pháº©m phÃ¹ há»£p vá»›i yÃªu cáº§u cá»§a báº¡n:',
        sender: 'bot',
        timestamp: new Date(),
        suggestions,
      };
      setMessages((prev) => [...prev, botResponse]);
    } catch {
      const botResponse: Message = {
        id: messages.length + 2,
        content: 'Xin lá»—i, hiá»‡n khÃ´ng thá»ƒ tÃ¬m kiáº¿m. Vui lÃ²ng thá»­ láº¡i sau.',
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botResponse]);
    } finally {
      setIsLoading(false);
      // keep the query for quick refinement and ensure focus stays on the input
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  const handleImageUpload = () => {
    try { localStorage.setItem('vc_scanner_tab_v1', 'image'); } catch {}
    navigate('/scanner?tab=image');
  };
  const handleBarcodeScanner = () => {
    navigate('/scanner');
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      <div ref={messagesContainerRef} className="flex-grow overflow-y-auto p-4 space-y-4 min-h-0">
        {messages.map((message) => (
          <ChatBubble key={message.id} message={message} suggestions={message.suggestions} />
        ))}
        {isLoading && (
          <div className="flex items-center justify-center p-4">
            <Loader2Icon className="animate-spin h-5 w-5 mr-2 text-emerald-600" />
            <span className="text-gray-600">Äang tÃ¬m kiáº¿m...</span>
          </div>
        )}
      </div>

      <div className="border-t border-gray-200 p-4 flex-shrink-0 sticky bottom-0 bg-white">
        <div className="flex items-center space-x-2">
          <button
            onClick={handleBarcodeScanner}
            className="p-2 text-gray-500 hover:text-emerald-600 hover:bg-emerald-50 rounded-full"
            title="QuÃ©t mÃ£ váº¡ch"
          >
            <BarcodeIcon className="h-5 w-5" />
          </button>
          <button
            onClick={handleImageUpload}
            className="p-2 text-gray-500 hover:text-emerald-600 hover:bg-emerald-50 rounded-full"
            title="Táº£i lÃªn hÃ¬nh áº£nh"
          >
            <ImageIcon className="h-5 w-5" />
          </button>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Nháº­p tÃªn sáº£n pháº©m báº¡n muá»‘n tÃ¬m..."
            className="flex-grow border border-gray-300 rounded-full px-4 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            ref={inputRef}
          />
          <button
            onClick={handleSendMessage}
            disabled={input.trim() === ''}
            className={`p-2 rounded-full ${input.trim() === '' ? 'bg-gray-200 text-gray-400' : 'bg-emerald-600 text-white hover:bg-emerald-700'}`}
          >
            <SendIcon className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;


