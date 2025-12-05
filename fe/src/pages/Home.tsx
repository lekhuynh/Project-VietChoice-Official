import React from 'react';
import { ShieldCheck, Star, AlertTriangle, Scan } from 'lucide-react';
import ChatInterface from '../components/chat/ChatInterface';

const quickActions = [
  { title: 'Kiểm tra nguồn gốc', desc: 'Quét mã vạch hoặc nhập tên', icon: ShieldCheck },
  { title: 'Sản phẩm tốt nhất', desc: 'Gợi ý độ tin cậy cao trên thị trường', icon: Star },
  { title: 'Đánh giá nhanh', desc: 'Tóm tắt review từ người dùng thật', icon: AlertTriangle },
  { title: 'Quét mã sản phẩm', desc: 'Dùng camera để tra cứu sản phẩm', icon: Scan },
];

const Home = () => {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_20%_20%,rgba(16,185,129,0.08),transparent_35%),radial-gradient(circle_at_80%_0%,rgba(59,130,246,0.08),transparent_30%),#f8fafc] text-slate-900">
      <div className="max-w-6xl mx-auto px-4 md:px-6 pt-12 pb-16">
        {/* Hero */}
        <div className="text-center space-y-3 mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-100">
            Tìm kiếm thông minh · Sẵn sàng hỗ trợ
          </div>
          <h1 className="text-3xl md:text-5xl font-bold tracking-tight">
            Trợ lý mua sắm <span className="text-emerald-600">VietChoice</span>
          </h1>
          <p className="text-lg text-slate-600">Đánh giá chất lượng, kiểm tra minh bạch và cảnh báo rủi ro.</p>
        </div>

        {/* Chat card */}
        <div className="max-w-4xl mx-auto rounded-3xl bg-white/85 backdrop-blur-xl border border-slate-100 shadow-[0_18px_50px_-25px_rgba(15,23,42,0.35)] p-4 md:p-6">
          <div className="rounded-2xl bg-gradient-to-b from-white to-slate-50 border border-slate-100 shadow-inner h-[540px]">
            <ChatInterface />
          </div>
        </div>

        {/* Quick actions */}
        <div className="max-w-4xl mx-auto mt-6 grid grid-cols-1 md:grid-cols-4 gap-3">
          {quickActions.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.title}
                className="rounded-2xl bg-white border border-slate-100 shadow-sm p-4 text-left hover:border-emerald-200 transition flex gap-3 items-start"
              >
                <span className="p-2 rounded-xl bg-emerald-50 text-emerald-700 shadow-sm">
                  <Icon size={18} />
                </span>
                <div>
                  <p className="text-sm font-semibold text-slate-900">{item.title}</p>
                  <p className="text-xs text-slate-600 mt-1">{item.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default Home;
