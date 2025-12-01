import React, { useMemo, useState } from 'react';
import { ChevronRight, ChevronDown, ListTree, Search, X } from 'lucide-react';
import type { CategoryNode } from '../../api/categories';

interface CategoryTreeProps {
  nodes: CategoryNode[];
  selectedPath: string[];
  onSelect: (path: string[]) => void;
}

const pathKey = (path: string[]) => path.join(' > ');
const countNodes = (items: CategoryNode[]): number =>
  items.reduce((sum, n) => sum + 1 + (n.children ? countNodes(n.children) : 0), 0);

function filterNodes(nodes: CategoryNode[], q: string): CategoryNode[] {
  if (!q.trim()) return nodes;
  const query = q.trim().toLowerCase();
  const walk = (list: CategoryNode[]): CategoryNode[] =>
    list
      .map((n) => {
        const filteredChildren = n.children ? walk(n.children) : [];
        const selfMatch = n.name.toLowerCase().includes(query);
        if (selfMatch || filteredChildren.length) {
          return { name: n.name, children: filteredChildren } as CategoryNode;
        }
        return null;
      })
      .filter(Boolean) as CategoryNode[];
  return walk(nodes);
}

const CategoryTree: React.FC<CategoryTreeProps> = ({ nodes, selectedPath, onSelect }) => {
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const [q, setQ] = useState('');

  const filtered = useMemo(() => filterNodes(nodes, q), [nodes, q]);
  const visibleCount = useMemo(() => countNodes(filtered || []), [filtered]);
  const hasSelection = selectedPath.length > 0;
  const selectedLabel = hasSelection ? selectedPath.join(' / ') : '';

  const toggle = (path: string[]) => {
    const key = pathKey(path);
    setOpen((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const renderNodes = (items: CategoryNode[], parentPath: string[] = []) => (
    <ul className="space-y-1.5">
      {items.map((n) => {
        const currentPath = [...parentPath, n.name];
        const key = pathKey(currentPath);
        const selectedPrefixOpen = pathKey(selectedPath.slice(0, currentPath.length)) === key;
        const isOpen = open[key] ?? (!!q ? true : selectedPrefixOpen);
        const isSelected = pathKey(selectedPath) === key;
        const hasChildren = (n.children?.length ?? 0) > 0;
        return (
          <li key={key} className="group">
            <div
              className={`flex items-center px-3 py-2.5 rounded-xl cursor-pointer border border-transparent leading-5 transition-all duration-150 ${
                isSelected
                  ? 'bg-gradient-to-r from-emerald-50 to-emerald-100 text-emerald-800 border-emerald-100 shadow-sm'
                  : 'bg-white hover:bg-gray-50 hover:border-gray-200'
              }`}
            >
              {hasChildren ? (
                <button
                  className="mr-2 text-gray-500 hover:text-gray-700 transition-colors"
                  onClick={(e) => {
                    e.stopPropagation();
                    toggle(currentPath);
                  }}
                  aria-label={isOpen ? 'Thu gon' : 'Mo rong'}
                >
                  {isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                </button>
              ) : (
                <span className="w-4 mr-2" />
              )}
              <button
                className={`flex-1 text-left text-sm truncate ${hasChildren ? 'text-gray-800' : 'text-gray-900'}`}
                title={currentPath.join(' / ')}
                onClick={() => {
                  if (hasChildren) {
                    onSelect(currentPath);
                    setOpen((prev) => ({ ...prev, [key]: true }));
                  } else {
                    onSelect(currentPath);
                  }
                }}
              >
                {n.name}
              </button>
            </div>
            {hasChildren && isOpen && (
              <div className="ml-4 border-l border-gray-200 pl-2 mt-1">
                {renderNodes(n.children, currentPath)}
              </div>
            )}
          </li>
        );
      })}
    </ul>
  );

  return (
    <div className="text-gray-800 rounded-2xl border border-gray-200/70 bg-white shadow-[0_4px_18px_rgba(0,0,0,0.06)] p-4">
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2 text-sm font-semibold text-gray-900">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-100">
              <ListTree className="h-4 w-4" />
            </span>
            <div className="flex items-center gap-2">
              <span>Danh muc san pham</span>
              <span className="px-2 py-0.5 text-[11px] rounded-full bg-gray-50 text-emerald-700 border border-gray-200">
                {visibleCount}
              </span>
            </div>
          </div>
          {hasSelection && (
            <div className="mt-1 text-[12px] text-gray-700 line-clamp-1">Dang chon: {selectedLabel}</div>
          )}
        </div>
        {hasSelection && (
          <button
            className="text-xs text-emerald-700 hover:text-emerald-800 font-medium"
            onClick={() => onSelect([])}
            title="Bo chon"
          >
            Bo chon
          </button>
        )}
      </div>
      <div className="relative mb-4">
        <Search className="h-4 w-4 text-gray-400 absolute left-3 top-2.5 pointer-events-none" />
        <input
          className="w-full pl-9 pr-9 py-2.5 text-sm border border-gray-200 rounded-xl bg-white focus:ring-2 focus:ring-emerald-400/30 focus:border-emerald-400 transition-all"
          placeholder="Tim danh muc..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        {q && (
          <button
            className="absolute right-2 top-2 text-gray-400 hover:text-gray-600 rounded-full p-1"
            onClick={() => setQ('')}
            title="Xoa tim kiem"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
      <div className="max-h-96 overflow-y-auto pr-2 custom-scrollbar space-y-1">
        {filtered?.length ? (
          renderNodes(filtered)
        ) : (
          <div className="text-sm text-gray-500 py-6 text-center">Khong co danh muc.</div>
        )}
      </div>
    </div>
  );
};

export default CategoryTree;
