import React, { useEffect, useState } from 'react';
import { UserIcon, ClockIcon, HistoryIcon, LogOutIcon } from 'lucide-react';
import { type Conversation } from '../types';
import { fetchUserProfile, updateUserProfile, changePassword, type UserProfile } from '../api/user';
import {
  fetchSearchHistory,
  fetchViewedHistory,
  deleteAllSearchHistory,
  deleteSearchHistoryItem,
  deleteAllViewedHistory,
  deleteViewedHistoryItem,
  type SearchHistoryItem,
  type ViewedHistoryItem,
} from '../api/history';
import Auth from './Auth';
import { logout as apiLogout } from '../api/auth';

const Profile: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'profile' | 'search-history' | 'view-history' | 'conversations'>('profile');
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [nameInput, setNameInput] = useState('');
  const [loadingProfile, setLoadingProfile] = useState(false);

  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([]);
  const [viewedHistory, setViewedHistory] = useState<ViewedHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [unauthenticated, setUnauthenticated] = useState(false);

  // Change password states
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [changingPassword, setChangingPassword] = useState(false);
  const [changePwError, setChangePwError] = useState<string | null>(null);
  const [changePwSuccess, setChangePwSuccess] = useState<string | null>(null);

  const formatDate = (dateString?: string | Date) => {
    if (!dateString) return '';
    const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
    return date.toLocaleDateString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const loadProfile = async () => {
    setLoadingProfile(true);
    setError(null);
    try {
      const p = await fetchUserProfile();
      setProfile(p);
      setNameInput(p.name || '');
      setUnauthenticated(false);
    } catch (e: any) {
      if (String(e?.message || '').toLowerCase().includes('unauthenticated')) {
        setUnauthenticated(true);
      } else {
        setError(e?.message || 'Không tải được hồ sơ');
      }
    } finally {
      setLoadingProfile(false);
    }
  };

  const loadHistories = async () => {
    setLoadingHistory(true);
    setError(null);
    try {
      const s = await fetchSearchHistory();
      const v = await fetchViewedHistory();
      setSearchHistory(s.history || []);
      setViewedHistory(v.viewed || []);
    } catch (e: any) {
      setError(e?.message || 'Không tải được lịch sử');
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    loadProfile();
    loadHistories();
  }, []);

  const handleUpdateProfile = async () => {
    try {
      const updated = await updateUserProfile({ name: nameInput.trim() });
      setProfile(updated);
      alert('Đã cập nhật thông tin');
    } catch (e: any) {
      alert(e?.message || 'Cập nhật thất bại');
    }
  };

  const handleDeleteSearchItem = async (id: number) => {
    await deleteSearchHistoryItem(id);
    setSearchHistory((prev) => prev.filter((h) => h.History_ID !== id));
  };
  const handleClearSearchHistory = async () => {
    await deleteAllSearchHistory();
    setSearchHistory([]);
  };

  const handleDeleteViewedItem = async (productId: number) => {
    await deleteViewedHistoryItem(productId);
    setViewedHistory((prev) => prev.filter((i) => i.Product_ID !== productId));
  };
  const handleClearViewedHistory = async () => {
    await deleteAllViewedHistory();
    setViewedHistory([]);
  };

  const handleLogout = async () => {
    try {
      await apiLogout();
    } catch (e) {
      // ignore errors
    } finally {
      setProfile(null);
      setSearchHistory([]);
      setViewedHistory([]);
      setUnauthenticated(true);
    }
  };

  const handleChangePassword = async () => {
    setChangePwError(null);
    setChangePwSuccess(null);
    const oldPw = oldPassword.trim();
    const newPw = newPassword.trim();
    const confirmPw = confirmPassword.trim();

    if (!oldPw || !newPw || !confirmPw) {
      setChangePwError('Vui lòng nhập đầy đủ thông tin.');
      return;
    }
    if (newPw.length < 6) {
      setChangePwError('Mật khẩu mới phải có ít nhất 6 ký tự.');
      return;
    }
    if (newPw !== confirmPw) {
      setChangePwError('Xác nhận mật khẩu không khớp.');
      return;
    }

    setChangingPassword(true);
    try {
      await changePassword({ old_password: oldPw, new_password: newPw, confirm_password: confirmPw });
      setChangePwSuccess('Đổi mật khẩu thành công.');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (e: any) {
      setChangePwError(e?.message || 'Đổi mật khẩu thất bại.');
    } finally {
      setChangingPassword(false);
    }
  };

  if (unauthenticated) {
    return (
      <div className="max-w-5xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Đăng nhập / Đăng ký</h1>
        <Auth />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Tài khoản của tôi</h1>
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="flex border-b border-gray-200">
          <button
            className={`flex items-center px-4 py-3 ${activeTab === 'profile' ? 'text-emerald-600 border-b-2 border-emerald-600' : 'text-gray-600 hover:text-gray-800'}`}
            onClick={() => setActiveTab('profile')}
          >
            <UserIcon className="h-5 w-5 mr-2" />
            Thông tin cá nhân
          </button>
          <button
            className={`flex items-center px-4 py-3 ${activeTab === 'search-history' ? 'text-emerald-600 border-b-2 border-emerald-600' : 'text-gray-600 hover:text-gray-800'}`}
            onClick={() => setActiveTab('search-history')}
          >
            <ClockIcon className="h-5 w-5 mr-2" />
            Lịch sử tìm kiếm
          </button>
          <button
            className={`flex items-center px-4 py-3 ${activeTab === 'view-history' ? 'text-emerald-600 border-b-2 border-emerald-600' : 'text-gray-600 hover:text-gray-800'}`}
            onClick={() => setActiveTab('view-history')}
          >
            <HistoryIcon className="h-5 w-5 mr-2" />
            Lịch sử đã xem
          </button>
          <button
            className={`flex items-center px-4 py-3 ${activeTab === 'conversations' ? 'text-emerald-600 border-b-2 border-emerald-600' : 'text-gray-600 hover:text-gray-800'}`}
            onClick={() => {
              setActiveTab('conversations');
              setSelectedConversation(null);
            }}
          >
            <HistoryIcon className="h-5 w-5 mr-2" />
            Lịch sử trò chuyện
          </button>
        </div>
        <div className="p-6">
          {activeTab === 'profile' && (
            <div>
              <div className="flex items-center justify-center mb-6">
                <div className="h-24 w-24 rounded-full bg-emerald-100 flex items-center justify-center">
                  <UserIcon className="h-12 w-12 text-emerald-600" />
                </div>
              </div>
              <div className="max-w-md mx-auto">
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Họ và tên</label>
                  <input
                    type="text"
                    value={nameInput}
                    onChange={(e) => setNameInput(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-700"
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    value={profile?.email ?? ''}
                    readOnly
                    className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-md text-gray-700"
                  />
                </div>
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ngày tham gia</label>
                  <input
                    type="text"
                    value={profile?.created_at ? formatDate(profile.created_at) : ''}
                    readOnly
                    className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-md text-gray-700"
                  />
                </div>
                <div className="flex justify-between">
                  <button onClick={handleUpdateProfile} className="px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700">
                    Cập nhật thông tin
                  </button>
                  <button onClick={handleLogout} className="flex items-center px-4 py-2 text-red-600 border border-red-600 rounded-md hover:bg-red-50">
                    <LogOutIcon className="h-4 w-4 mr-2" />
                    Đăng xuất
                  </button>
                </div>
                {loadingProfile && <div className="text-center text-gray-500 mt-3">Đang tải...</div>}
                {error && <div className="text-center text-red-600 mt-3">{error}</div>}

                <div className="mt-8 pt-6 border-t border-gray-200">
                  <h3 className="text-lg font-semibold mb-4">Đổi mật khẩu</h3>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Mật khẩu hiện tại</label>
                    <input
                      type="password"
                      value={oldPassword}
                      onChange={(e) => setOldPassword(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-700"
                    />
                  </div>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Mật khẩu mới</label>
                    <input
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-700"
                    />
                  </div>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Xác nhận mật khẩu mới</label>
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-700"
                    />
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={handleChangePassword}
                      disabled={changingPassword}
                      className={`px-4 py-2 rounded-md text-white ${changingPassword ? 'bg-emerald-400' : 'bg-emerald-600 hover:bg-emerald-700'}`}
                    >
                      {changingPassword ? 'Đang đổi...' : 'Đổi mật khẩu'}
                    </button>
                    <button
                      type="button"
                      onClick={() => { setOldPassword(''); setNewPassword(''); setConfirmPassword(''); setChangePwError(null); setChangePwSuccess(null); }}
                      className="px-4 py-2 rounded-md border border-gray-300 text-gray-700 hover:bg-gray-50"
                    >
                      Hủy
                    </button>
                  </div>
                  {changePwError && <div className="text-red-600 mt-3">{changePwError}</div>}
                  {changePwSuccess && <div className="text-emerald-600 mt-3">{changePwSuccess}</div>}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'search-history' && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium">Lịch sử tìm kiếm gần đây</h3>
                {searchHistory.length > 0 && (
                  <button className="text-sm text-red-600 hover:underline" onClick={handleClearSearchHistory}>Xóa tất cả</button>
                )}
              </div>
              {loadingHistory ? (
                <div className="text-center text-gray-500 py-6">Đang tải...</div>
              ) : searchHistory.length > 0 ? (
                <div className="space-y-3">
                  {searchHistory.map((item) => (
                    <div key={item.History_ID} className="p-3 bg-gray-50 rounded-md hover:bg-gray-100">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-medium">{item.Query}</p>
                          <p className="text-xs text-gray-500">{formatDate(item.Created_At)}</p>
                        </div>
                        <button className="text-xs text-red-600 hover:underline" onClick={() => handleDeleteSearchItem(item.History_ID)}>Xóa</button>
                      </div>
                      {item.Products?.length ? (
                        <div className="mt-2 grid grid-cols-2 md:grid-cols-3 gap-2">
                          {item.Products.slice(0, 6).map((p) => (
                            <a key={p.Product_ID} href={`/product/${p.Product_ID}`} className="flex items-center gap-2 p-2 bg-white border rounded hover:shadow-sm">
                              <img src={p.Image_URL || ''} alt={p.Product_Name} className="w-10 h-10 object-cover rounded" />
                              <div>
                                <div className="text-sm line-clamp-1">{p.Product_Name}</div>
                                <div className="text-xs text-gray-500">{typeof p.Price === 'number' ? p.Price.toLocaleString('vi-VN') + ' ₫' : ''}</div>
                              </div>
                            </a>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-4">Bạn chưa có lịch sử tìm kiếm nào.</p>
              )}
            </div>
          )}

          {activeTab === 'view-history' && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium">Lịch sử sản phẩm đã xem</h3>
                {viewedHistory.length > 0 && (
                  <button className="text-sm text-red-600 hover:underline" onClick={handleClearViewedHistory}>Xóa tất cả</button>
                )}
              </div>
              {loadingHistory ? (
                <div className="text-center text-gray-500 py-6">Đang tải...</div>
              ) : viewedHistory.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {viewedHistory.map((v) => (
                    <div key={v.Product_ID} className="flex items-center gap-3 p-3 bg-gray-50 rounded-md hover:bg-gray-100">
                      <a href={`/product/${v.Product_ID}`} className="flex items-center gap-3 flex-1">
                        <img src={v.Image_URL || ''} alt={v.Product_Name} className="w-12 h-12 object-cover rounded" />
                        <div>
                          <div className="font-medium line-clamp-1">{v.Product_Name}</div>
                          <div className="text-xs text-gray-500">{formatDate(v.Viewed_At)}</div>
                        </div>
                      </a>
                      <button className="text-xs text-red-600 hover:underline" onClick={() => handleDeleteViewedItem(v.Product_ID)}>Xóa</button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-4">Bạn chưa xem sản phẩm nào.</p>
              )}
            </div>
          )}

          {activeTab === 'conversations' && !selectedConversation && (
            <div>
              <h3 className="font-medium mb-4">Lịch sử trò chuyện</h3>
              <p className="text-gray-500">Hiện chưa có API trò chuyện trong backend được đồng bộ. Phần này sẽ được bổ sung sau.</p>
            </div>
          )}

          {activeTab === 'conversations' && selectedConversation && (
            <div>
              <div className="flex items-center mb-4">
                <button className="text-emerald-600 mr-2" onClick={() => setSelectedConversation(null)}>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z" clipRule="evenodd" />
                  </svg>
                </button>
                <h3 className="font-medium">{selectedConversation.title}</h3>
                <span className="text-xs text-gray-500 ml-2">{formatDate(selectedConversation.timestamp)}</span>
              </div>
              <div className="bg-gray-50 rounded-md p-4 space-y-4">
                {selectedConversation.messages.map((message) => (
                  <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] rounded-lg p-3 ${message.sender === 'user' ? 'bg-emerald-600 text-white' : 'bg-white text-gray-800 border border-gray-200'}`}>
                      <div>{message.content}</div>
                      <div className="text-xs mt-1 opacity-70">{formatDate(message.timestamp)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Profile;
