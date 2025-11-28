import React from 'react';
import { Link } from 'react-router-dom';
const Footer = () => {
  return (
    <footer className="bg-white border-t border-gray-200">
      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3">VietChoice</h3>
            <p className="text-gray-600 text-sm">
              Nền tảng tra cứu chất lượng sản phẩm hàng đầu Việt Nam, giúp người tiêu dùng đưa ra
              quyết định mua sắm thông minh.
            </p>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3">Liên kết</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/" className="text-gray-600 hover:text-emerald-600 text-sm">
                  Trang chủ
                </Link>
              </li>
              <li>
                <Link to="/products" className="text-gray-600 hover:text-emerald-600 text-sm">
                  Sản phẩm
                </Link>
              </li>
              <li>
                <Link to="/scanner" className="text-gray-600 hover:text-emerald-600 text-sm">
                  Quét mã
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3">Liên hệ</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>Email: contact@vietchoice.vn</li>
              <li>Điện thoại: (+84) 795-052-102</li>
              <li>Địa chỉ: Đà Nẵng, Việt Nam</li>
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-200 mt-6 pt-6 text-center text-sm text-gray-600">
          <p>© {new Date().getFullYear()} VietChoice. Tất cả các quyền được bảo lưu.</p>
        </div>
      </div>
    </footer>
  );
};
export default Footer;
