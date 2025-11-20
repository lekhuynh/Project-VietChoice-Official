import React from 'react';
import { type FC } from 'react';
import ProductCard from './ProductCard';
import Pagination from './Pagination';
import { type Product } from '../../types';

interface ProductListProps {
  products: Product[];
  currentPage: number;
  pageSize: number;
  totalProducts: number;
  onPageChange: (page: number) => void;
}

const ProductList: FC<ProductListProps> = ({ products, currentPage, pageSize, totalProducts, onPageChange }) => {
  const totalPages = Math.max(1, Math.ceil(totalProducts / pageSize));

  return (
    <div>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {products.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>

      <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={onPageChange} />
    </div>
  );
};

export default ProductList;
