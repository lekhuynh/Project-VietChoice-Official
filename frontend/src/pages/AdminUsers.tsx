import React, { useEffect, useState } from 'react';
import { RefreshCwIcon, TrashIcon } from 'lucide-react';
import { fetchAdminUsers, deleteAdminUser, AdminUser } from '../api/adminUsers';

const AdminUsers: React.FC = () => {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAdminUsers();
      setUsers(data);
    } catch (err: any) {
      setError(err?.message || 'Không tải được danh sách người dùng');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleDelete = async (id: number) => {
    if (!window.confirm('Bạn chắc chắn muốn xóa người dùng này?')) return;
    try {
      await deleteAdminUser(id);
      await load();
    } catch (err: any) {
      alert(err?.message || 'Xóa người dùng thất bại');
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-semibold">Quản lý người dùng</h1>
          <p className="text-sm text-gray-500">Chỉ admin mới xem/xóa được người dùng.</p>
        </div>
        <button
          onClick={load}
          className="inline-flex items-center px-3 py-2 text-sm text-emerald-600 hover:text-emerald-700"
        >
          <RefreshCwIcon className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
          Tải lại
        </button>
      </div>

      {error && <div className="text-sm text-red-600 mb-3">{error}</div>}

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tên</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Thao tác
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((u) => (
                <tr key={u.User_ID}>
                  <td className="px-4 py-3 text-sm text-gray-600">{u.User_ID}</td>
                  <td className="px-4 py-3 text-sm text-gray-900">{u.User_Email}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{u.User_Name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{u.Role || 'user'}</td>
                  <td className="px-4 py-3 text-right text-sm font-medium">
                    <button
                      onClick={() => handleDelete(u.User_ID)}
                      className="text-red-600 hover:text-red-800 inline-flex items-center"
                      disabled={loading}
                    >
                      <TrashIcon className="h-4 w-4 mr-1" />
                      Xóa
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!loading && users.length === 0 && (
          <div className="text-center py-8 text-gray-500">Chưa có dữ liệu người dùng.</div>
        )}
        {loading && <div className="text-center py-8 text-gray-500">Đang tải danh sách người dùng...</div>}
      </div>
    </div>
  );
};

export default AdminUsers;
