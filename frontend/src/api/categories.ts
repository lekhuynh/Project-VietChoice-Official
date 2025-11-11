import { API_BASE_URL } from '../config';

export interface CategoryNode {
  name: string;
  children: CategoryNode[];
}

export const fetchCategoryTree = async (): Promise<CategoryNode[]> => {
  try {
    const res = await fetch(`${API_BASE_URL}/categories/tree`, { credentials: 'include' });
    if (!res.ok) return [];
    const data = (await res.json()) as CategoryNode[];
    return Array.isArray(data) ? data : [];
  } catch (e) {
    // eslint-disable-next-line no-console
    console.info('[fetchCategoryTree] network error:', e);
    return [];
  }
};

