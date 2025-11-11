import { type FC, useEffect, useState } from 'react';
import { CameraIcon, XIcon, Loader2Icon } from 'lucide-react';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { type Product } from '../../types';
import { fetchProductsByBarcode, type ProductMin } from '../../api/products';

const currency = (v?: number) => (typeof v === 'number' ? v.toLocaleString('vi-VN') + ' ₫' : '');

const BarcodeScanner: FC = () => {
  const [scanResult, setScanResult] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [product, setProduct] = useState<Product | null>(null);

  const toUiProduct = (p: ProductMin): Product => ({
    id: p.Product_ID,
    name: p.Product_Name,
    image: p.Image_URL || '',
    price: currency(typeof p.Price === 'number' ? p.Price : Number((p as any).Price ?? 0)),
    rating: typeof p.Avg_Rating === 'number' ? p.Avg_Rating : 0,
    positivePercent: 0,
    sentiment: (p.Sentiment_Label?.toLowerCase() as Product['sentiment']) || undefined,
    brand: (p as any).Brand,
    origin: (p as any).Origin,
  });

  const startScanner = () => {
    setIsScanning(true);
    setScanResult(null);
    setProduct(null);
    const html5QrcodeScanner = new Html5QrcodeScanner(
      'qr-reader',
      {
        fps: 10,
        qrbox: 250,
        rememberLastUsedCamera: true,
      },
      false
    );
    html5QrcodeScanner.render(onScanSuccess, onScanError);

    async function onScanSuccess(decodedText: string) {
      setScanResult(decodedText);
      setIsScanning(false);
      html5QrcodeScanner.clear();
      setIsLoading(true);
      try {
        const results = await fetchProductsByBarcode(decodedText);
        const first = results[0];
        setProduct(first ? toUiProduct(first) : null);
      } catch (e) {
        setProduct(null);
      } finally {
        setIsLoading(false);
      }
    }
    function onScanError(error: string) {
      console.warn(`Code scan error = ${error}`);
    }
  };

  const stopScanner = () => {
    setIsScanning(false);
  };

  useEffect(() => {
    return () => {
      if (isScanning) {
        const el = document.getElementById('qr-reader');
        if (el) el.innerHTML = '';
      }
    };
  }, [isScanning]);

  return (
    <div className="flex flex-col items-center">
      {!isScanning && !scanResult && (
        <div className="text-center mb-6">
          <p className="text-gray-600 mb-4">Quét mã vạch để tìm sản phẩm nhanh chóng</p>
          <button onClick={startScanner} className="bg-emerald-600 text-white px-4 py-2 rounded-md flex items-center justify-center">
            <CameraIcon className="w-5 h-5 mr-2" />
            Bắt đầu quét
          </button>
        </div>
      )}

      {isScanning && (
        <div className="w-full max-w-md">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-medium">Đưa mã vạch vào khung hình</h3>
            <button onClick={stopScanner} className="text-gray-500 hover:text-gray-700">
              <XIcon className="w-5 h-5" />
            </button>
          </div>
          <div id="qr-reader" className="w-full"></div>
        </div>
      )}

      {scanResult && (
        <div className="w-full max-w-md mt-4">
          <div className="bg-gray-100 p-4 rounded-md">
            <h3 className="font-medium mb-2">Kết quả quét:</h3>
            <p className="text-gray-700 font-mono bg-white p-2 rounded border border-gray-200">{scanResult}</p>
          </div>
        </div>
      )}

      {isLoading && (
        <div className="flex items-center justify-center mt-6">
          <Loader2Icon className="animate-spin h-6 w-6 mr-2 text-emerald-600" />
          <span>Đang tìm thông tin sản phẩm...</span>
        </div>
      )}

      {product && (
        <div className="w-full max-w-md mt-6 bg-white rounded-lg shadow-md overflow-hidden">
          <div className="p-4">
            <div className="flex items-start space-x-4">
              <img src={product.image} alt={product.name} className="w-24 h-24 object-cover rounded" />
              <div>
                <h3 className="font-medium text-lg">{product.name}</h3>
                <p className="text-emerald-600 font-medium mt-1">{product.price}</p>
                <div className="mt-2 text-sm text-gray-600">
                  {product.brand && <p>Thương hiệu: {product.brand}</p>}
                  {product.origin && <p>Xuất xứ: {product.origin}</p>}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default BarcodeScanner;
