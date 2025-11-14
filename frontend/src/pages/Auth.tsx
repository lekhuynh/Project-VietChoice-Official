import React, { useState, useRef } from 'react';
import LoginForm from '../components/auth/LoginForm';
import RegisterForm from '../components/auth/RegisterForm';
import { API_BASE_URL } from '../config';

const Auth = () => {
  const [activeTab, setActiveTab] = useState<'login' | 'register'>('login');
  const cardRef = useRef<HTMLDivElement>(null);

  const handleTabChange = (tab: 'login' | 'register') => {
    setActiveTab(tab);
  };
  return (
    <div className="min-h-screen flex items-start justify-center bg-gray-50 px-4 pt-24 pb-24">
      <div ref={cardRef} className="w-full max-w-md bg-white rounded-xl shadow-xl overflow-hidden">
        <div className="px-8 py-10">
          <h2 className="text-4xl font-bold text-[#00A878] text-center mb-10 tracking-tight">{activeTab === 'register' ? 'Đăng ký' : 'Đăng nhập'}</h2>

          <div className="">{activeTab === 'login' ? <LoginForm /> : <RegisterForm />}</div>

          <div className="text-center text-sm text-gray-600 mt-6 pt-6 border-t border-gray-200">
            {activeTab === 'register' ? (
              <>
                Đã có tài khoản?{' '}
                <button type="button" className="text-[#00A878] font-medium" onClick={() => handleTabChange('login')}>
                  Đăng nhập ngay
                </button>
              </>
            ) : (
              <>
                Chưa có tài khoản?{' '}
                <button type="button" className="text-[#00A878] font-medium" onClick={() => handleTabChange('register')}>
                  Đăng ký ngay
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Auth;