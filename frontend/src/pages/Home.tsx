import React from 'react';
import ChatInterface from '../components/chat/ChatInterface';
const Home = () => {
  return (
    <div className="flex flex-col h-[calc(100dvh-140px)]">
      <div className="text-center mb-4">
        <h1 className="text-3xl font-bold text-gray-800">VietChoice</h1>
        <p className="text-gray-600 mt-2">
          Tra cứu chất lượng sản phẩm thông minh với trí tuệ nhân tạo
        </p>
      </div>
      <ChatInterface />
    </div>
  );
};
export default Home;
