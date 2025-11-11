import { API_BASE_URL } from '../config';

export interface SearchHistoryItemProduct {
  Product_ID: number;
  Product_Name: string;
  Image_URL?: string;
  Price?: number;
  Avg_Rating?: number;
}

export interface SearchHistoryItem {
  History_ID: number;
  Query: string;
  Result_Count: number;
  Created_At: string;
  Products: SearchHistoryItemProduct[];
}

export interface SearchHistoryResponse {
  user_id: number;
  history: SearchHistoryItem[];
}

export const fetchSearchHistory = async (): Promise<SearchHistoryResponse> => {
  const res = await fetch(`${API_BASE_URL}/users/search`, { credentials: 'include' });
  if (!res.ok) {
    if (res.status === 401) throw new Error('Unauthenticated');
    throw new Error('Không lấy được lịch sử tìm kiếm');
  }
  return (await res.json()) as SearchHistoryResponse;
};

export const deleteSearchHistoryItem = async (historyId: number): Promise<void> => {
  const res = await fetch(`${API_BASE_URL}/users/delete/search/${historyId}`, {
    method: 'DELETE',
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Xóa lịch sử tìm kiếm thất bại');
};

export const deleteAllSearchHistory = async (): Promise<void> => {
  const res = await fetch(`${API_BASE_URL}/users/delete/search`, {
    method: 'DELETE',
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Xóa tất cả lịch sử tìm kiếm thất bại');
};

export interface ViewedHistoryItem {
  Viewed_At: string;
  Product_ID: number;
  Product_Name: string;
  Image_URL?: string;
  Price?: number;
  Avg_Rating?: number;
}

export interface ViewedHistoryResponse {
  user_id: number;
  viewed: ViewedHistoryItem[];
}

export const fetchViewedHistory = async (): Promise<ViewedHistoryResponse> => {
  const res = await fetch(`${API_BASE_URL}/users/viewed`, { credentials: 'include' });
  if (!res.ok) {
    if (res.status === 401) throw new Error('Unauthenticated');
    throw new Error('Không lấy được lịch sử đã xem');
  }
  return (await res.json()) as ViewedHistoryResponse;
};

export const deleteViewedHistoryItem = async (productId: number): Promise<void> => {
  const res = await fetch(`${API_BASE_URL}/users/delete/viewed/${productId}`, {
    method: 'DELETE',
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Xóa khỏi lịch sử xem thất bại');
};

export const deleteAllViewedHistory = async (): Promise<void> => {
  const res = await fetch(`${API_BASE_URL}/users/delete/viewed`, {
    method: 'DELETE',
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Xóa tất cả lịch sử xem thất bại');
};

