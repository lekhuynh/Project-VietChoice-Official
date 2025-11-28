import { API_BASE_URL } from '../config';

export interface AdminProduct {
  Product_ID: number;
  Product_Name: string;
  Brand?: string;
  Price?: number;
  Avg_Rating?: number;
  Positive_Percent?: number;
  Sentiment_Label?: string;
  Image_URL?: string;
  Product_URL?: string;
  Is_Active?: boolean;
}

export interface SentimentGroup {
  label: string;
  category_id: number | null;
  total: number;
  positive: number;
  neutral: number;
  negative: number;
  positive_pct: number;
  neutral_pct: number;
  negative_pct: number;
}

export async function fetchOutstandingProducts(params?: {
  limit?: number;
  brand?: string;
  min_price?: number;
  max_price?: number;
}): Promise<{ total: number; results: AdminProduct[] }> {
  const url = new URL(`${API_BASE_URL}/admin/products/outstanding`);
  if (params?.limit) url.searchParams.set('limit', String(params.limit));
  if (params?.brand) url.searchParams.set('brand', params.brand);
  if (params?.min_price !== undefined) url.searchParams.set('min_price', String(params.min_price));
  if (params?.max_price !== undefined) url.searchParams.set('max_price', String(params.max_price));
  const res = await fetch(url.toString(), { credentials: 'include' });
  if (!res.ok) throw new Error(`Fetch outstanding failed ${res.status}`);
  return res.json();
}

export async function fetchSentimentByCategory(params?: {
  group_by?: string;
  lv1?: string;
  lv2?: string;
  lv3?: string;
  lv4?: string;
  lv5?: string;
  min_count?: number;
}): Promise<{ data: SentimentGroup[] }> {
  const url = new URL(`${API_BASE_URL}/admin/analytics/sentiment-by-category`);
  url.searchParams.set('group_by', params?.group_by || 'category');
  if (params?.lv1) url.searchParams.set('lv1', params.lv1);
  if (params?.lv2) url.searchParams.set('lv2', params.lv2);
  if (params?.lv3) url.searchParams.set('lv3', params.lv3);
  if (params?.lv4) url.searchParams.set('lv4', params.lv4);
  if (params?.lv5) url.searchParams.set('lv5', params.lv5);
  if (params?.min_count) url.searchParams.set('min_count', String(params.min_count));
  const res = await fetch(url.toString(), { credentials: 'include' });
  if (!res.ok) throw new Error(`Fetch sentiment failed ${res.status}`);
  return res.json();
}

export async function fetchAdminProducts(params?: {
  skip?: number;
  limit?: number;
  min_price?: number;
  max_price?: number;
  brand?: string;
  sort?: string;
}): Promise<{ total: number; results: AdminProduct[] }> {
  const url = new URL(`${API_BASE_URL}/admin/products/by-category`);
  url.searchParams.set('skip', String(params?.skip ?? 0));
  url.searchParams.set('limit', String(params?.limit ?? 50));
  if (params?.min_price !== undefined) url.searchParams.set('min_price', String(params.min_price));
  if (params?.max_price !== undefined) url.searchParams.set('max_price', String(params.max_price));
  if (params?.brand) url.searchParams.set('brand', params.brand);
  if (params?.sort) url.searchParams.set('sort', params.sort);
  const res = await fetch(url.toString(), { credentials: 'include' });
  if (!res.ok) throw new Error(`Fetch admin products failed ${res.status}`);
  return res.json();
}
