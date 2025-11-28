import React from 'react';
import { Link } from 'react-router-dom';
import { StarIcon, ThumbsUpIcon } from 'lucide-react';
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
  const { id, name, image, price, rating, positivePercent, brand } = product;
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
      </div>
    </div>
  );
};
export default ProductCard;
