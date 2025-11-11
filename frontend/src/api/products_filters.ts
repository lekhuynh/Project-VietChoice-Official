import { API_BASE_URL } from '../config';

export interface DbProduct {
  Product_ID: number;
  Product_Name: string;
  Image_URL?: string;
  Price?: number;
  Avg_Rating?: number;
  Positive_Percent?: number;
  Brand?: string;
  Origin?: string;
  Sentiment_Label?: string;
}

export interface ProductFilterParams {
  lv1?: string;
  lv2?: string;
  lv3?: string;
  lv4?: string;
  lv5?: string;
  min_price?: number;
  max_price?: number;
  brand?: string; // comma separated
  min_rating?: number;
  sort?: 'price_asc' | 'price_desc' | 'rating_desc';
  is_vietnam_origin?: boolean;
  is_vietnam_brand?: boolean;
  positive_over?: number;
}

export const fetchProductsByCategoryAndFilters = async (
  params: ProductFilterParams
): Promise<DbProduct[]> => {
  const usp = new URLSearchParams();
  (Object.entries(params) as [keyof ProductFilterParams, any][]).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') usp.set(String(k), String(v));
  });
  const url = `${API_BASE_URL}/products/by-category${usp.toString() ? `?${usp.toString()}` : ''}`;
  const res = await fetch(url, { credentials: 'include' });
  if (!res.ok) throw new Error('Không lấy được danh sách sản phẩm.');
  const data = (await res.json()) as DbProduct[];
  return Array.isArray(data) ? data : [];
};

