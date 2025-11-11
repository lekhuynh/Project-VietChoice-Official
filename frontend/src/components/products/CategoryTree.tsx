import React, { useMemo, useState } from 'react';
import { ChevronRight, ChevronDown, ListTree, X } from 'lucide-react';
import type { CategoryNode } from '../../api/categories';

interface CategoryTreeProps {
  nodes: CategoryNode[];
  selectedPath: string[];
  onSelect: (path: string[]) => void;
}

const pathKey = (path: string[]) => path.join(' > ');

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

  const toggle = (path: string[]) => {
    const key = pathKey(path);
    setOpen((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const renderNodes = (items: CategoryNode[], parentPath: string[] = []) => (
    <ul className="space-y-0.5">
      {items.map((n) => {
        const currentPath = [...parentPath, n.name];
        const key = pathKey(currentPath);
        // Only open when explicitly toggled, or when searching
        const selectedPrefixOpen = pathKey(selectedPath.slice(0, currentPath.length)) === key;
        const isOpen = open[key] ?? (!!q ? true : selectedPrefixOpen);
        const isSelected = pathKey(selectedPath) === key;
        const hasChildren = (n.children?.length ?? 0) > 0;
        return (
          <li key={key} className="group">
            <div
              className={`flex items-center px-2 py-1.5 rounded-md cursor-pointer border border-transparent group-hover:border-gray-200 ${
                isSelected ? 'bg-emerald-50 text-emerald-700 border-emerald-100' : 'hover:bg-gray-50'
              }`}
            >
              {hasChildren ? (
                <button
                  className="mr-2 text-gray-500 hover:text-gray-700"
                  onClick={(e) => {
                    e.stopPropagation();
                    toggle(currentPath);
                  }}
                  aria-label={isOpen ? 'Thu gá»n' : 'Má»Ÿ rá»™ng'}
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
                    // Select parent category and ensure it is expanded
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
    <div className="text-gray-800">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
          <ListTree className="h-4 w-4 text-emerald-600" />
          Danh mục sản phẩm
        </div>
        {selectedPath.length > 0 && (
          <button
            className="text-xs text-emerald-700 hover:underline"
            onClick={() => onSelect([])}
            title="Bỏ chọn"
          >
            Bỏ chọn
          </button>
        )}
      </div>
      <div className="relative mb-2">
        <input
          className="w-full px-3 py-2 text-sm border rounded-md pr-8"
          placeholder="Tìm trong danh mục..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        {q && (
          <button className="absolute right-2 top-2 text-gray-400 hover:text-gray-600" onClick={() => setQ('')}>
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
      <div className="max-h-96 overflow-y-auto pr-1 custom-scrollbar">
        {filtered?.length ? (
          renderNodes(filtered)
        ) : (
          <div className="text-sm text-gray-500 py-4">KhÃ´ng cÃ³ danh má»¥c.</div>
        )}
      </div>
    </div>
  );
};

export default CategoryTree;

