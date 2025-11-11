import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { SearchIcon, ScanIcon, ShoppingBagIcon, UserIcon, MenuIcon, XIcon } from 'lucide-react';
const Navbar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();
  const navigation = [
    {
      name: 'Trang chủ',
      href: '/',
      icon: <SearchIcon className="w-5 h-5" />,
    },
    {
      name: 'Quét mã',
      href: '/scanner',
      icon: <ScanIcon className="w-5 h-5" />,
    },
    {
      name: 'Sản phẩm',
      href: '/products',
      icon: <ShoppingBagIcon className="w-5 h-5" />,
    },
    {
      name: 'Tài khoản',
      href: '/profile',
      icon: <UserIcon className="w-5 h-5" />,
    },
  ];
  return (
    <header className="bg-white shadow-md">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center py-4">
          <Link to="/" className="flex items-center space-x-2">
            <span className="font-bold text-xl text-emerald-600">VietChoice</span>
          </Link>
          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              type="button"
              className="text-gray-500 hover:text-gray-600"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
            >
              {isMenuOpen ? <XIcon className="h-6 w-6" /> : <MenuIcon className="h-6 w-6" />}
            </button>
          </div>
          {/* Desktop navigation */}
          <nav className="hidden md:flex space-x-8">
            {navigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium ${location.pathname === item.href ? 'text-emerald-600 bg-emerald-50' : 'text-gray-600 hover:text-emerald-600 hover:bg-emerald-50'}`}
              >
                {item.icon}
                <span>{item.name}</span>
              </Link>
            ))}
            
          </nav>
        </div>
        {/* Mobile menu */}
        {isMenuOpen && (
          <div className="md:hidden py-2 pb-4">
            {navigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center space-x-3 px-4 py-3 text-base font-medium ${location.pathname === item.href ? 'text-emerald-600 bg-emerald-50' : 'text-gray-600 hover:text-emerald-600 hover:bg-emerald-50'}`}
                onClick={() => setIsMenuOpen(false)}
              >
                {item.icon}
                <span>{item.name}</span>
              </Link>
            ))}
            
          </div>
        )}
      </div>
    </header>
  );
};
export default Navbar;


