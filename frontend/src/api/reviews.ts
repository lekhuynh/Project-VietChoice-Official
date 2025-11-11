import { API_BASE_URL } from '../config';

export interface ProductReview {
  review_id: number;
  user_id: number;
  product_id: number;
  rating: number;
  comment?: string;
  created_at: string;
}

export const fetchReviewsByProduct = async (
  productId: number | string
): Promise<ProductReview[]> => {
  const res = await fetch(`${API_BASE_URL}/reviews/product/${productId}`);
  if (!res.ok) {
    // Return empty list on error to avoid blocking detail page
    return [];
  }
  return (await res.json()) as ProductReview[];
};

export const createReview = async (
  productId: number | string,
  rating: number,
  comment?: string
): Promise<ProductReview> => {
  const res = await fetch(`${API_BASE_URL}/reviews/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ product_id: productId, rating, comment }),
  });
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || 'Không thể tạo đánh giá');
  }
  return (await res.json()) as unknown as ProductReview;
};

export const updateReview = async (
  reviewId: number,
  rating: number,
  comment?: string
): Promise<ProductReview> => {
  const res = await fetch(`${API_BASE_URL}/reviews/${reviewId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ rating, comment }),
  });
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || 'Không thể cập nhật đánh giá');
  }
  return (await res.json()) as unknown as ProductReview;
};

export const deleteReview = async (reviewId: number): Promise<void> => {
  const res = await fetch(`${API_BASE_URL}/reviews/${reviewId}`, {
    method: 'DELETE',
    credentials: 'include',
  });
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || 'Không thể xóa đánh giá');
  }
};
