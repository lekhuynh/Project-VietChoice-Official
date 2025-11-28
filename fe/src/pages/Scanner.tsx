import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import BarcodeScanner from "../components/scanner/BarcodeScanner";
import ImageUploader from "../components/scanner/ImageUploader";
import { BarcodeIcon, ImageIcon } from "lucide-react";

/**
 * Scanner page
 *
 * Trang chứa hai tab chính:
 * - Quét mã vạch: dùng `BarcodeScanner` để quét bằng camera
 * - Quét ảnh (OCR): dùng `ImageUploader` để upload ảnh và nhận dạng ký tự
 *
 * Lưu ý: cần cấp quyền camera khi quét mã vạch. Ảnh sẽ tự xử lý khi tải lên ở tab OCR.
 */
const Scanner = () => {
  const TAB_KEY = "vc_scanner_tab_v1";
  const [activeTab, setActiveTab] = useState<'barcode' | 'image'>(() => {
    try {
      const raw = localStorage.getItem(TAB_KEY);
      if (raw === "barcode" || raw === "image") return raw;
    } catch {}
    return "image";
  });
  const [searchParams] = useSearchParams();

  useEffect(() => {
    try {
      localStorage.setItem(TAB_KEY, activeTab);
    } catch {}
  }, [activeTab]);

  // Allow tab override via query param (?tab=image|barcode)
  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab === 'image' || tab === 'barcode') {
      setActiveTab(tab);
    }
  }, [searchParams]);

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
          Quét ảnh (OCR)
        </button>
      </div>
      <div className="mt-6">{activeTab === 'barcode' ? <BarcodeScanner /> : <ImageUploader />}</div>
    </div>
  );
};
export default Scanner;
