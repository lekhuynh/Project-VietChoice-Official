import { type FC } from 'react';
import { ShoppingCartIcon, ThumbsUpIcon, StarIcon } from 'lucide-react';
import { Link } from 'react-router-dom';
import { type Message, type Product } from '../../types';

/**
 * Props cho ChatBubble
 *
 * @property message - đối tượng `Message` chứa nội dung, người gửi và timestamp
 * @property suggestions - danh sách `Product` được gợi ý khi bot trả kết quả
 */
interface ChatBubbleProps {
  message: Message;
  suggestions?: Product[];
}

/**
 * ChatBubble
 *
 * Hiển thị một tin nhắn trong giao diện chat. Nếu `suggestions` được cung cấp
 * (thường khi bot trả về kết quả), component sẽ hiển thị danh sách sản phẩm gợi ý
 * kèm link đến trang chi tiết.
 */
const ChatBubble: FC<ChatBubbleProps> = ({ message, suggestions }) => {
  const { content, sender, timestamp } = message;
  return (
    <div className={`flex ${sender === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-lg p-4 ${sender === 'user' ? 'bg-emerald-600 text-white' : 'bg-gray-100 text-gray-800'}`}
      >
        <div className="text-sm">{content}</div>
        <div className="text-xs mt-1 opacity-70">
          {new Date(timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
        {suggestions && suggestions.length > 0 && (
          <div className="mt-4 space-y-4">
            {suggestions.map((product) => (
              <div key={product.id} className="bg-white rounded-lg shadow p-3">
                <div className="flex items-start space-x-3">
                  <img
                    src={product.image}
                    alt={product.name}
                    className="w-16 h-16 object-cover rounded"
                  />
                  <div className="flex-1">
                    <Link
                      to={`/product/${product.id}`}
                      className="font-medium text-gray-900 hover:text-emerald-600"
                    >
                      {product.name}
                    </Link>
                    <div className="flex items-center mt-1">
                      <StarIcon className="h-4 w-4 text-yellow-400" />
                      <span className="text-xs text-gray-600 ml-1">{product.rating}/5</span>
                      <span className="mx-2 text-gray-300">|</span>
                      <ThumbsUpIcon className="h-4 w-4 text-emerald-500" />
                      <span className="text-xs text-gray-600 ml-1">
                        {product.positivePercent}% tích cực
                      </span>
                    </div>
                    <div className="mt-1 text-sm font-medium text-gray-900">{product.price}</div>
                    {product.links && (
                      <div className="flex mt-2 space-x-2">
                        {product.links.shopee && (
                          <a
                            href={product.links.shopee}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center text-xs bg-orange-500 text-white px-2 py-1 rounded"
                          >
                            <ShoppingCartIcon className="h-3 w-3 mr-1" />
                            Shopee
                          </a>
                        )}
                        {product.links.lazada && (
                          <a
                            href={product.links.lazada}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center text-xs bg-blue-500 text-white px-2 py-1 rounded"
                          >
                            <ShoppingCartIcon className="h-3 w-3 mr-1" />
                            Lazada
                          </a>
                        )}
                        {product.links.tiki && (
                          <a
                            href={product.links.tiki}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center text-xs bg-teal-500 text-white px-2 py-1 rounded"
                          >
                            <ShoppingCartIcon className="h-3 w-3 mr-1" />
                            Tiki
                          </a>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
export default ChatBubble;
