import React from 'react';
import { Link } from 'react-router-dom';
import { StarIcon, ThumbsUpIcon, ShoppingCartIcon } from 'lucide-react';
import { type FC } from 'react';
import { type Product } from '../../types';

/**
 * Props cho `ProductCard`.
 *
 * @property product - đối tượng `Product` (xem `src/types/index.ts`) sẽ được hiển thị trong thẻ.
 */
interface ProductCardProps {
  product: Product;
}

const ProductCard: FC<ProductCardProps> = ({ product }) => {
  const { id, name, image, price, rating, positivePercent, sentiment, brand } = product;
  // Determine sentiment color
  const getSentimentColor = (sentiment: Product['sentiment']) => {
    switch (sentiment) {
      case 'positive':
        return 'bg-emerald-100 text-emerald-800';
      case 'neutral':
        return 'bg-blue-100 text-blue-800';
      case 'negative':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };
  const sentimentLabel: Record<NonNullable<Product['sentiment']>, string> = {
    positive: 'Tích cực',
    neutral: 'Trung lập',
    negative: 'Tiêu cực',
  };
  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300">
      <Link to={`/product/${id}`}>
        <div className="h-48 overflow-hidden">
          <img
            src={image}
            alt={name}
            className="w-full h-full object-cover transform hover:scale-105 transition-transform duration-300"
          />
        </div>
      </Link>
      <div className="p-4">
        <Link to={`/product/${id}`} className="block">
          <h3 className="text-sm font-medium text-gray-900 line-clamp-2 h-10">{name}</h3>
        </Link>
        <div className="mt-1 flex justify-between items-center">
          <span className="text-emerald-600 font-medium">{price}</span>
          <span className="text-xs text-gray-500">{brand}</span>
        </div>
        <div className="mt-2 flex items-center">
          <div className="flex items-center">
            <StarIcon className="h-4 w-4 text-yellow-400" />
            <span className="ml-1 text-xs text-gray-600">{rating}/5</span>
          </div>
          <span className="mx-2 text-gray-300">|</span>
          <div className="flex items-center">
            <ThumbsUpIcon className="h-4 w-4 text-emerald-500" />
            <span className="ml-1 text-xs text-gray-600">{positivePercent}%</span>
          </div>
        </div>
        <div className="mt-3 flex justify-between items-center">
          <span className={`text-xs px-2 py-1 rounded-full ${getSentimentColor(sentiment)}`}>
            {sentiment ? sentimentLabel[sentiment] : 'Không xác định'}
          </span>
          <div className="flex space-x-1">
            <a
              href="https://shopee.vn"
              target="_blank"
              rel="noopener noreferrer"
              className="p-1 bg-orange-500 text-white rounded"
              title="Mua trên Shopee"
            >
              <ShoppingCartIcon className="h-3 w-3" />
            </a>
            <a
              href="https://lazada.vn"
              target="_blank"
              rel="noopener noreferrer"
              className="p-1 bg-blue-500 text-white rounded"
              title="Mua trên Lazada"
            >
              <ShoppingCartIcon className="h-3 w-3" />
            </a>
            <a
              href="https://tiki.vn"
              target="_blank"
              rel="noopener noreferrer"
              className="p-1 bg-teal-500 text-white rounded"
              title="Mua trên Tiki"
            >
              <ShoppingCartIcon className="h-3 w-3" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};
export default ProductCard;
