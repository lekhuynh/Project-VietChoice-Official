import React, { useEffect, useMemo, useState } from 'react';
import { SearchIcon, FilterIcon, Star, ArrowUp, ArrowDown, ArrowUpDown } from 'lucide-react';
import ProductList from '../components/products/ProductList';
import CategoryTree from '../components/products/CategoryTree';
import { type Product } from '../types';
import { fetchCategoryTree, type CategoryNode } from '../api/categories';
import { fetchProductsByCategoryAndFilters, type DbProduct, type ProductFilterParams } from '../api/products_filters';
import { fetchSearchProducts, type ProductMin } from '../api/products';

const formatPrice = (v?: number) => {
  if (v === undefined || v === null) return '—';
  try {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(Number(v));
  } catch {
    return `${v} đ`;
  }
};

const mapDbToProduct = (p: DbProduct): Product => ({
  id: p.Product_ID,
  name: p.Product_Name,
  image: p.Image_URL || '',
  price: formatPrice(Number(p.Price)),
  rating: Number(p.Avg_Rating || 0),
  positivePercent: Number(p.Positive_Percent || 0),
  sentiment: (p.Sentiment_Label?.toLowerCase() as Product['sentiment']) || undefined,
  brand: p.Brand,
  origin: p.Origin,
});

const mapMinToProduct = (p: ProductMin): Product => ({
  id: p.Product_ID,
  name: p.Product_Name,
  image: p.Image_URL || '',
  price: formatPrice(Number(p.Price)),
  rating: Number(p.Avg_Rating || 0),
  positivePercent: 0,
  sentiment: (p.Sentiment_Label?.toLowerCase() as Product['sentiment']) || undefined,
});

const Products: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(8);

  const [categoryTree, setCategoryTree] = useState<CategoryNode[]>([]);
  const [selectedPath, setSelectedPath] = useState<string[]>([]);

  const [brand, setBrand] = useState('');
  const [minPrice, setMinPrice] = useState<number | undefined>();
  const [maxPrice, setMaxPrice] = useState<number | undefined>();
  const [minRating, setMinRating] = useState<number | undefined>();
  const [sort, setSort] = useState<ProductFilterParams['sort']>();
  const [isVnOrigin, setIsVnOrigin] = useState(false);
  const [isVnBrand, setIsVnBrand] = useState(false);
  const [positiveOver, setPositiveOver] = useState<number | undefined>();

  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const totalProducts = products.length;

  useEffect(() => {
    fetchCategoryTree().then(setCategoryTree).catch(() => setCategoryTree([]));
    applyFilters();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const currentCategoryParams = useMemo(() => {
    const [lv1, lv2, lv3, lv4, lv5] = selectedPath;
    const params: ProductFilterParams = {};
    if (lv1) params.lv1 = lv1;
    if (lv2) params.lv2 = lv2;
    if (lv3) params.lv3 = lv3;
    if (lv4) params.lv4 = lv4;
    if (lv5) params.lv5 = lv5;
    return params;
  }, [selectedPath]);

  // Re-apply filters when category changes to avoid double-click issues
  useEffect(() => {
    applyFilters();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentCategoryParams]);

  const applyFilters = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchProductsByCategoryAndFilters({
        ...currentCategoryParams,
        brand: brand || undefined,
        min_price: minPrice,
        max_price: maxPrice,
        min_rating: minRating,
        sort,
        is_vietnam_origin: isVnOrigin || undefined,
        is_vietnam_brand: isVnBrand || undefined,
        positive_over: positiveOver,
      });
      setProducts(data.map(mapDbToProduct));
      setPage(1);
    } catch (e: any) {
      setError(e?.message || 'Lỗi tải sản phẩm');
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const doSearch = async () => {
    if (!searchTerm.trim()) return applyFilters();
    setLoading(true);
    setError(null);
    try {
      const { products: items } = await fetchSearchProducts(searchTerm.trim());
      setProducts(items.map(mapMinToProduct));
      setPage(1);
    } catch (e: any) {
      setError(e?.message || 'Lỗi tìm kiếm');
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Sản phẩm</h1>

      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-4 gap-3">
        <div className="relative w-full md:w-96">
          <input
            type="text"
            placeholder="Tìm kiếm sản phẩm..."
            className="w-full pl-10 pr-20 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') doSearch(); }}
          />
          <SearchIcon className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
          <button
            onClick={doSearch}
            className="absolute right-2 top-1.5 px-3 py-1.5 bg-emerald-600 text-white rounded text-sm"
          >
            Tìm
          </button>
        </div>
        <div className="flex items-center gap-2 w-full md:w-auto">
          <button
            className="flex items-center text-sm text-gray-700 hover:text-emerald-600"
            onClick={() => setShowFilters(!showFilters)}
          >
            <FilterIcon className="h-4 w-4 mr-1" />
            Bộ lọc
          </button>
          <div className="flex items-center space-x-2">
            <label className="text-sm text-gray-600">Hiển thị</label>
            <select
              value={pageSize}
              onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
              className="border border-gray-300 rounded px-2 py-1 text-sm"
            >
              <option value={8}>8 / trang</option>
              <option value={12}>12 / trang</option>
              <option value={16}>16 / trang</option>
            </select>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <aside className="md:col-span-1 space-y-4 md:sticky top-4 self-start">
          <div className="bg-white rounded-lg border shadow-sm p-3">
            <CategoryTree
              nodes={categoryTree}
              selectedPath={selectedPath}
              onSelect={(path) => { setSelectedPath(path); setPage(1); }}
            />
          </div>

          {showFilters && (
            <div className="bg-white rounded-lg border shadow-sm p-3">
              <h3 className="font-medium mb-3">Bộ lọc</h3>
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-gray-600 mb-1">Thương hiệu</div>
                  <input
                    value={brand}
                    onChange={(e) => setBrand(e.target.value)}
                    placeholder="Nhập thương hiệu, phân tách bằng dấu phẩy"
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
                <div>
                  <div className="text-sm text-gray-600 mb-1">Khoảng giá (đ)</div>
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      type="number"
                      inputMode="numeric"
                      placeholder="Từ"
                      value={minPrice ?? ''}
                      onChange={(e) => setMinPrice(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-full px-3 py-2 border rounded-md"
                    />
                    <input
                      type="number"
                      inputMode="numeric"
                      placeholder="Đến"
                      value={maxPrice ?? ''}
                      onChange={(e) => setMaxPrice(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-full px-3 py-2 border rounded-md"
                    />
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 mb-1">Đánh giá tối thiểu</div>
                  <div className="flex flex-col gap-2">
                    {[
                      { label: 'Từ 4.5★', value: 4.5 },
                      { label: 'Từ 4★', value: 4 },
                      { label: 'Từ 3★', value: 3 },
                      { label: 'Bất kỳ', value: undefined },
                    ].map((opt) => (
                      <button
                        key={String(opt.value)}
                        onClick={() => setMinRating(opt.value as any)}
                        className={`flex items-center justify-between px-3 py-2 rounded border text-sm ${
                          (opt.value ?? '') === (minRating ?? '') ? 'border-emerald-500 bg-emerald-50 text-emerald-700' : 'border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        <span className="flex items-center gap-2">
                          <Star className="h-4 w-4 text-yellow-500" /> {opt.label}
                        </span>
                        {(opt.value ?? '') === (minRating ?? '') && <span className="text-emerald-600">✓</span>}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="flex flex-col gap-2">
                  <label className="inline-flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={isVnOrigin} onChange={(e) => setIsVnOrigin(e.target.checked)} />
                    Hàng sản xuất tại Việt Nam
                  </label>
                  <label className="inline-flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={isVnBrand} onChange={(e) => setIsVnBrand(e.target.checked)} />
                    Thương hiệu Việt Nam
                  </label>
                </div>
                <div>
                  <div className="text-sm text-gray-600 mb-1">Tỷ lệ đánh giá tích cực</div>
                  <div className="flex flex-wrap gap-2">
                    {[
                      { label: 'Bất kỳ', value: undefined },
                      { label: '≥ 70%', value: 70 },
                      { label: '≥ 80%', value: 80 },
                      { label: '≥ 90%', value: 90 },
                    ].map((opt) => (
                      <button
                        key={String(opt.value)}
                        onClick={() => setPositiveOver(opt.value as any)}
                        className={`px-3 py-1.5 rounded-full text-xs border ${
                          (opt.value ?? '') === (positiveOver ?? '') ? 'border-emerald-500 bg-emerald-50 text-emerald-700' : 'border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="flex gap-2 pt-1">
                  <button onClick={applyFilters} className="flex-1 px-3 py-2 bg-emerald-600 text-white rounded-md text-sm">Áp dụng</button>
                  <button
                    onClick={() => { setBrand(''); setMinPrice(undefined); setMaxPrice(undefined); setMinRating(undefined); setIsVnOrigin(false); setIsVnBrand(false); setPositiveOver(undefined); setSort(undefined); applyFilters(); }}
                    className="px-3 py-2 bg-gray-100 text-gray-700 rounded-md text-sm"
                  >
                    Xóa lọc
                  </button>
                </div>
              </div>
            </div>
          )}
        </aside>

        <section className="md:col-span-3">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm text-gray-600">Tổng: {totalProducts} sản phẩm</div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Sắp xếp</span>
              <div className="flex items-center gap-2">
                <button
                  className={`px-3 py-1.5 rounded-full text-xs border ${!sort ? 'border-emerald-500 bg-emerald-50 text-emerald-700' : 'border-gray-300 hover:bg-gray-50'}`}
                  onClick={() => { setSort(undefined); applyFilters(); }}
                >
                  Mặc định
                </button>
                <button
                  className={`px-3 py-1.5 rounded-full text-xs border ${sort === 'rating_desc' ? 'border-emerald-500 bg-emerald-50 text-emerald-700' : 'border-gray-300 hover:bg-gray-50'}`}
                  onClick={() => { setSort('rating_desc'); applyFilters(); }}
                >
                  Đánh giá
                </button>
                <button
                  className={`px-3 py-1.5 rounded-full text-xs border flex items-center gap-1 ${sort?.startsWith('price_') ? 'border-emerald-500 bg-emerald-50 text-emerald-700' : 'border-gray-300 hover:bg-gray-50'}`}
                  onClick={() => {
                    const next = sort === 'price_asc' ? 'price_desc' : 'price_asc';
                    setSort(next as any);
                    applyFilters();
                  }}
                  title="Sắp xếp theo giá"
                >
                  Giá {sort === 'price_asc' ? <ArrowUp className="h-3 w-3" /> : sort === 'price_desc' ? <ArrowDown className="h-3 w-3" /> : <ArrowUpDown className="h-3 w-3" />}
                </button>
              </div>
            </div>
          </div>

          {loading ? (
            <div className="py-10 text-center text-gray-500">Đang tải sản phẩm...</div>
          ) : error ? (
            <div className="py-10 text-center text-red-600">{error}</div>
          ) : (
            <>
              <ProductList products={products} currentPage={page} pageSize={pageSize} onPageChange={(p) => setPage(p)} />
              {products.length === 0 && (
                <div className="text-center py-10">
                  <p className="text-gray-500">Không có sản phẩm phù hợp.</p>
                </div>
              )}
            </>
          )}
        </section>
      </div>
    </div>
  );
};

export default Products;
