import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { SearchIcon, ScanIcon, ShoppingBagIcon, UserIcon, MenuIcon, XIcon } from 'lucide-react';
import { fetchUserProfile } from '../../api/user';
import { ShieldCheckIcon } from 'lucide-react';

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
    // Account link is rendered specially below based on authentication state
  ];
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userRole, setUserRole] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    const checkAuth = async () => {
      try {
        const profile = await fetchUserProfile();
        if (mounted) {
          setIsAuthenticated(true);
          setUserRole((profile as any).role || (profile as any).Role || null);
        }
      } catch (err) {
        if (mounted) {
          setIsAuthenticated(false);
          setUserRole(null);
        }
      }
    };
    checkAuth();
    const onAuthChange = (ev: Event) => {
      try {
        // @ts-ignore
        const d = (ev as CustomEvent).detail;
        setIsAuthenticated(Boolean(d?.authenticated));
      } catch {
        // ignore
      }
    };
    window.addEventListener('auth-change', onAuthChange as EventListener);
    return () => {
      mounted = false;
      window.removeEventListener('auth-change', onAuthChange as EventListener);
    };
  }, []);
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
            {/* Account link: show text 'Đăng nhập' when unauthenticated, icon when authenticated */}
            {isAuthenticated ? (
              <Link
                to="/profile"
                className={`flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium ${location.pathname === '/profile' ? 'text-emerald-600 bg-emerald-50' : 'text-gray-600 hover:text-emerald-600 hover:bg-emerald-50'}`}
              >
                <UserIcon className="w-5 h-5" />
                <span>Tài khoản</span>
              </Link>
            ) : (
              <Link
                to="/auth"
                className={`flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium ${location.pathname === '/auth' ? 'text-emerald-600 bg-emerald-50' : 'text-gray-600 hover:text-emerald-600 hover:bg-emerald-50'}`}
              >
                <span className="font-medium">Đăng nhập</span>
              </Link>
            )}
            {isAuthenticated && (userRole || '').toLowerCase() === 'admin' && (
              <Link
                to="/admin"
                className={`flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium ${
                  location.pathname.startsWith('/admin')
                    ? 'text-emerald-600 bg-emerald-50'
                    : 'text-gray-600 hover:text-emerald-600 hover:bg-emerald-50'
                }`}
              > <ShieldCheckIcon className="w-5 h-5" />
                <span>Quản lý hệ thống</span>
              </Link>
            )}
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
            {isAuthenticated ? (
              <Link
                to="/profile"
                className={`flex items-center space-x-3 px-4 py-3 text-base font-medium ${location.pathname === '/profile' ? 'text-emerald-600 bg-emerald-50' : 'text-gray-600 hover:text-emerald-600 hover:bg-emerald-50'}`}
                onClick={() => setIsMenuOpen(false)}
              >
                <UserIcon className="w-5 h-5" />
                <span>Tài khoản</span>
              </Link>
            ) : (
              <Link
                to="/auth"
                className={`flex items-center space-x-3 px-4 py-3 text-base font-medium ${location.pathname === '/auth' ? 'text-emerald-600 bg-emerald-50' : 'text-gray-600 hover:text-emerald-600 hover:bg-emerald-50'}`}
                onClick={() => setIsMenuOpen(false)}
              >
                <span className="font-medium">Đăng nhập</span>
              </Link>
            )}
            {isAuthenticated && (userRole || '').toLowerCase() === 'admin' && (
              <Link
                to="/admin"
                className={`flex items-center space-x-3 px-4 py-3 text-base font-medium ${
                  location.pathname.startsWith('/admin')
                    ? 'text-emerald-600 bg-emerald-50'
                    : 'text-gray-600 hover:text-emerald-600 hover:bg-emerald-50'
                }`}
                
                onClick={() => setIsMenuOpen(false)}
                
              >
                <span>Quản lý hệ thống</span>
              </Link>
            )}
          </div>
        )}
      </div>
    </header>
  );
};
export default Navbar;


