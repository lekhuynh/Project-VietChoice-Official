import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2Icon, Eye, EyeOff } from 'lucide-react';
import { login } from '../../api/auth';

const LoginForm: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    if (!email || !password) {
      setError('Vui lòng nhập đầy đủ thông tin.');
      return;
    }
    setIsLoading(true);
    try {
      await login({ email, password });
      // Notify other parts of the app that auth succeeded, then navigate
      try {
        window.dispatchEvent(new CustomEvent('auth-change', { detail: { authenticated: true } }));
      } catch {
        // ignore if CustomEvent isn't supported
      }
      // Reload/navigate to profile
      window.location.href = '/profile';
    } catch (err: any) {
      setError(err?.message || 'Đăng nhập thất bại.');
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
      {/* Thay đổi: Bỏ mb-7 */}
      <div className="relative">
        <label htmlFor="password" className="block text-base font-semibold text-gray-800 mb-2">
          Mật khẩu
        </label>
        <input
          type={showPassword ? 'text' : 'password'}
          id="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#00A878] focus:border-transparent text-base transition"
          placeholder="Nhập mật khẩu của bạn"
        />
        <button type="button" className="absolute right-3 top-12 text-gray-500 hover:text-gray-700" onClick={() => setShowPassword((s) => !s)}>
          {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
        </button>
      </div>
      {/* Thay đổi: Bỏ mb-8 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <input
            id="remember"
            type="checkbox"
            className="h-5 w-5 accent-[#00A878] border-gray-300 rounded focus:ring-[#00A878]"
          />
          <label htmlFor="remember" className="ml-3 block text-sm font-medium text-gray-700">
            Ghi nhớ đăng nhập
          </label>
        </div>
        <div className="text-sm">
          <a href="#" className="font-medium text-[#00A878] hover:text-[#008f68] transition">
            Quên mật khẩu?
          </a>
        </div>
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
          'Đăng nhập'
        )}
      </button>
    </form>
  );
};

export default LoginForm;