import React from 'react';
import { type FC } from 'react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

const Pagination: FC<PaginationProps> = ({ currentPage, totalPages, onPageChange }) => {
  if (totalPages <= 1) return null;

  const pages: number[] = [];
  const start = Math.max(1, currentPage - 2);
  const end = Math.min(totalPages, currentPage + 2);
  for (let i = start; i <= end; i++) pages.push(i);

  return (
    <nav className="mt-6 flex items-center justify-center space-x-2" aria-label="Pagination">
      <button
        onClick={() => onPageChange(Math.max(1, currentPage - 1))}
        disabled={currentPage === 1}
        className={`px-3 py-1 rounded-md border ${currentPage === 1 ? 'text-gray-400 border-gray-200' : 'text-gray-700 hover:bg-gray-100'}`}
      >
        Previous
      </button>

      {start > 1 && (
        <button onClick={() => onPageChange(1)} className="px-3 py-1 rounded-md border text-gray-700 hover:bg-gray-100">1</button>
      )}

      {start > 2 && <span className="px-2">...</span>}

      {pages.map((p) => (
        <button
          key={p}
          onClick={() => onPageChange(p)}
          className={`px-3 py-1 rounded-md border ${p === currentPage ? 'bg-emerald-600 text-white border-emerald-600' : 'text-gray-700 hover:bg-gray-100'}`}
        >
          {p}
        </button>
      ))}

      {end < totalPages - 1 && <span className="px-2">...</span>}

      {end < totalPages && (
        <button onClick={() => onPageChange(totalPages)} className="px-3 py-1 rounded-md border text-gray-700 hover:bg-gray-100">{totalPages}</button>
      )}

      <button
        onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
        disabled={currentPage === totalPages}
        className={`px-3 py-1 rounded-md border ${currentPage === totalPages ? 'text-gray-400 border-gray-200' : 'text-gray-700 hover:bg-gray-100'}`}
      >
        Next
      </button>
    </nav>
  );
};

export default Pagination;
