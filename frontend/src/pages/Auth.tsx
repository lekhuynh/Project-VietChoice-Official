import React, { useState } from 'react';
import LoginForm from '../components/auth/LoginForm';
import RegisterForm from '../components/auth/RegisterForm';
const Auth = () => {
  const [activeTab, setActiveTab] = useState('login');
  return (
    <div className="max-w-md mx-auto bg-white rounded-lg shadow-lg overflow-hidden">
      <div className="flex">
        <button
          className={`flex-1 py-4 text-center font-medium ${activeTab === 'login' ? 'text-emerald-600 border-b-2 border-emerald-600' : 'text-gray-500 border-b border-gray-200'}`}
          onClick={() => setActiveTab('login')}
        >
          Đăng nhập
        </button>
        <button
          className={`flex-1 py-4 text-center font-medium ${activeTab === 'register' ? 'text-emerald-600 border-b-2 border-emerald-600' : 'text-gray-500 border-b border-gray-200'}`}
          onClick={() => setActiveTab('register')}
        >
          Đăng ký
        </button>
      </div>
      <div className="p-6">{activeTab === 'login' ? <LoginForm /> : <RegisterForm />}</div>
    </div>
  );
};
export default Auth;
