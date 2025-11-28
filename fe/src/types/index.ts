/**
 * Product — mô tả sản phẩm được sử dụng trong toàn ứng dụng.
 *
 * Các trường chính:
 * - id: id nội bộ của sản phẩm
 * - name: tên/tiêu đề hiển thị
 * - image: URL ảnh sản phẩm
 * - price: chuỗi hiển thị giá (vd. "28.000đ")
 * - origin, brand: metadata tùy chọn
 * - rating: điểm trung bình (0-5)
 * - positivePercent: tỉ lệ phần trăm đánh giá tích cực (0-100)
 * - sentiment: nhãn cảm xúc tổng hợp (positive|neutral|negative)
 * - links: liên kết đến các marketplace (shopee, lazada, tiki)
 */
export interface Product {
  id: number;
  name: string;
  image: string;
  price: string;
  origin?: string;
  brand?: string;
  rating: number;
  positivePercent: number;
  sentiment?: 'positive' | 'neutral' | 'negative';
  links?: {
    shopee?: string;
    lazada?: string;
    tiki?: string;
  };
}

/**
 * Review — đại diện cho đánh giá của người dùng về sản phẩm.
 *
 * Lưu ý: `createdAt` là chuỗi ISO (ví dụ từ API hoặc mock data).
 */
export interface Review {
  /** id duy nhất của đánh giá */
  id: number;
  /** id người dùng (có thể là number hoặc string tuỳ hệ thống auth) */
  userId: number | string;
  /** tên hiển thị của người đánh giá */
  userName: string;
  /** điểm đánh giá (1-5) */
  rating: number;
  /** nhận xét tự do (tuỳ chọn) */
  comment?: string;
  /** thời điểm tạo (ISO string) */
  createdAt: string;
}

/**
 * Message — một tin nhắn trong giao diện chat.
 * - `suggestions` sẽ chứa danh sách `Product` khi bot trả về kết quả.
 */
export interface Message {
  id: number;
  content: string;
  sender: 'user' | 'system' | 'bot';
  timestamp: string | Date;
  suggestions?: Product[];
}

/**
 * Conversation — nhóm các `Message` cùng metadata để hiển thị trong UI chat.
 */
export interface Conversation {
  id: number;
  title: string;
  lastMessage: string;
  timestamp: string;
  messages: Message[];
}
