import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2Icon, Eye, EyeOff } from 'lucide-react';
import { register } from '../../api/auth';

const RegisterForm: React.FC = () => {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    if (!name || !email || !password || !confirmPassword) {
      setError('Vui lòng nhập đầy đủ thông tin.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Mật khẩu xác nhận không khớp.');
      return;
    }
    setIsLoading(true);
    try {
      await register({ name, email, password });
      try {
        window.dispatchEvent(new CustomEvent('auth-change', { detail: { authenticated: true } }));
      } catch {}
      // Reload to show home after registration
      window.location.href = '/';
    } catch (err: any) {
      setError(err?.message || 'Đăng ký thất bại.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    // Thay đổi: space-y-1 -> space-y-6
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        // Thay đổi: Bỏ mb-6
        <div className="bg-red-50 text-red-600 p-4 rounded-lg text-sm font-medium">{error}</div>
      )}
      {/* Thay đổi: Bỏ mb-5 */}
      <div>
        <label htmlFor="name" className="block text-base font-semibold text-gray-800 mb-2">
          Họ và tên
        </label>
        <input
          type="text"
          id="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#00A878] focus:border-transparent text-base transition"
          placeholder="Nhập họ và tên của bạn"
        />
      </div>
      {/* Thay đổi: Bỏ mb-5 */}
      <div>
        <label htmlFor="email" className="block text-base font-semibold text-gray-800 mb-2">
          Email
        </label>
        <input
          type="email"
          id="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#00A878] focus:border-transparent text-base transition"
          placeholder="Nhập email của bạn"
        />
      </div>
      {/* Thay đổi: Bỏ mb-5 */}
      <div className="relative">
        <label htmlFor="password" className="block text-base font-semibold text-gray-800 mb-2">
          Mật khẩu (ít nhất 6 ký tự)
        </label>
        <input
          type={showPassword ? 'text' : 'password'}
          id="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#00A878] focus:border-transparent text-base transition"
          placeholder="Tạo mật khẩu"
        />
        <button type="button" className="absolute right-3 top-12 text-gray-500 hover:text-gray-700" onClick={() => setShowPassword((s) => !s)}>
          {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
        </button>
      </div>
      {/* Thay đổi: Bỏ mb-7 */}
      <div className="relative">
        <label htmlFor="confirmPassword" className="block text-base font-semibold text-gray-800 mb-2">
          Xác nhận mật khẩu
        </label>
        <input
          type={showConfirmPassword ? 'text' : 'password'}
          id="confirmPassword"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#00A878] focus:border-transparent text-base transition"
          placeholder="Nhập lại mật khẩu"
        />
        <button type="button" className="absolute right-3 top-12 text-gray-500 hover:text-gray-700" onClick={() => setShowConfirmPassword((s) => !s)}>
          {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
        </button>
      </div>
      <button
        type="submit"
        className="w-full py-3 px-4 bg-[#00A878] text-white font-semibold text-base rounded-lg hover:bg-[#008f68] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#00A878] flex justify-center transition duration-200"
        disabled={isLoading}
      >
        {isLoading ? (
          <>
            <Loader2Icon className="animate-spin h-5 w-5 mr-2" />
            Đang xử lý...
          </>
        ) : (
          'Đăng ký'
        )}
      </button>
    </form>
  );
};

export default RegisterForm;