import React, { useEffect, useState } from 'react';
import {
  BarChart3Icon, UsersIcon, ShoppingBagIcon, RefreshCwIcon,
  FilterIcon, PlusIcon, TrashIcon, EditIcon, TrendingUpIcon,
  StarIcon, ActivityIcon, XIcon, SaveIcon, SearchIcon
} from 'lucide-react';

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts';

import {
  fetchAdminProducts,
  fetchOutstandingProducts,
  fetchSentimentByCategory,
  AdminProduct,
  SentimentGroup
} from '../api/adminDashboard';

import {
  fetchAdminUsers,
  deleteAdminUser,
  AdminUser
} from '../api/adminUsers';


const Admin = () => {

  /** --------------------------------------
   *  STATE
   -------------------------------------- */
  const [activeTab, setActiveTab] = useState("dashboard");

  const [products, setProducts] = useState<AdminProduct[]>([]);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [featuredProducts, setFeaturedProducts] = useState<AdminProduct[]>([]);
  const [sentimentData, setSentimentData] = useState<SentimentGroup[]>([]);

  const [searchTerm, setSearchTerm] = useState("");

  const [stats, setStats] = useState({
    totalProducts: 0,
    totalUsers: 0,
    positiveRatio: 0,
  });

  const [loadingDashboard, setLoadingDashboard] = useState(false);
  const [loadingProducts, setLoadingProducts] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const [showProductModal, setShowProductModal] = useState(false);
  const [showUserModal, setShowUserModal] = useState(false);

  const [editingProduct, setEditingProduct] = useState<AdminProduct | null>(null);
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null);


  /** --------------------------------------
   * LOAD USERS
   -------------------------------------- */
  const loadUsers = async () => {
    try {
      const data = await fetchAdminUsers();
      setUsers(data);
      setStats((s) => ({ ...s, totalUsers: data.length }));
    } catch (err) {
      console.error("Load users error:", err);
    }
  };


  /** --------------------------------------
   * LOAD PRODUCTS
   -------------------------------------- */
  const loadProducts = async () => {
    setLoadingProducts(true);
    try {
      const res = await fetchAdminProducts({ limit: 50 });
      setProducts(res.results || []);
      setStats((s) => ({ ...s, totalProducts: res.total || 0 }));
    } catch (err) {
      console.error("Load products error:", err);
    }
    setLoadingProducts(false);
  };


  /** --------------------------------------
   * LOAD DASHBOARD
   -------------------------------------- */
  const loadDashboard = async () => {
    setLoadingDashboard(true);
    try {
      const [outstanding, sentiment] = await Promise.all([
        fetchOutstandingProducts({ limit: 6 }),
        fetchSentimentByCategory({ group_by: "category", min_count: 1 }),
      ]);

      setFeaturedProducts(outstanding.results || []);
      setSentimentData(sentiment.data || []);

      // Tính trung bình tỷ lệ tích cực
      const avg =
        (sentiment.data || []).reduce((a, c) => a + (c.positive_pct || 0), 0) /
        (sentiment.data?.length || 1);

      setStats((s) => ({ ...s, positiveRatio: Math.round(avg || 0) }));

    } catch (err) {
      console.error("Dashboard load error:", err);
    }
    setLoadingDashboard(false);
  };


  /** --------------------------------------
   * FIRST LOAD
   -------------------------------------- */
  useEffect(() => {
    loadUsers();
    loadProducts();
    loadDashboard();
  }, []);


  /** --------------------------------------
   * DELETE USER
   -------------------------------------- */
  const handleDeleteUser = async (User_ID: number) => {
    if (!window.confirm("Bạn có chắc chắn muốn xóa người dùng này?")) return;

    try {
      await deleteAdminUser(User_ID);
      setUsers((u) => u.filter((x) => x.User_ID !== User_ID));
      alert("Xóa thành công!");
    } catch (err) {
      console.error(err);
      alert("Xóa thất bại!");
    }
  };


  /** --------------------------------------
   * FILTERING
   -------------------------------------- */
  const filteredProducts = products.filter(p =>
    (p.Product_Name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
    (p.Brand || "").toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredUsers = users.filter(u =>
    (u.User_Name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
    (u.User_Email || "").toLowerCase().includes(searchTerm.toLowerCase())
  );


  /** --------------------------------------
   * UPDATE SENTIMENT (FAKE BUTTON)
   -------------------------------------- */
  const handleUpdateSentiment = () => {
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      loadDashboard();
      alert("Cập nhật phân tích cảm xúc thành công!");
    }, 1500);
  };


  /** --------------------------------------
   * UI
   -------------------------------------- */
  return (
    <div className="max-w-7xl mx-auto">

      {/* HEADER */}
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Quản trị hệ thống</h1>

        <button
          onClick={handleUpdateSentiment}
          disabled={isLoading}
          className="flex items-center px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
        >
          {isLoading ? (
            <>
              <RefreshCwIcon className="animate-spin h-4 w-4 mr-2" />
              Đang cập nhật...
            </>
          ) : (
            <>
              <RefreshCwIcon className="h-4 w-4 mr-2" />
              Cập nhật Sentiment
            </>
          )}
        </button>
      </div>


      {/* TABS */}
      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="border-b border-gray-200">
          <div className="flex overflow-x-auto">
            {[
              { key: "dashboard", icon: <BarChart3Icon className="h-5 w-5 mr-2" />, label: "Dashboard" },
              { key: "products", icon: <ShoppingBagIcon className="h-5 w-5 mr-2" />, label: "Sản phẩm" },
              { key: "users", icon: <UsersIcon className="h-5 w-5 mr-2" />, label: "Người dùng" },
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center px-6 py-4 font-medium whitespace-nowrap ${
                  activeTab === tab.key
                    ? "text-emerald-600 border-b-2 border-emerald-600 bg-emerald-50"
                    : "text-gray-600 hover:text-gray-800 hover:bg-gray-50"
                }`}
              >
                {tab.icon} {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="p-6">

          {/* ---------------- DASHBOARD TAB ---------------- */}
          {activeTab === "dashboard" && (
            <div className="space-y-6">

              {/* STATS */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Total products */}
                <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-6">
                  <p className="text-sm text-emerald-600">Tổng sản phẩm</p>
                  <p className="text-3xl font-bold mt-1">{stats.totalProducts}</p>
                </div>

                {/* Users */}
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
                  <p className="text-sm text-blue-600">Người dùng</p>
                  <p className="text-3xl font-bold mt-1">{stats.totalUsers}</p>
                </div>

                {/* Sentiment */}
                <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
                  <p className="text-sm text-yellow-600">Tỷ lệ tích cực</p>
                  <p className="text-3xl font-bold mt-1">{stats.positiveRatio}%</p>
                </div>
              </div>

              {/* OUTSTANDING PRODUCTS */}
              <div className="bg-white border rounded-xl p-6">
                <h3 className="font-semibold text-lg mb-4">Sản phẩm nổi bật</h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {featuredProducts.map(p => (
                    <div key={p.Product_ID} className="p-4 border rounded-lg">
                      <h4 className="font-medium text-gray-900">{p.Product_Name}</h4>
                      <p className="text-sm text-gray-600">{p.Brand}</p>
                      <p className="text-yellow-600 font-medium mt-2">
                        {p.Avg_Rating || 0} ★
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* SENTIMENT CHART */}
              <div className="bg-white border rounded-xl p-6">
                <h3 className="text-lg font-semibold mb-4">Tỷ lệ cảm xúc theo danh mục</h3>

                <div style={{ height: 400 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={sentimentData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="label" />
                      <YAxis />
                      <Tooltip />
                      <Legend />

                      <Bar dataKey="positive_pct" name="Tích cực" stackId="a" fill="#10b981" />
                      <Bar dataKey="neutral_pct" name="Trung lập" stackId="a" fill="#3b82f6" />
                      <Bar dataKey="negative_pct" name="Tiêu cực" stackId="a" fill="#ef4444" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

            </div>
          )}

          {/* ---------------- PRODUCTS TAB ---------------- */}
          {activeTab === "products" && (
            <div>

              {/* SEARCH */}
              <div className="flex mb-6">
                <input
                  type="text"
                  placeholder="Tìm kiếm sản phẩm..."
                  className="w-64 px-4 py-2 border rounded-lg"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>

              {/* TABLE */}
              <div className="bg-white border rounded-lg">
                <table className="min-w-full divide-y">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium">ID</th>
                      <th className="px-4 py-2 text-left text-xs font-medium">Tên</th>
                      <th className="px-4 py-2 text-left text-xs font-medium">Thương hiệu</th>
                      <th className="px-4 py-2 text-left text-xs font-medium">Rating</th>
                      <th className="px-4 py-2 text-left text-xs font-medium">Sentiment</th>
                      <th className="px-4 py-2 text-left text-xs font-medium">Trạng thái</th>
                    </tr>
                  </thead>

                  <tbody className="bg-white divide-y">
                    {filteredProducts.map((p) => (
                      <tr key={p.Product_ID} className="hover:bg-gray-50">
                        <td className="px-4 py-2 text-sm">{p.Product_ID}</td>
                        <td className="px-4 py-2 text-sm">{p.Product_Name}</td>
                        <td className="px-4 py-2 text-sm">{p.Brand}</td>
                        <td className="px-4 py-2 text-sm">{p.Avg_Rating || 0} ★</td>

                        <td className="px-4 py-2">
                          <span className="px-2 py-1 text-xs bg-emerald-100 text-emerald-800 rounded-lg">
                            {p.Positive_Percent ?? 0}%
                          </span>
                        </td>

                        <td className="px-4 py-2">
                          <span
                            className={`px-2 py-1 text-xs rounded-lg ${
                              p.Is_Active ? "bg-green-100 text-green-800" : "bg-gray-200 text-gray-700"
                            }`}
                          >
                            {p.Is_Active ? "Hoạt động" : "Ngừng"}
                          </span>
                        </td>

                      </tr>
                    ))}
                  </tbody>

                </table>
              </div>
            </div>
          )}

          {/* ---------------- USERS TAB ---------------- */}
          {activeTab === "users" && (
            <div>

              {/* SEARCH */}
              <div className="flex mb-6">
                <input
                  type="text"
                  placeholder="Tìm kiếm người dùng..."
                  className="w-64 px-4 py-2 border rounded-lg"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>

              {/* TABLE */}
              <div className="bg-white border rounded-lg">
                <table className="min-w-full divide-y">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium">ID</th>
                      <th className="px-4 py-2 text-left text-xs font-medium">Tên</th>
                      <th className="px-4 py-2 text-left text-xs font-medium">Email</th>
                      <th className="px-4 py-2 text-left text-xs font-medium">Role</th>
                      <th className="px-4 py-2 text-left text-xs font-medium">Ngày tạo</th>
                      <th className="px-4 py-2 text-left text-xs font-medium">Xóa</th>
                    </tr>
                  </thead>

                  <tbody className="bg-white divide-y">
                    {filteredUsers.map((u) => (
                      <tr key={u.User_ID} className="hover:bg-gray-50">

                        <td className="px-4 py-2 text-sm">{u.User_ID}</td>
                        <td className="px-4 py-2 text-sm">{u.User_Name}</td>
                        <td className="px-4 py-2 text-sm">{u.User_Email}</td>

                        <td className="px-4 py-2 text-sm">
                          <span className="px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded-lg">
                            {u.Role || "User"}
                          </span>
                        </td>

                        <td className="px-4 py-2 text-sm">
                          {u.Created_At?.slice(0, 10)}
                        </td>

                        <td className="px-4 py-2">
                          <button
                            onClick={() => handleDeleteUser(u.User_ID)}
                            className="text-red-600 hover:text-red-800"
                          >
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        </td>

                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

            </div>
          )}

        </div>
      </div>

    </div>
  );
};

export default Admin;
