import React, { useState } from 'react';
import BarcodeScanner from '../components/scanner/BarcodeScanner';
import ImageUploader from '../components/scanner/ImageUploader';
import { BarcodeIcon, ImageIcon } from 'lucide-react';
/**
 * Scanner page
 *
 * Trang chứa hai tab chính:
 * - Quét mã vạch: sử dụng `BarcodeScanner` để quét bằng camera
 * - Quét ảnh chữ (OCR): sử dụng `ImageUploader` để upload ảnh và nhận dạng ký tự
 *
 * Chú ý: cả hai component hiện đang sử dụng mock/demo data. Khi tích hợp API,
 * chuyển các mock call thành fetch/axios và xử lý quyền camera, lỗi và trạng thái loading.
 */
const Scanner = () => {
  const [activeTab, setActiveTab] = useState('barcode');
  return (
    <div className="max-w-3xl mx-auto bg-white rounded-lg shadow-lg p-6">
      <h1 className="text-2xl font-bold text-center mb-6">Quét mã sản phẩm</h1>
      <div className="flex border-b border-gray-200 mb-6">
        <button
          className={`flex items-center px-4 py-2 border-b-2 font-medium text-sm ${activeTab === 'barcode' ? 'border-emerald-500 text-emerald-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
          onClick={() => setActiveTab('barcode')}
        >
          <BarcodeIcon className="w-5 h-5 mr-2" />
          Quét mã vạch
        </button>
        <button
          className={`flex items-center px-4 py-2 border-b-2 font-medium text-sm ${activeTab === 'image' ? 'border-emerald-500 text-emerald-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
          onClick={() => setActiveTab('image')}
        >
          <ImageIcon className="w-5 h-5 mr-2" />
          Quét ảnh chữ (OCR)
        </button>
      </div>
      <div className="mt-6">{activeTab === 'barcode' ? <BarcodeScanner /> : <ImageUploader />}</div>
    </div>
  );
};
export default Scanner;
