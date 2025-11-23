import React, { useState, useEffect } from 'react';
import { BarChart3Icon, UsersIcon, ShoppingBagIcon, RefreshCwIcon, FilterIcon, PlusIcon, TrashIcon, EditIcon, TrendingUpIcon, AlertCircleIcon, StarIcon, ActivityIcon, XIcon, SaveIcon, SearchIcon } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
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
  getActivityLogs,
  updateSentiment,
  getSentimentChartData,
  getTrendData,
  getFeaturedProducts,
  type DashboardStats,
  type AdminProduct,
  type AdminUser,
  type ActivityLog,
  type ProductCreate,
  type ProductUpdate,
  type UserCreate,
  type UserUpdate,
} from '../api/admin';

const COLORS = ['#10b981', '#3b82f6', '#ef4444'];

const Admin = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showProductModal, setShowProductModal] = useState(false);
  const [showUserModal, setShowUserModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState<AdminProduct | null>(null);
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null);
  const [products, setProducts] = useState<AdminProduct[]>([]);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [chartData, setChartData] = useState<any[]>([]);
  const [trendData, setTrendData] = useState<any[]>([]);
  const [featuredProducts, setFeaturedProducts] = useState<any[]>([]);
  const [activityLogs, setActivityLogs] = useState<ActivityLog[]>([]);
  const [loadingData, setLoadingData] = useState(false);
  const [productsNeedingAttention, setProductsNeedingAttention] = useState<any[]>([]);

  // Load data khi tab thay đổi
  useEffect(() => {
    if (activeTab === 'dashboard') {
      loadDashboardData();
    } else if (activeTab === 'products') {
      loadProducts();
    } else if (activeTab === 'users') {
      loadUsers();
    } else if (activeTab === 'logs') {
      loadLogs();
    }
  }, [activeTab]);

  const loadDashboardData = async () => {
    setLoadingData(true);
    try {
      console.log('Loading dashboard data...');
      const [statsData, chart, trends, featured] = await Promise.all([
        getDashboardStats(),
        getSentimentChartData(),
        getTrendData(),
        getFeaturedProducts(),
      ]);
      
      console.log('Dashboard data loaded:', { statsData, chart, trends, featured });
      
      setStats(statsData);
      setChartData(chart || []);
      setTrendData(trends || []);
      setFeaturedProducts(featured || []);
      
      // Load products needing attention
      await loadProductsNeedingAttention();
      
    } catch (error: any) {
      console.error('Error loading dashboard data:', error);
      
      // Set default values on error
      setStats({
        totalProducts: 0,
        totalUsers: 0,
        totalBrands: 0,
        positiveRatio: 0,
        todayProducts: 0,
        activeUsers: 0,
        pendingReviews: 0,
      });
      setChartData([]);
      setTrendData([]);
      setFeaturedProducts([]);
      setProductsNeedingAttention([]);
      
      const errorMessage = error?.message || 'Unknown error';
      if (errorMessage.includes('401') || errorMessage.includes('Unauthenticated')) {
        alert('Bạn cần đăng nhập để xem dashboard. Vui lòng đăng nhập lại.');
      } else if (errorMessage.includes('403') || errorMessage.includes('Forbidden')) {
        alert('Bạn không có quyền truy cập trang admin. Vui lòng đăng nhập với tài khoản admin.');
      } else {
        alert('Lỗi khi tải dữ liệu dashboard: ' + errorMessage);
      }
    } finally {
      setLoadingData(false);
    }
  };

  const loadProductsNeedingAttention = async () => {
  try {
    console.log('Loading products needing attention...');
    
    // Thử load từ API endpoint chuyên dụng
    try {
      // Tạo API function tạm thời
      const response = await fetch('/admin/products-needing-attention', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('Products needing attention from API:', data);
        setProductsNeedingAttention(data);
        return;
      }
      console.log('Products needing attention API not available, using fallback');
    } catch (apiError) {
      console.log('API call failed, using fallback:', apiError);
    }
    
    // Fallback: Load all products và filter locally
    const allProducts = await getAdminProducts();
    console.log('All products for filtering:', allProducts);
    
    // SỬA Ở ĐÂY: Chỉ lọc những sản phẩm < 4 sao
    const problematicProducts = allProducts.filter(p => 
      (p.Avg_Rating && p.Avg_Rating < 4.0)  // Chỉ lấy sản phẩm dưới 4 sao
    );
    
    console.log('Filtered problematic products (rating < 4):', problematicProducts);
    
    // Format data để hiển thị
    const formattedProducts = problematicProducts.map(p => {
      const issues = [];
      if (p.Avg_Rating && p.Avg_Rating < 4.0) {
        issues.push(`Rating thấp (${p.Avg_Rating}/5)`);
      }
      // Có thể thêm các điều kiện khác nếu muốn
      if (p.Positive_Percent && p.Positive_Percent < 70) {
        issues.push(`Tỷ lệ tích cực thấp (${p.Positive_Percent}%)`);
      }
      if (!p.Sentiment_Label) {
        issues.push('Chưa phân tích sentiment');
      }
      
      return {
        Product_ID: p.Product_ID,
        Product_Name: p.Product_Name,
        Brand: p.Brand,
        Avg_Rating: p.Avg_Rating,
        Positive_Percent: p.Positive_Percent,
        issues: issues.join(', ') || 'Rating dưới 4 sao'
      };
    });
    
    console.log('Formatted products needing attention:', formattedProducts);
    setProductsNeedingAttention(formattedProducts);
    
  } catch (error) {
    console.error('Error in loadProductsNeedingAttention:', error);
    setProductsNeedingAttention([]);
  }
};

  const loadProducts = async () => {
    setLoadingData(true);
    try {
      const data = await getAdminProducts(searchTerm || undefined);
      setProducts(data);
    } catch (error) {
      console.error('Error loading products:', error);
      alert('Lỗi khi tải danh sách sản phẩm');
    } finally {
      setLoadingData(false);
    }
  };

  const loadUsers = async () => {
    setLoadingData(true);
    try {
      const data = await getAdminUsers(searchTerm || undefined);
      setUsers(data);
    } catch (error) {
      console.error('Error loading users:', error);
      alert('Lỗi khi tải danh sách người dùng');
    } finally {
      setLoadingData(false);
    }
  };

  const loadLogs = async () => {
    setLoadingData(true);
    try {
      const data = await getActivityLogs();
      setActivityLogs(data);
    } catch (error) {
      console.error('Error loading logs:', error);
      alert('Lỗi khi tải nhật ký hoạt động');
    } finally {
      setLoadingData(false);
    }
  };

  // Hàm để lấy tất cả category keys từ trend data
  const getTrendCategories = () => {
    if (!trendData.length) return [];
    
    const allKeys = new Set<string>();
    trendData.forEach(item => {
      Object.keys(item).forEach(key => {
        if (key !== 'month') {
          allKeys.add(key);
        }
      });
    });
    
    return Array.from(allKeys);
  };

  // Mapping màu sắc cho các categories
  const getCategoryColor = (category: string) => {
    const colors = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4'];
    const index = getTrendCategories().indexOf(category) % colors.length;
    return colors[index];
  };

  // Format tên category để hiển thị đẹp
  const formatCategoryName = (categoryKey: string) => {
    return categoryKey
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
  };

  const filteredProducts = products.filter(product => 
    product.Product_Name?.toLowerCase().includes(searchTerm.toLowerCase()) || 
    product.Brand?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredUsers = users.filter(user => 
    user.User_Name?.toLowerCase().includes(searchTerm.toLowerCase()) || 
    user.User_Email?.toLowerCase().includes(searchTerm.toLowerCase()) || 
    user.Role?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleUpdateSentiment = async () => {
    setIsLoading(true);
    try {
      await updateSentiment();
      alert('Cập nhật phân tích cảm xúc thành công!');
      if (activeTab === 'dashboard') {
        loadDashboardData();
      }
    } catch (error: any) {
      alert(error.message || 'Lỗi khi cập nhật sentiment');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEditProduct = (product: AdminProduct) => {
    setEditingProduct(product);
    setShowProductModal(true);
  };

  const handleDeleteProduct = async (productId: number) => {
    if (window.confirm('Bạn có chắc chắn muốn xóa sản phẩm này?')) {
      try {
        await deleteProduct(productId);
        setProducts(products.filter(p => p.Product_ID !== productId));
        alert('Đã xóa sản phẩm thành công!');
      } catch (error: any) {
        alert(error.message || 'Lỗi khi xóa sản phẩm');
      }
    }
  };

  const handleSaveProduct = async () => {
    const form = document.querySelector('#product-form') as HTMLFormElement;
    if (!form) return;

    const formData = new FormData(form);
    const productData: any = {
      product_name: formData.get('product_name') as string,
      brand: formData.get('brand') as string || undefined,
      category_id: parseInt(formData.get('category_id') as string),
      price: formData.get('price') ? parseFloat(formData.get('price') as string) : undefined,
      description: formData.get('description') as string || undefined,
      is_active: (formData.get('is_active') as string) === 'true',
    };

    try {
      if (editingProduct) {
        await updateProduct({ ...productData, Product_ID: editingProduct.Product_ID } as ProductUpdate);
        alert('Đã cập nhật sản phẩm thành công!');
      } else {
        await createProduct(productData as ProductCreate);
        alert('Đã tạo sản phẩm thành công!');
      }
      setShowProductModal(false);
      setEditingProduct(null);
      loadProducts();
    } catch (error: any) {
      alert(error.message || 'Lỗi khi lưu sản phẩm');
    }
  };

  const handleEditUser = (user: AdminUser) => {
    setEditingUser(user);
    setShowUserModal(true);
  };

  const handleDeleteUser = async (userId: number) => {
    if (window.confirm('Bạn có chắc chắn muốn xóa người dùng này?')) {
      try {
        await deleteUser(userId);
        setUsers(users.filter(u => u.User_ID !== userId));
        alert('Đã xóa người dùng thành công!');
      } catch (error: any) {
        alert(error.message || 'Lỗi khi xóa người dùng');
      }
    }
  };

  const handleSaveUser = async () => {
    const form = document.querySelector('#user-form') as HTMLFormElement;
    if (!form) return;

    const formData = new FormData(form);
    
    try {
      if (editingUser) {
        const updateData: UserUpdate = {
          User_ID: editingUser.User_ID,
          User_Name: formData.get('name') as string || undefined,
          User_Email: formData.get('email') as string || undefined,
          Role: formData.get('role') as string || undefined,
        };
        await updateUser(updateData);
        alert('Đã cập nhật người dùng thành công!');
      } else {
        const createData: UserCreate = {
          User_Name: formData.get('name') as string,
          User_Email: formData.get('email') as string,
          User_Password: formData.get('password') as string,
          Role: formData.get('role') as string || 'user',
        };
        await createUser(createData);
        alert('Đã tạo người dùng thành công!');
      }
      setShowUserModal(false);
      setEditingUser(null);
      loadUsers();
    } catch (error: any) {
      alert(error.message || 'Lỗi khi lưu người dùng');
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Quản trị hệ thống</h1>
        <div className="flex items-center space-x-3">
          <button 
            onClick={handleUpdateSentiment} 
            disabled={isLoading}
            className="flex items-center px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50"
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
      </div>

      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="border-b border-gray-200">
          <div className="flex overflow-x-auto">
            <button 
              className={`flex items-center px-6 py-4 font-medium whitespace-nowrap transition-colors ${
                activeTab === 'dashboard' 
                  ? 'text-emerald-600 border-b-2 border-emerald-600 bg-emerald-50' 
                  : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
              }`} 
              onClick={() => setActiveTab('dashboard')}
            >
              <BarChart3Icon className="h-5 w-5 mr-2" />
              Dashboard
            </button>
            <button 
              className={`flex items-center px-6 py-4 font-medium whitespace-nowrap transition-colors ${
                activeTab === 'products' 
                  ? 'text-emerald-600 border-b-2 border-emerald-600 bg-emerald-50' 
                  : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
              }`} 
              onClick={() => setActiveTab('products')}
            >
              <ShoppingBagIcon className="h-5 w-5 mr-2" />
              Sản phẩm
            </button>
            <button 
              className={`flex items-center px-6 py-4 font-medium whitespace-nowrap transition-colors ${
                activeTab === 'users' 
                  ? 'text-emerald-600 border-b-2 border-emerald-600 bg-emerald-50' 
                  : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
              }`} 
              onClick={() => setActiveTab('users')}
            >
              <UsersIcon className="h-5 w-5 mr-2" />
              Người dùng
            </button>
            <button 
              className={`flex items-center px-6 py-4 font-medium whitespace-nowrap transition-colors ${
                activeTab === 'logs' 
                  ? 'text-emerald-600 border-b-2 border-emerald-600 bg-emerald-50' 
                  : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
              }`} 
              onClick={() => setActiveTab('logs')}
            >
              <ActivityIcon className="h-5 w-5 mr-2" />
              Nhật ký hoạt động
            </button>
          </div>
        </div>

        <div className="p-6">
          {activeTab === 'dashboard' && (
            <div className="space-y-6">
              {/* Statistics Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-xl p-6 border border-emerald-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-emerald-600">Tổng sản phẩm</p>
                      <p className="text-3xl font-bold text-emerald-900 mt-2">
                        {loadingData ? '...' : (stats?.totalProducts || 0)}
                      </p>
                      <p className="text-xs text-emerald-600 mt-1">
                        +{loadingData ? '...' : (stats?.todayProducts || 0)} hôm nay
                      </p>
                    </div>
                    <div className="p-3 rounded-full bg-emerald-600">
                      <ShoppingBagIcon className="h-8 w-8 text-white" />
                    </div>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-6 border border-blue-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-blue-600">Người dùng</p>
                      <p className="text-3xl font-bold text-blue-900 mt-2">
                        {loadingData ? '...' : (stats?.totalUsers || 0)}
                      </p>
                      <p className="text-xs text-blue-600 mt-1">
                        {loadingData ? '...' : (stats?.activeUsers || 0)} đang hoạt động
                      </p>
                    </div>
                    <div className="p-3 rounded-full bg-blue-600">
                      <UsersIcon className="h-8 w-8 text-white" />
                    </div>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-6 border border-purple-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-purple-600">Thương hiệu</p>
                      <p className="text-3xl font-bold text-purple-900 mt-2">
                        {loadingData ? '...' : (stats?.totalBrands || 0)}
                      </p>
                      <p className="text-xs text-purple-600 mt-1">Đã xác minh</p>
                    </div>
                    <div className="p-3 rounded-full bg-purple-600">
                      <StarIcon className="h-8 w-8 text-white" />
                    </div>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-xl p-6 border border-yellow-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-yellow-600">Tỷ lệ tích cực</p>
                      <p className="text-3xl font-bold text-yellow-900 mt-2">
                        {loadingData ? '...' : (stats?.positiveRatio ? stats.positiveRatio.toFixed(1) : '0.0')}%
                      </p>
                      <p className="text-xs text-yellow-600 mt-1">Trung bình toàn hệ thống</p>
                    </div>
                    <div className="p-3 rounded-full bg-yellow-600">
                      <TrendingUpIcon className="h-8 w-8 text-white" />
                    </div>
                  </div>
                </div>
              </div>

              {/* Featured Products */}
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                    <StarIcon className="h-5 w-5 text-yellow-500 mr-2" />
                    Sản phẩm nổi bật hôm nay
                  </h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {loadingData ? (
                    <div className="col-span-3 text-center py-8 text-gray-500">Đang tải...</div>
                  ) : featuredProducts.length === 0 ? (
                    <div className="col-span-3 text-center py-8 text-gray-500">Chưa có sản phẩm nổi bật</div>
                  ) : (
                    featuredProducts.map(product => (
                      <div key={product.Product_ID} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="font-medium text-gray-900 text-sm line-clamp-2">
                            {product.Product_Name}
                          </h4>
                          <TrendingUpIcon className="h-5 w-5 text-emerald-500 flex-shrink-0" />
                        </div>
                        <p className="text-xs text-gray-500 mb-3">
                          {product.Brand || 'N/A'}
                        </p>
                        <div className="flex items-center justify-between text-sm">
                          <div className="flex items-center">
                            <StarIcon className="h-4 w-4 text-yellow-400 fill-yellow-400" />
                            <span className="ml-1 font-medium">
                              {product.Avg_Rating?.toFixed(1) || 'N/A'}
                            </span>
                          </div>
                          <span className="text-emerald-600 font-medium">
                            {product.Positive_Percent?.toFixed(1) || 0}%
                          </span>
                        </div>
                        <div className="mt-2 pt-2 border-t border-gray-100">
                          <p className="text-xs text-gray-500">
                            {product.views || 0} lượt xem
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Products Needing Attention */}
              <div className="bg-white rounded-xl border border-red-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                    <AlertCircleIcon className="h-5 w-5 text-red-500 mr-2" />
                    Sản phẩm cần chú ý
                  </h3>
                </div>
                <div className="space-y-3">
                  {loadingData ? (
                    <div className="text-center py-8 text-gray-500">Đang tải...</div>
                  ) : productsNeedingAttention.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <p>Chưa có sản phẩm cần chú ý</p>
                      <p className="text-sm text-gray-400 mt-2">Tất cả sản phẩm đều có rating tốt</p>
                    </div>
                  ) : (
                    productsNeedingAttention.map(product => (
                      <div key={product.Product_ID} className="border border-red-200 rounded-lg p-4 bg-red-50">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <h4 className="font-medium text-gray-900 text-sm">
                              {product.Product_Name}
                            </h4>
                            <p className="text-xs text-gray-500 mt-1">
                              {product.Brand || 'N/A'}
                            </p>
                          </div>
                          <AlertCircleIcon className="h-5 w-5 text-red-500 flex-shrink-0 ml-2" />
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <div className="flex items-center">
                            <StarIcon className="h-4 w-4 text-yellow-400 fill-yellow-400" />
                            <span className="ml-1 font-medium">
                              {product.Avg_Rating?.toFixed(1) || 'N/A'}
                            </span>
                          </div>
                          <span className="text-red-600 font-medium">
                            {product.Positive_Percent?.toFixed(1) || 0}%
                          </span>
                        </div>
                        {product.issues && (
                          <div className="mt-2 pt-2 border-t border-red-200">
                            <p className="text-xs text-red-600">
                              {product.issues}
                            </p>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Sentiment Chart */}
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Tỷ lệ cảm xúc theo danh mục
                </h3>
                <div style={{ height: '400px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    {loadingData || chartData.length === 0 ? (
                      <div className="flex items-center justify-center h-full text-gray-500">
                        {loadingData ? 'Đang tải dữ liệu...' : 'Không có dữ liệu biểu đồ'}
                      </div>
                    ) : (
                      <BarChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="positive" name="Tích cực" stackId="a" fill="#10b981" />
                        <Bar dataKey="neutral" name="Trung lập" stackId="a" fill="#3b82f6" />
                        <Bar dataKey="negative" name="Tiêu cực" stackId="a" fill="#ef4444" />
                      </BarChart>
                    )}
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Trend Radar */}
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Trend Radar - Xu hướng sản phẩm 6 tháng
                </h3>
                <div style={{ height: '400px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    {loadingData || trendData.length === 0 ? (
                      <div className="flex items-center justify-center h-full text-gray-500">
                        {loadingData ? 'Đang tải dữ liệu...' : 'Không có dữ liệu xu hướng'}
                      </div>
                    ) : (
                      <LineChart data={trendData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis dataKey="month" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        {getTrendCategories().map((categoryKey, index) => (
                          <Line
                            key={categoryKey}
                            type="monotone"
                            dataKey={categoryKey}
                            name={formatCategoryName(categoryKey)}
                            stroke={getCategoryColor(categoryKey)}
                            strokeWidth={2}
                            dot={{ r: 4 }}
                          />
                        ))}
                      </LineChart>
                    )}
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}

          {/* Products Tab */}
          {activeTab === 'products' && (
            <div>
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
                <div className="relative w-full sm:w-64">
                  <input 
                    type="text" 
                    placeholder="Tìm kiếm sản phẩm..." 
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500" 
                    value={searchTerm} 
                    onChange={e => setSearchTerm(e.target.value)} 
                    onKeyDown={(e) => { if (e.key === 'Enter') loadProducts(); }} 
                  />
                  <button 
                    type="button" 
                    onClick={loadProducts} 
                    className="absolute right-2 top-2 px-2 py-1 text-sm text-emerald-600 hover:text-emerald-700"
                  >
                    Tìm
                  </button>
                  <SearchIcon className="h-5 w-5 absolute left-3 top-2.5 text-gray-400" />
                </div>
                <div className="flex items-center gap-2 w-full sm:w-auto">
                  <button className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
                    <FilterIcon className="h-4 w-4 mr-2" />
                    Lọc
                  </button>
                  <button 
                    onClick={() => {
                      setEditingProduct(null);
                      setShowProductModal(true);
                    }} 
                    className="flex items-center px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
                  >
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Thêm sản phẩm
                  </button>
                </div>
              </div>

              <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sản phẩm</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Giá</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Đánh giá</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sentiment</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Trạng thái</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Thao tác</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {loadingData ? (
                        <tr>
                          <td colSpan={7} className="px-6 py-4 text-center text-gray-500">Đang tải...</td>
                        </tr>
                      ) : filteredProducts.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="px-6 py-4 text-center text-gray-500">Không có sản phẩm nào</td>
                        </tr>
                      ) : (
                        filteredProducts.map(product => (
                          <tr key={product.Product_ID} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">#{product.Product_ID}</td>
                            <td className="px-6 py-4">
                              <div className="text-sm font-medium text-gray-900">{product.Product_Name}</div>
                              <div className="text-sm text-gray-500">{product.Brand || 'N/A'}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {product.Price ? `${product.Price.toLocaleString('vi-VN')}đ` : 'N/A'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <StarIcon className="h-4 w-4 text-yellow-400 fill-yellow-400" />
                                <span className="ml-1 text-sm text-gray-900">
                                  {product.Avg_Rating?.toFixed(1) || 'N/A'}
                                </span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="px-2 py-1 text-xs font-medium rounded-full bg-emerald-100 text-emerald-800">
                                {product.Positive_Percent?.toFixed(1) || 0}%
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                                {product.Is_Active ? 'Hoạt động' : 'Ngừng'}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                              <div className="flex space-x-2">
                                <button onClick={() => handleEditProduct(product)} className="text-blue-600 hover:text-blue-900">
                                  <EditIcon className="h-4 w-4" />
                                </button>
                                <button onClick={() => handleDeleteProduct(product.Product_ID)} className="text-red-600 hover:text-red-900">
                                  <TrashIcon className="h-4 w-4" />
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Users Tab - Giữ nguyên structure như products tab */}
          {activeTab === 'users' && (
            <div>
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
                <div className="relative w-full sm:w-64">
                  <input 
                    type="text" 
                    placeholder="Tìm kiếm người dùng..." 
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500" 
                    value={searchTerm} 
                    onChange={e => setSearchTerm(e.target.value)} 
                    onKeyDown={(e) => { if (e.key === 'Enter') loadUsers(); }} 
                  />
                  <button 
                    type="button" 
                    onClick={loadUsers} 
                    className="absolute right-2 top-2 px-2 py-1 text-sm text-emerald-600 hover:text-emerald-700"
                  >
                    Tìm
                  </button>
                  <SearchIcon className="h-5 w-5 absolute left-3 top-2.5 text-gray-400" />
                </div>
                <button 
                  onClick={() => {
                    setEditingUser(null);
                    setShowUserModal(true);
                  }} 
                  className="flex items-center px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
                >
                  <PlusIcon className="h-4 w-4 mr-2" />
                  Thêm người dùng
                </button>
              </div>

              <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Người dùng</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vai trò</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Trạng thái</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ngày tham gia</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Hoạt động gần nhất</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Thao tác</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {loadingData ? (
                        <tr>
                          <td colSpan={7} className="px-6 py-4 text-center text-gray-500">Đang tải...</td>
                        </tr>
                      ) : filteredUsers.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="px-6 py-4 text-center text-gray-500">Không có người dùng nào</td>
                        </tr>
                      ) : (
                        filteredUsers.map(user => (
                          <tr key={user.User_ID} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">#{user.User_ID}</td>
                            <td className="px-6 py-4">
                              <div className="text-sm font-medium text-gray-900">{user.User_Name}</div>
                              <div className="text-sm text-gray-500">{user.User_Email}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                user.Role === 'admin' ? 'bg-purple-100 text-purple-800' : 
                                user.Role === 'moderator' ? 'bg-blue-100 text-blue-800' : 
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {user.Role === 'admin' ? 'Quản trị viên' : 
                                 user.Role === 'moderator' ? 'Kiểm duyệt viên' : 
                                 'Người dùng'}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                                Hoạt động
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {user.Created_At ? new Date(user.Created_At).toLocaleDateString('vi-VN') : 'N/A'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {user.lastActive || 'N/A'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                              <div className="flex space-x-2">
                                <button onClick={() => handleEditUser(user)} className="text-blue-600 hover:text-blue-900">
                                  <EditIcon className="h-4 w-4" />
                                </button>
                                <button onClick={() => handleDeleteUser(user.User_ID)} className="text-red-600 hover:text-red-900">
                                  <TrashIcon className="h-4 w-4" />
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Logs Tab */}
          {activeTab === 'logs' && (
            <div>
              <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                <div className="p-4 bg-gray-50 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Nhật ký hoạt động hệ thống</h3>
                </div>
                <div className="divide-y divide-gray-200">
                  {loadingData ? (
                    <div className="p-4 text-center text-gray-500">Đang tải...</div>
                  ) : activityLogs.length === 0 ? (
                    <div className="p-4 text-center text-gray-500">Chưa có nhật ký hoạt động</div>
                  ) : (
                    activityLogs.map(log => (
                      <div key={log.id} className="p-4 hover:bg-gray-50">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                log.type === 'create' ? 'bg-green-100 text-green-800' : 
                                log.type === 'update' ? 'bg-blue-100 text-blue-800' : 
                                'bg-red-100 text-red-800'
                              }`}>
                                {log.type === 'create' ? 'Tạo mới' : 
                                 log.type === 'update' ? 'Cập nhật' : 
                                 'Xóa'}
                              </span>
                              <span className="font-medium text-gray-900">{log.user}</span>
                              <span className="text-gray-500">•</span>
                              <span className="text-gray-600">{log.action}</span>
                            </div>
                            <p className="text-sm text-gray-500 mt-1">{log.details}</p>
                          </div>
                          <span className="text-sm text-gray-500">{log.timestamp}</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Product Modal */}
      {showProductModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-xl font-semibold text-gray-900">
                {editingProduct ? 'Chỉnh sửa sản phẩm' : 'Thêm sản phẩm mới'}
              </h3>
              <button onClick={() => setShowProductModal(false)} className="text-gray-400 hover:text-gray-600">
                <XIcon className="h-6 w-6" />
              </button>
            </div>
            <form id="product-form" onSubmit={(e) => { e.preventDefault(); handleSaveProduct(); }}>
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tên sản phẩm</label>
                  <input 
                    type="text" 
                    name="product_name" 
                    required 
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500" 
                    defaultValue={editingProduct?.Product_Name} 
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Thương hiệu</label>
                    <input 
                      type="text" 
                      name="brand" 
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500" 
                      defaultValue={editingProduct?.Brand} 
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Danh mục ID</label>
                    <input 
                      type="number" 
                      name="category_id" 
                      required 
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500" 
                      defaultValue={editingProduct?.Category_ID} 
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Giá</label>
                    <input 
                      type="number" 
                      step="0.01" 
                      name="price" 
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500" 
                      defaultValue={editingProduct?.Price} 
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Trạng thái</label>
                    <select 
                      name="is_active" 
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500" 
                      defaultValue={editingProduct?.Is_Active ? 'true' : 'false'}
                    >
                      <option value="true">Hoạt động</option>
                      <option value="false">Ngừng hoạt động</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Mô tả</label>
                  <textarea 
                    rows={4} 
                    name="description" 
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500" 
                    defaultValue={editingProduct?.Description} 
                  />
                </div>
              </div>
            </form>
            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button onClick={() => setShowProductModal(false)} className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">
                Hủy
              </button>
              <button 
                type="button" 
                onClick={handleSaveProduct} 
                className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 flex items-center"
              >
                <SaveIcon className="h-4 w-4 mr-2" />
                Lưu
              </button>
            </div>
          </div>
        </div>
      )}

      {/* User Modal */}
      {showUserModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-xl font-semibold text-gray-900">
                {editingUser ? 'Chỉnh sửa người dùng' : 'Thêm người dùng mới'}
              </h3>
              <button onClick={() => setShowUserModal(false)} className="text-gray-400 hover:text-gray-600">
                <XIcon className="h-6 w-6" />
              </button>
            </div>
            <form id="user-form" onSubmit={(e) => { e.preventDefault(); handleSaveUser(); }}>
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Họ và tên</label>
                  <input 
                    type="text" 
                    name="name" 
                    required 
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500" 
                    defaultValue={editingUser?.User_Name} 
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input 
                    type="email" 
                    name="email" 
                    required 
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500" 
                    defaultValue={editingUser?.User_Email} 
                  />
                </div>
                {!editingUser && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Mật khẩu</label>
                    <input 
                      type="password" 
                      name="password" 
                      required 
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500" 
                    />
                  </div>
                )}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Vai trò</label>
                  <select 
                    name="role" 
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500" 
                    defaultValue={editingUser?.Role || 'user'}
                  >
                    <option value="user">Người dùng</option>
                    <option value="moderator">Kiểm duyệt viên</option>
                    <option value="admin">Quản trị viên</option>
                  </select>
                </div>
              </div>
            </form>
            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button onClick={() => setShowUserModal(false)} className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">
                Hủy
              </button>
              <button 
                type="button" 
                onClick={handleSaveUser} 
                className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 flex items-center"
              >
                <SaveIcon className="h-4 w-4 mr-2" />
                Lưu
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Admin;