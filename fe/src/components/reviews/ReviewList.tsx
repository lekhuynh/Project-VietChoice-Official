import React from 'react';
import { Edit, Trash, Star } from 'lucide-react';
import { type ProductReview } from '../../api/reviews';

interface ReviewListProps {
  reviews: ProductReview[];
  currentUserId: number | null;
  onEdit: (rv: ProductReview) => void;
  onDelete: (reviewId: number) => Promise<void> | void;
}

const ReviewList: React.FC<ReviewListProps> = ({ reviews, currentUserId, onEdit, onDelete }) => {
  return (
    <div className="border border-gray-200 rounded-xl p-3 bg-gray-50">
      <div className="text-sm font-semibold text-gray-800 mb-2">Danh sách đánh giá</div>
      <div className="h-[320px] overflow-y-auto pr-1 space-y-3">
        {reviews.length > 0 ? (
          reviews.map((rv) => (
            <div key={rv.review_id} className="bg-white border border-gray-200 rounded-lg p-3 shadow-sm">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-sm text-gray-500">
                      {rv.user_name || 'Người dùng'}
                      {currentUserId && rv.user_id === currentUserId ? ' (Bạn)' : ''}
                      <span className="ml-2 text-xs text-gray-400">{new Date(rv.created_at).toLocaleString('vi-VN')}</span>
                    </div>
                    <div className="flex items-center">
                      {[...Array(5)].map((_, i) => (
                        <Star
                          key={i}
                          className={`h-4 w-4 ${i < rv.rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300'}`}
                        />
                      ))}
                    </div>
                  </div>
                  {rv.comment && <p className="text-gray-700 text-sm">{rv.comment}</p>}
                </div>
                {currentUserId && rv.user_id === currentUserId && (
                  <div className="flex space-x-2 ml-4">
                    <button
                      className="text-blue-600 hover:text-blue-800 p-1"
                      onClick={() => onEdit(rv)}
                      title="Chỉnh sửa"
                    >
                      <Edit className="h-4 w-4" />
                    </button>
                    <button
                      className="text-red-600 hover:text-red-800 p-1"
                      onClick={() => onDelete(rv.review_id)}
                      title="Xóa"
                    >
                      <Trash className="h-4 w-4" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-6 bg-gray-50 rounded-lg">
            <p className="text-gray-500">Chưa có đánh giá nào. Hãy là người đầu tiên chia sẻ trải nghiệm!</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReviewList;
