import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { StarIcon, ChevronLeftIcon, ChevronRightIcon } from 'lucide-react';
import { fetchRecommendedForProduct, fetchTopRatedProducts, type ProductMin } from '../../api/products';

interface RecommendationsProps {
  title?: string;
  productId?: number;
  limit?: number;
}

const currency = (v?: number) => (typeof v === 'number' ? v.toLocaleString('vi-VN') + ' ₫' : '');

const Recommendations: React.FC<RecommendationsProps> = ({ title = 'Gợi ý cho bạn', productId, limit = 12 }) => {
  const [items, setItems] = useState<ProductMin[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);
    (async () => {
      try {
        let recs: ProductMin[] = [];
        if (productId) {
          recs = await fetchRecommendedForProduct(productId, limit).catch(() => []);
        }
        if ((!recs || recs.length === 0)) {
          recs = await fetchTopRatedProducts(limit).catch(() => []);
        }
        if (!mounted) return;
        setItems(recs || []);
      } catch (e: any) {
        if (!mounted) return;
        setError(e?.message || 'Không tải được gợi ý');
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, [productId, limit]);

  const scrollBy = (container: HTMLDivElement | null, delta: number) => {
    if (!container) return;
    container.scrollBy({ left: delta, behavior: 'smooth' });
  };

  const [containerEl, setContainerEl] = useState<HTMLDivElement | null>(null);

  return (
    <div className="mt-10">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold">{title}</h3>
        <div className="hidden sm:flex gap-2">
          <button
            aria-label="Cuộn trái"
            className="p-1.5 rounded-full border text-gray-600 hover:bg-gray-50"
            onClick={() => scrollBy(containerEl, -300)}
          >
            <ChevronLeftIcon className="h-5 w-5" />
          </button>
          <button
            aria-label="Cuộn phải"
            className="p-1.5 rounded-full border text-gray-600 hover:bg-gray-50"
            onClick={() => scrollBy(containerEl, 300)}
          >
            <ChevronRightIcon className="h-5 w-5" />
          </button>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="animate-pulse bg-white rounded-xl border p-3">
              <div className="h-28 bg-gray-200 rounded mb-3" />
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
              <div className="h-4 bg-gray-200 rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="p-4 bg-red-50 text-red-700 border border-red-200 rounded">{error}</div>
      ) : items.length === 0 ? (
        <div className="p-4 bg-gray-50 text-gray-600 rounded">Chưa có gợi ý phù hợp.</div>
      ) : (
        <div className="relative">
          <div
            ref={setContainerEl}
            className="flex gap-4 overflow-x-auto scroll-smooth pb-2"
          >
            {items.map((p) => (
              <Link
                key={p.Product_ID}
                to={`/product/${p.Product_ID}`}
                className="min-w-[180px] w-[180px] flex-shrink-0 bg-white rounded-xl border hover:shadow transition overflow-hidden"
              >
                <div className="h-28 overflow-hidden">
                  <img src={p.Image_URL} alt={p.Product_Name} className="w-full h-full object-cover" />
                </div>
                <div className="p-3">
                  <h4 className="text-sm font-medium line-clamp-2 min-h-[2.5rem]">{p.Product_Name}</h4>
                  <div className="mt-1 flex items-center justify-between text-sm">
                    <span className="text-emerald-600 font-medium">{currency(p.Price)}</span>
                    <span className="inline-flex items-center gap-1 text-gray-600">
                      <StarIcon className="h-4 w-4 text-yellow-400" />
                      {p.Avg_Rating?.toFixed ? p.Avg_Rating.toFixed(1) : p.Avg_Rating}
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Recommendations;

