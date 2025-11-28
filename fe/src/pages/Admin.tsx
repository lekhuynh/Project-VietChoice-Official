import React, { useEffect, useMemo, useState } from 'react';
import {
  LayoutDashboard,
  Package,
  Users,
  BarChart2,
  Settings,
  Search,
  Plus,
  Pencil,
  Trash2,
  RefreshCw,
  Play,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
} from 'lucide-react';
import {
  getDashboardStats,
  getAdminProducts,
  createProduct,
  updateProduct,
  deleteProduct,
  getAdminUsers,
  createUser,
  updateUser,
  deleteUser,
  updateSentiment,
  getSentimentChartData,
  getTrendData,
  getFeaturedProducts,
  getAutoUpdateStatus,
  enableAutoUpdateAdmin,
  disableAutoUpdateAdmin,
  type DashboardStats,
  type AdminProduct,
  type AdminUser,
  type ProductCreate,
  type ProductUpdate,
  type UserCreate,
  type UserUpdate,
  type SentimentChartData,
  type TrendData,
  type FeaturedProduct,
} from '../api/admin';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';

type TabKey = 'dashboard' | 'products' | 'users' | 'analytics' | 'settings';

const pill = (label: string, tone: 'green' | 'gray' = 'green') =>
  `px-2.5 py-1 rounded-full text-xs font-medium ${
    tone === 'green' ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-100' : 'bg-slate-100 text-slate-700 ring-1 ring-slate-200'
  }`;

const currency = (v?: number) => (typeof v === 'number' ? `${v.toLocaleString('vi-VN')} đ` : '—');

const Admin: React.FC = () => {
  const [tab, setTab] = useState<TabKey>('dashboard');
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [products, setProducts] = useState<AdminProduct[]>([]);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [chartData, setChartData] = useState<SentimentChartData[]>([]);
  const [trendData, setTrendData] = useState<TrendData[]>([]);
  const [featured, setFeatured] = useState<FeaturedProduct[]>([]);
  const [autoStatus, setAutoStatus] = useState<{ enabled: boolean } | null>(null);
  const [search, setSearch] = useState('');

  const [productModalOpen, setProductModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<AdminProduct | null>(null);

  const [userModalOpen, setUserModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        if (tab === 'dashboard') {
          const [s, sc, td, fp] = await Promise.all([
            getDashboardStats().catch(() => null),
            getSentimentChartData().catch(() => []),
            getTrendData().catch(() => []),
            getFeaturedProducts().catch(() => []),
          ]);
          setStats(s);
          setChartData(sc);
          setTrendData(td);
          setFeatured(fp);
        }
        if (tab === 'products') {
          const list = await getAdminProducts(search || undefined);
          setProducts(list);
        }
        if (tab === 'users') {
          const list = await getAdminUsers();
          setUsers(list);
        }
        if (tab === 'settings') {
          const st = await getAutoUpdateStatus().catch(() => null);
          setAutoStatus(st);
        }
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [tab, search]);

  const sentimentColors = useMemo(
    () => ({ positive: '#10b981', neutral: '#3b82f6', negative: '#ef4444' }),
    []
  );

  const openEditProduct = (p: AdminProduct) => {
    setEditingProduct(p);
    setProductModalOpen(true);
  };

  const saveProduct = async (data: { name: string; brand?: string; categoryId: number; price?: number; description?: string; active?: boolean }) => {
    const payload: ProductCreate = {
      Product_Name: data.name,
      Brand: data.brand,
      Category_ID: data.categoryId,
      Price: data.price,
      Description: data.description,
      Is_Active: data.active,
    };
    if (editingProduct) {
      const updatePayload: ProductUpdate = { ...payload, Product_ID: editingProduct.Product_ID };
      await updateProduct(updatePayload);
    } else {
      await createProduct(payload);
    }
    setProductModalOpen(false);
    setEditingProduct(null);
    const refreshed = await getAdminProducts(search || undefined);
    setProducts(refreshed);
  };

  const removeProduct = async (id: number) => {
    if (!window.confirm('Xóa sản phẩm này?')) return;
    await deleteProduct(id);
    setProducts((prev) => prev.filter((p) => p.Product_ID !== id));
  };

  const openEditUser = (u: AdminUser) => {
    setEditingUser(u);
    setUserModalOpen(true);
  };

  const saveUser = async (data: { name: string; email: string; role?: string; password?: string }) => {
    if (editingUser) {
      const payload: UserUpdate = { User_ID: editingUser.User_ID, User_Name: data.name, User_Email: data.email, Role: data.role };
      await updateUser(payload);
    }
    setUserModalOpen(false);
    setEditingUser(null);
    const refreshed = await getAdminUsers();
    setUsers(refreshed);
  };

  const removeUser = async (id: number) => {
    if (!window.confirm('Xóa người dùng này?')) return;
    await deleteUser(id);
    setUsers((prev) => prev.filter((u) => u.User_ID !== id));
  };

  const runAutoUpdate = async () => {
    setLoading(true);
    try {
      await updateSentiment();
      const st = await getAutoUpdateStatus().catch(() => null);
      setAutoStatus(st);
    } finally {
      setLoading(false);
    }
  };

  const toggleAutoUpdate = async (enable: boolean) => {
    setLoading(true);
    try {
      if (enable) await enableAutoUpdateAdmin();
      else await disableAutoUpdateAdmin();
      const st = await getAutoUpdateStatus().catch(() => null);
      setAutoStatus(st);
    } finally {
      setLoading(false);
    }
  };

  const NavButton = ({ k, label, icon: Icon }: { k: TabKey; label: string; icon: any }) => (
    <button
      onClick={() => setTab(k)}
      className={`flex items-center gap-2 px-3 py-2 rounded-lg transition ${
        tab === k ? 'bg-emerald-50 text-emerald-700' : 'text-slate-600 hover:bg-slate-100'
      }`}
    >
      <Icon size={16} />
      <span className="text-sm font-semibold">{label}</span>
    </button>
  );

  const Card = ({ title, value, sub }: { title: string; value: React.ReactNode; sub?: React.ReactNode }) => (
    <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{title}</p>
      <div className="text-2xl font-semibold text-slate-900 mt-1">{value}</div>
      {sub && <div className="text-sm text-slate-500 mt-1">{sub}</div>}
    </div>
  );

  const ProductsTable = () => (
      <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
      <div className="flex flex-wrap gap-2 items-center p-4">
        <div className="flex items-center bg-slate-50 rounded-lg px-3 py-2 w-full md:w-72">
          <Search size={16} className="text-slate-500" />
          <input
            className="flex-1 bg-transparent outline-none px-2 text-sm"
            placeholder="Tìm sản phẩm..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="text-left px-4 py-3">Tên</th>
              <th className="text-left px-4 py-3">Brand</th>
              <th className="text-left px-4 py-3">Giá</th>
              <th className="text-left px-4 py-3">Trạng thái</th>
              <th className="text-left px-4 py-3">Cập nhật</th>
              <th className="text-right px-4 py-3">Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.Product_ID} className="border-t border-slate-100 hover:bg-slate-50/50">
                <td className="px-4 py-3 font-medium text-slate-900">{p.Product_Name}</td>
                <td className="px-4 py-3 text-slate-600">{p.Brand || '—'}</td>
                <td className="px-4 py-3 text-slate-600">{currency(p.Price)}</td>
                <td className="px-4 py-3">
                  <span className={pill(p.Is_Active ? 'Đang bán' : 'Ẩn', p.Is_Active ? 'green' : 'gray')}>
                    {p.Is_Active ? 'Đang bán' : 'Ẩn'}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-500 text-xs">{p.Updated_At || p.Created_At || '—'}</td>
                <td className="px-4 py-3 text-right">
                  <div className="flex justify-end gap-2">
                    <button onClick={() => openEditProduct(p)} className="p-2 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700">
                      <Pencil size={16} />
                    </button>
                    <button onClick={() => removeProduct(p.Product_ID)} className="p-2 rounded-full bg-rose-50 hover:bg-rose-100 text-rose-600">
                      <Trash2 size={16} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {products.length === 0 && <div className="p-6 text-center text-slate-500 text-sm">Chưa có sản phẩm</div>}
      </div>
    </div>
  );

  const UsersTable = () => (
    <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
      <div className="flex items-center p-4 text-sm font-semibold text-slate-700">Danh sách người dùng</div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="text-left px-4 py-3">Tên</th>
              <th className="text-left px-4 py-3">Email</th>
              <th className="text-left px-4 py-3">Role</th>
              <th className="text-left px-4 py-3">Tạo lúc</th>
              <th className="text-right px-4 py-3">Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.User_ID} className="border-t border-slate-100 hover:bg-slate-50/50">
                <td className="px-4 py-3 font-medium text-slate-900">{u.User_Name}</td>
                <td className="px-4 py-3 text-slate-600">{u.User_Email}</td>
                <td className="px-4 py-3">
                  <span className={pill(u.Role || 'user', 'gray')}>{u.Role || 'user'}</span>
                </td>
                <td className="px-4 py-3 text-slate-500 text-xs">{u.Created_At || '—'}</td>
                <td className="px-4 py-3 text-right">
                  <div className="flex justify-end gap-2">
                    <button onClick={() => openEditUser(u)} className="p-2 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700">
                      <Pencil size={16} />
                    </button>
                    <button onClick={() => removeUser(u.User_ID)} className="p-2 rounded-full bg-rose-50 hover:bg-rose-100 text-rose-600">
                      <Trash2 size={16} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {users.length === 0 && <div className="p-6 text-center text-slate-500 text-sm">Chưa có người dùng</div>}
      </div>
    </div>
  );

  const Analytics = () => (
    <div className="grid gap-6">
      <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-slate-900 flex items-center gap-2">
            <BarChart2 size={18} /> Sentiment theo nhóm
          </h3>
        </div>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="positive" fill={sentimentColors.positive} name="Tích cực" />
              <Bar dataKey="neutral" fill={sentimentColors.neutral} name="Trung lập" />
              <Bar dataKey="negative" fill={sentimentColors.negative} name="Tiêu cực" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-slate-900 flex items-center gap-2">
            <TrendingUp size={18} /> Xu hướng
          </h3>
        </div>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              {trendData.length > 0 &&
                Object.keys(trendData[0] || {})
                  .filter((k) => k !== 'month')
                  .map((k, idx) => (
                    <Line key={k} type="monotone" dataKey={k} stroke={['#10b981', '#3b82f6', '#f59e0b', '#ef4444'][idx % 4]} name={k} />
                  ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4">
        <h3 className="font-semibold text-slate-900 mb-3">Sản phẩm nổi bật</h3>
        <div className="grid md:grid-cols-3 gap-3">
          {featured.map((f) => (
            <div key={f.Product_ID} className="p-3 rounded-lg border border-slate-100 shadow-sm">
              <div className="font-semibold text-slate-900 line-clamp-2">{f.Product_Name}</div>
              <div className="text-sm text-slate-500">{f.Brand || '—'}</div>
              <div className="mt-2 flex items-center gap-2 text-xs text-slate-600">
                <CheckCircle2 size={14} className="text-emerald-500" />
                {(typeof f.Positive_Percent === 'number' ? f.Positive_Percent : 0).toFixed(0)}% tích cực
              </div>
            </div>
          ))}
          {featured.length === 0 && <div className="text-sm text-slate-500">Không có dữ liệu</div>}
        </div>
      </div>
    </div>
  );

  const AutoUpdate = () => (
    <div className="flex justify-center">
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5 w-full max-w-xl space-y-3">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-emerald-50 text-emerald-700">
            <ShieldCheck size={18} />
          </div>
          <div>
            <div className="font-semibold text-slate-900">Auto-update dữ liệu</div>
            <p className="text-sm text-slate-500">Bật/tắt và chạy cập nhật thủ công.</p>
            <div className="text-xs text-slate-500 mt-1">
              Trạng thái: {autoStatus ? (autoStatus.enabled ? 'Đang bật' : 'Đang tắt') : '—'}
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => toggleAutoUpdate(true)}
            className="px-3 py-2 rounded-lg border border-emerald-200 text-emerald-700 bg-emerald-50 text-sm"
            disabled={loading}
          >
            Bật
          </button>
          <button
            onClick={() => toggleAutoUpdate(false)}
            className="px-3 py-2 rounded-lg border border-slate-200 text-slate-700 bg-white text-sm"
            disabled={loading}
          >
            Tắt
          </button>
          <button
            onClick={runAutoUpdate}
            className="px-3 py-2 rounded-lg bg-emerald-600 text-white text-sm inline-flex items-center gap-2"
            disabled={loading}
          >
            <Play size={16} /> Chạy ngay
          </button>
        </div>
      </div>
    </div>
  );

  const ProductModal = () => {
    const [name, setName] = useState(editingProduct?.Product_Name || '');
    const [brand, setBrand] = useState(editingProduct?.Brand || '');
    const [categoryId, setCategoryId] = useState(editingProduct?.Category_ID || 0);
    const [price, setPrice] = useState<number | undefined>(editingProduct?.Price);
    const [description, setDescription] = useState(editingProduct?.Description || '');
    const [active, setActive] = useState<boolean>(editingProduct?.Is_Active ?? true);

    const onSave = async () => {
      await saveProduct({ name, brand: brand || undefined, categoryId: Number(categoryId) || 0, price, description, active });
    };

    return (
      <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50">
        <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-slate-900">{editingProduct ? 'Sửa sản phẩm' : 'Thêm sản phẩm'}</h3>
            <button onClick={() => setProductModalOpen(false)} className="text-slate-500 hover:text-slate-700">
              ×
            </button>
          </div>
          <div className="grid gap-3">
            <label className="text-sm text-slate-700">
              Tên sản phẩm
              <input
                className="mt-1 w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </label>
            <label className="text-sm text-slate-700">
              Brand
              <input
                className="mt-1 w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
                value={brand}
                onChange={(e) => setBrand(e.target.value)}
              />
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className="text-sm text-slate-700">
                Category ID
                <input
                  type="number"
                  className="mt-1 w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
                  value={categoryId}
                  onChange={(e) => setCategoryId(Number(e.target.value))}
                />
              </label>
              <label className="text-sm text-slate-700">
                Giá
                <input
                  type="number"
                  className="mt-1 w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
                  value={price ?? ''}
                  onChange={(e) => setPrice(e.target.value ? Number(e.target.value) : undefined)}
                />
              </label>
            </div>
            <label className="text-sm text-slate-700">
              Mô tả
              <textarea
                className="mt-1 w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </label>
            <label className="inline-flex items-center gap-2 text-sm text-slate-700">
              <input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} />
              Đang bán
            </label>
          </div>
          <div className="flex justify-end gap-2">
            <button onClick={() => setProductModalOpen(false)} className="px-4 py-2 rounded-lg border border-slate-200 text-slate-700 text-sm">
              Hủy
            </button>
            <button onClick={onSave} className="px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm">
              Lưu
            </button>
          </div>
        </div>
      </div>
    );
  };

  const UserModal = () => {
    const [name, setName] = useState(editingUser?.User_Name || '');
    const [email, setEmail] = useState(editingUser?.User_Email || '');
    const [role, setRole] = useState(editingUser?.Role || 'user');
    const [password, setPassword] = useState('');

    const onSave = async () => {
      await saveUser({ name, email, role, password });
    };

    return (
      <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50">
        <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-slate-900">{editingUser ? 'Sửa người dùng' : 'Thêm người dùng'}</h3>
            <button onClick={() => setUserModalOpen(false)} className="text-slate-500 hover:text-slate-700">
              ×
            </button>
          </div>
          <div className="grid gap-3">
            <label className="text-sm text-slate-700">
              Tên
              <input className="mt-1 w-full border border-slate-200 rounded-lg px-3 py-2 text-sm" value={name} onChange={(e) => setName(e.target.value)} />
            </label>
            <label className="text-sm text-slate-700">
              Email
              <input className="mt-1 w-full border border-slate-200 rounded-lg px-3 py-2 text-sm" value={email} onChange={(e) => setEmail(e.target.value)} />
            </label>
            <label className="text-sm text-slate-700">
              Role
              <select className="mt-1 w-full border border-slate-200 rounded-lg px-3 py-2 text-sm" value={role} onChange={(e) => setRole(e.target.value)}>
                <option value="admin">admin</option>
                <option value="user">user</option>
              </select>
            </label>
            {!editingUser && (
              <label className="text-sm text-slate-700">
                Mật khẩu
                <input
                  type="password"
                  className="mt-1 w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </label>
            )}
          </div>
          <div className="flex justify-end gap-2">
            <button onClick={() => setUserModalOpen(false)} className="px-4 py-2 rounded-lg border border-slate-200 text-slate-700 text-sm">
              Hủy
            </button>
            <button onClick={onSave} className="px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm">
              Lưu
            </button>
          </div>
        </div>
      </div>
    );
  };

  const Dashboard = () => (
    <div className="grid gap-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card title="Tổng sản phẩm" value={stats?.totalProducts ?? '—'} />
        <Card title="Người dùng" value={stats?.totalUsers ?? '—'} />
        <Card title="Thương hiệu" value={stats?.totalBrands ?? '—'} />
        <Card title="Tích cực" value={`${stats?.positiveRatio ?? 0}%`} />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card title="Sản phẩm hôm nay" value={stats?.todayProducts ?? '—'} sub="Thêm mới trong ngày" />
        <Card title="Active users" value={stats?.activeUsers ?? '—'} />
        <Card title="Pending review" value={stats?.pendingReviews ?? '—'} />
      </div>
      <Analytics />
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-3">
          <div className="flex items-center gap-2 text-slate-900 font-semibold">
            <LayoutDashboard size={18} />
            Admin Center
          </div>
          <div className="flex-1" />
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6 flex gap-6">
        <nav className="hidden md:flex flex-col gap-2 w-60 bg-white border border-slate-100 rounded-2xl p-3 sticky top-20 self-start shadow-sm">
          <NavButton k="dashboard" label="Dashboard" icon={LayoutDashboard} />
          <NavButton k="products" label="Sản phẩm" icon={Package} />
          <NavButton k="users" label="Người dùng" icon={Users} />
          <NavButton k="analytics" label="Analytics" icon={BarChart2} />
          <NavButton k="settings" label="Cấu hình" icon={Settings} />
        </nav>

        <main className="flex-1 space-y-6 min-w-0">
          {loading && <div className="text-sm text-slate-500">Đang tải...</div>}
          {!loading && tab === 'dashboard' && <Dashboard />}
          {!loading && tab === 'products' && <ProductsTable />}
          {!loading && tab === 'users' && <UsersTable />}
          {!loading && tab === 'analytics' && <Analytics />}
          {!loading && tab === 'settings' && <AutoUpdate />}
        </main>
      </div>

      {productModalOpen && <ProductModal />}
      {userModalOpen && <UserModal />}
    </div>
  );
};

export default Admin;
