import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Search as SearchIcon,
  ScanIcon,
  ShoppingBagIcon,
  UserIcon,
  ShieldCheck,
  Menu,
  X,
} from 'lucide-react';
import { fetchUserProfile } from '../../api/user';

const navItems = [
  { name: 'Trang chủ', href: '/', icon: SearchIcon },
  { name: 'Quét mã', href: '/scanner', icon: ScanIcon },
  { name: 'Sản phẩm', href: '/products', icon: ShoppingBagIcon },
];

const Navbar = () => {
  const location = useLocation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
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
      } catch {
        if (mounted) {
          setIsAuthenticated(false);
          setUserRole(null);
        }
      }
    };
    void checkAuth();
    return () => {
      mounted = false;
    };
  }, []);

  const pillClass = (active: boolean) =>
    `flex items-center gap-2 px-3 py-2 rounded-full text-sm font-semibold transition ${
      active
        ? 'text-emerald-700 bg-emerald-50 shadow-sm'
        : 'text-slate-600 hover:text-emerald-700 hover:bg-emerald-50'
    }`;

  return (
    <header className="fixed top-0 left-0 right-0 z-50 w-full bg-white/90 backdrop-blur-xl border-b border-slate-100 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 md:px-6">
        <div className="flex items-center justify-between py-3">
          <Link to="/" className="flex items-center gap-2">
            <div className="h-9 w-9 rounded-full bg-emerald-600 text-white flex items-center justify-center font-bold text-base shadow-lg">
              VC
            </div>
            <div className="leading-tight">
              <p className="text-sm font-semibold text-slate-900">VietChoice</p>
              <p className="text-xs text-slate-500">Chọn thông minh. Sống xanh.</p>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = location.pathname === item.href;
              return (
                <Link key={item.href} to={item.href} className={pillClass(active)}>
                  <Icon size={16} />
                  {item.name}
                </Link>
              );
            })}

            {isAuthenticated ? (
              <Link to="/profile" className={pillClass(location.pathname === '/profile')}>
                <UserIcon size={16} />
                Tài khoản
              </Link>
            ) : (
              <Link
                to="/auth"
                className="px-4 py-2 rounded-full bg-emerald-600 text-white text-sm font-semibold shadow hover:bg-emerald-700 transition"
              >
                Đăng nhập
              </Link>
            )}

            {isAuthenticated && (userRole || '').toLowerCase() === 'admin' && (
              <Link
                to="/admin"
                className={pillClass(location.pathname.startsWith('/admin'))}
                title="Quản lý hệ thống"
              >
                <ShieldCheck size={16} />
                Quản lý hệ thống
              </Link>
            )}
          </nav>

          <button
            type="button"
            className="md:hidden text-slate-600 hover:text-emerald-700"
            onClick={() => setIsMenuOpen((v) => !v)}
          >
            {isMenuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>

        {/* Mobile dropdown */}
        {isMenuOpen && (
          <div className="md:hidden pb-3 space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = location.pathname === item.href;
              return (
                <Link
                  key={item.href}
                  to={item.href}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
                    active ? 'bg-emerald-50 text-emerald-700' : 'text-slate-700 hover:bg-slate-50'
                  }`}
                  onClick={() => setIsMenuOpen(false)}
                >
                  <Icon size={18} />
                  {item.name}
                </Link>
              );
            })}
            {isAuthenticated ? (
              <Link
                to="/profile"
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-slate-700 hover:bg-slate-50"
                onClick={() => setIsMenuOpen(false)}
              >
                <UserIcon size={18} />
                Tài khoản
              </Link>
            ) : (
              <Link
                to="/auth"
                className="block text-center px-3 py-2 rounded-lg bg-emerald-600 text-white font-semibold"
                onClick={() => setIsMenuOpen(false)}
              >
                Đăng nhập
              </Link>
            )}
            {isAuthenticated && (userRole || '').toLowerCase() === 'admin' && (
              <Link
                to="/admin"
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-slate-700 hover:bg-slate-50"
                onClick={() => setIsMenuOpen(false)}
              >
                <ShieldCheck size={18} />
                Quản lý hệ thống
              </Link>
            )}
          </div>
        )}
      </div>
    </header>
  );
};

export default Navbar;

