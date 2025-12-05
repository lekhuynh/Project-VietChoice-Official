import { API_BASE_URL } from '../config';

// Product shapes aligned with backend, optional for flexibility
export interface ProductDetail {
  Product_ID: number;
  Product_Name: string;
  Image_URL?: string;
  Image_Full_URL?: string;
  Price?: number;
  Source?: string;
  Description?: string;
  Avg_Rating?: number;
  Review_Count?: number;
  Positive_Percent?: number;
  Sentiment_Score?: number;
  Sentiment_Label?: string;
  Origin?: string;
  Brand?: string;
  Product_URL?: string;
  Is_Active?: boolean;
  warning?: string;
}

export interface ProductMin {
  Product_ID: number;
  Product_Name: string;
  Image_URL: string;
  Price: number;
  Avg_Rating: number;
  Sentiment_Label: string;
  Positive_Percent?: number;
  Brand?: string;
}

export interface FavoriteProduct extends ProductMin {
  Favorited_At: string;
}

export interface ProductRisk {
  Product_ID: number;
  Risk_Score: number; // 0..1
  Risk_Level: string; // "Thấp" | "Trung bình" | "Cao"
  Reasons: string[];
}

export type ProductSearchInputType =
  | 'product_search'
  | 'local_product_search'
  | 'chat'
  | 'barcode'
  | 'image'
  | 'barcode_image';

export interface ProductSearchResponse<T = ProductMin> {
  input_type: ProductSearchInputType;
  query: string;
  refined_query?: string | null;
  count: number;
  results: T[];
  ai_message?: string | null;
  total?: number;
  skip?: number;
  limit?: number;
}

type JobStatus<T = unknown> = {
  job_id: string;
  status: string;
  result?: T;
};

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

async function pollJobResult<T>(jobId: string, maxRetries = 20, intervalMs = 1000): Promise<T> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    const res = await fetch(`${API_BASE_URL}/products/jobs/${jobId}`, { credentials: 'include' });
    if (!res.ok) {
      throw new Error('Không lấy được trạng thái tác vụ.');
    }
    const data = (await res.json()) as JobStatus<T>;
    if (data.status === 'finished' && typeof data.result !== 'undefined') {
      return data.result as T;
    }
    if (data.status === 'failed') {
      throw new Error('Tác vụ thất bại.');
    }
    await delay(intervalMs);
  }
  throw new Error('Tác vụ đang xử lý quá lâu, vui lòng thử lại.');
}

// Top rated (legacy helper)
export const fetchTopRatedProducts = async (limit: number): Promise<ProductMin[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/products/recommend/best/1?limit=${limit}`);
    if (!response.ok) return [];
    return (await response.json()) as ProductMin[];
  } catch (err) {
    // eslint-disable-next-line no-console
    console.info('[fetchTopRatedProducts] network error:', err);
    return [];
  }
};

// Search products (now supports queued jobs)
export const fetchSearchProducts = async (
  query: string
): Promise<ProductSearchResponse<ProductMin>> => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/products/search?q=${encodeURIComponent(query)}`,
      { credentials: 'include' }
    );
    if (!response.ok) {
      throw new Error('Không thể tìm kiếm sản phẩm.');
    }
    const data = (await response.json()) as ProductSearchResponse<ProductMin> & {
      message?: string;
      job_id?: string;
      status?: string;
    };

    const payload =
      data?.job_id
        ? await pollJobResult<ProductSearchResponse<ProductMin> | ProductMin[]>(data.job_id)
        : (data as ProductSearchResponse<ProductMin> | ProductMin[]);

    const safeResults = Array.isArray(payload)
      ? (payload as ProductMin[])
      : Array.isArray((payload as ProductSearchResponse<ProductMin>)?.results)
      ? (payload as ProductSearchResponse<ProductMin>).results
      : [];

    const rawType = !Array.isArray(payload)
      ? ((payload as ProductSearchResponse<ProductMin>)?.input_type || '').toString().toLowerCase()
      : 'product_search';
    const normalizedType: ProductSearchInputType =
      rawType === 'chat'
        ? 'chat'
        : rawType === 'barcode'
        ? 'barcode'
        : rawType === 'image'
        ? 'image'
        : rawType === 'barcode_image'
        ? 'barcode_image'
        : 'product_search';

    const aiMessage = !Array.isArray(payload)
      ? (payload as ProductSearchResponse<ProductMin>)?.ai_message ?? (data as any)?.message ?? null
      : (data as any)?.message ?? null;

    return {
      input_type: normalizedType,
      query: !Array.isArray(payload)
        ? (payload as ProductSearchResponse<ProductMin>)?.query ?? query
        : query,
      refined_query: !Array.isArray(payload)
        ? (payload as ProductSearchResponse<ProductMin>)?.refined_query ?? null
        : null,
      count: !Array.isArray(payload) && typeof (payload as ProductSearchResponse<ProductMin>)?.count === 'number'
        ? (payload as ProductSearchResponse<ProductMin>).count
        : safeResults.length,
      results: safeResults,
      ai_message: aiMessage,
    };
  } catch (err) {
    // eslint-disable-next-line no-console
    console.info('[fetchSearchProducts] network error:', err);
    throw new Error('Không thể kết nối tới dịch vụ tìm kiếm. Vui lòng thử lại sau.');
  }
};

// Product detail
export const fetchProductDetail = async (
  productId: string | number
): Promise<ProductDetail> => {
  try {
    const response = await fetch(`${API_BASE_URL}/products/${productId}`, {
      credentials: 'include',
    });
    if (!response.ok) {
      throw new Error('Không tìm thấy sản phẩm.');
    }
    return (await response.json()) as ProductDetail;
  } catch (err) {
    // eslint-disable-next-line no-console
    console.info('[fetchProductDetail] network error:', err);
    throw new Error('Không thể kết nối tới dịch vụ sản phẩm. Vui lòng thử lại sau.');
  }
};

export const fetchProductRisk = async (
  productId: string | number
): Promise<ProductRisk> => {
  const res = await fetch(`${API_BASE_URL}/products/${productId}/risk`, { credentials: 'include' });
  if (!res.ok) {
    throw new Error('Không lấy được rủi ro sản phẩm.');
  }
  return (await res.json()) as ProductRisk;
};

export const fetchRecommendedForProduct = async (
  productId: string | number,
  limit = 6
): Promise<ProductMin[]> => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/products/recommend/best/${productId}?limit=${limit}`,
      { credentials: 'include' }
    );
    if (!response.ok) return [];
    return (await response.json()) as ProductMin[];
  } catch (err) {
    // eslint-disable-next-line no-console
    console.info('[fetchRecommendedForProduct] network error:', err);
    return [];
  }
};

export const fetchProductsByBarcode = async (
  barcode: string
): Promise<ProductMin[]> => {
  const res = await fetch(`${API_BASE_URL}/products/barcode/${encodeURIComponent(barcode)}`, {
    credentials: 'include',
  });
  if (!res.ok) {
    throw new Error('Không lấy được sản phẩm theo mã vạch.');
  }
  const data = (await res.json()) as ProductSearchResponse<ProductMin> & { job_id?: string };
  const payload =
    data?.job_id
      ? await pollJobResult<ProductSearchResponse<ProductMin> | ProductMin[]>(data.job_id)
      : (data as ProductSearchResponse<ProductMin> | ProductMin[]);

  if (Array.isArray(payload)) {
    return payload as ProductMin[];
  }
  return (payload?.results ?? []) as ProductMin[];
};

export const scanProductsByImage = async (
  file: File
): Promise<ProductMin[]> => {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_BASE_URL}/products/scan/image`, {
    method: 'POST',
    body: form,
    credentials: 'include',
  });
  if (!res.ok) {
    throw new Error('Không nhận diện được ảnh sản phẩm.');
  }
  const data = (await res.json()) as ProductSearchResponse<ProductMin> & { job_id?: string };
  const payload =
    data?.job_id
      ? await pollJobResult<ProductSearchResponse<ProductMin> | ProductMin[]>(data.job_id)
      : (data as ProductSearchResponse<ProductMin> | ProductMin[]);
  if (Array.isArray(payload)) {
    return payload as ProductMin[];
  }
  return (payload?.results ?? []) as ProductMin[];
};

// Favorites
export const fetchFavorites = async (): Promise<FavoriteProduct[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/favorite/list`, { credentials: 'include' });
    if (!response.ok) {
      if (response.status === 401) throw new Error('Unauthenticated');
      throw new Error('Lỗi khi tải danh sách yêu thích.');
    }
    const data = await response.json();
    return (data?.favorites as FavoriteProduct[]) || [];
  } catch (err) {
    // eslint-disable-next-line no-console
    console.info('[fetchFavorites] network error:', err);
    return [];
  }
};

export const addFavorite = async (productId: number): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/favorite/add/${productId}`, {
    method: 'POST',
    credentials: 'include',
  });
  if (!response.ok) {
    throw new Error('Thêm vào danh sách yêu thích thất bại.');
  }
};

export const removeFavorite = async (productId: number): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/favorite/remove/${productId}`, {
    method: 'DELETE',
    credentials: 'include',
  });
  if (!response.ok) {
    throw new Error('Xóa khỏi danh sách yêu thích thất bại.');
  }
};

export interface LocalSearchParams {
  limit?: number;
  skip?: number;
  lv1?: string;
  lv2?: string;
  lv3?: string;
  lv4?: string;
  lv5?: string;
  min_price?: number;
  max_price?: number;
  brand?: string;
  min_rating?: number;
  sort?: string;
  is_vietnam_origin?: boolean;
  is_vietnam_brand?: boolean;
  positive_over?: number;
}

export const fetchLocalProducts = async (
  query: string,
  params: LocalSearchParams = {}
): Promise<ProductSearchResponse<ProductMin>> => {
  try {
    const usp = new URLSearchParams();
    usp.set('q', query);
    const {
      limit = 20,
      skip = 0,
      lv1,
      lv2,
      lv3,
      lv4,
      lv5,
      min_price,
      max_price,
      brand,
      min_rating,
      sort,
      is_vietnam_origin,
      is_vietnam_brand,
      positive_over,
    } = params;

    usp.set('limit', String(limit));
    usp.set('skip', String(skip));
    if (lv1) usp.set('lv1', lv1);
    if (lv2) usp.set('lv2', lv2);
    if (lv3) usp.set('lv3', lv3);
    if (lv4) usp.set('lv4', lv4);
    if (lv5) usp.set('lv5', lv5);
    if (min_price !== undefined) usp.set('min_price', String(min_price));
    if (max_price !== undefined) usp.set('max_price', String(max_price));
    if (brand) usp.set('brand', brand);
    if (min_rating !== undefined) usp.set('min_rating', String(min_rating));
    if (sort) usp.set('sort', sort);
    if (is_vietnam_origin !== undefined) usp.set('is_vietnam_origin', String(is_vietnam_origin));
    if (is_vietnam_brand !== undefined) usp.set('is_vietnam_brand', String(is_vietnam_brand));
    if (positive_over !== undefined) usp.set('positive_over', String(positive_over));
    const response = await fetch(
      `${API_BASE_URL}/products/search/local?${usp.toString()}`,
      { credentials: 'include' }
    );
    if (!response.ok) {
      throw new Error('Khong the tim kiem san pham trong kho du lieu.');
    }
    const data = (await response.json()) as ProductSearchResponse<ProductMin> & { message?: string };
    const safeResults = Array.isArray(data?.results) ? data.results : [];
    return {
      input_type: data?.input_type ?? 'local_product_search',
      query: data?.query ?? query,
      refined_query: data?.refined_query ?? null,
      count: typeof data?.count === 'number' ? data.count : safeResults.length,
      total: typeof data?.total === 'number' ? data.total : safeResults.length,
      skip: typeof data?.skip === 'number' ? data.skip : skip,
      limit: typeof data?.limit === 'number' ? data.limit : limit,
      results: safeResults,
      ai_message: data?.ai_message ?? null,
    };
  } catch (err) {
    // eslint-disable-next-line no-console
    console.info('[fetchLocalProducts] network error:', err);
    throw new Error('Khong the ket noi toi dich vu tim kiem noi bo. Vui long thu lai sau.');
  }
};
