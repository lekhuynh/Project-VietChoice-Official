import { type FC, useEffect, useRef, useState } from 'react';
import { CameraIcon, XIcon, Loader2Icon } from 'lucide-react';
import { Html5Qrcode, Html5QrcodeSupportedFormats } from 'html5-qrcode';
import { Link } from 'react-router-dom';
import { API_BASE_URL } from '../../config';
import { type Product } from '../../types';
import { type ProductMin } from '../../api/products';

const formatPrice = (v?: number) => {
  if (v === undefined || v === null) return '';
  try {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(
      Number(v)
    );
  } catch {
    return `${v} ₫`;
  }
};

const BarcodeScanner: FC = () => {
  const [scanResult, setScanResult] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const STORAGE_KEY = 'vc_scanner_barcode_state_v1';
  const scannerRef = useRef<Html5Qrcode | null>(null);

  const toUiProduct = (p: ProductMin): Product => ({
    id: p.Product_ID,
    name: p.Product_Name,
    image: p.Image_URL || '',
    price: formatPrice(typeof p.Price === 'number' ? p.Price : Number((p as any).Price ?? 0)),
    rating: typeof p.Avg_Rating === 'number' ? p.Avg_Rating : 0,
    positivePercent: 0,
    sentiment: (p.Sentiment_Label?.toLowerCase() as Product['sentiment']) || undefined,
    brand: (p as any).Brand,
    origin: (p as any).Origin,
  });

  const ensureContainer = async () => {
    await new Promise<void>((resolve) => {
      const tick = () => {
        if (document.getElementById('qr-reader')) return resolve();
        requestAnimationFrame(tick);
      };
      tick();
    });
  };

  const startScanner = async () => {
    setProducts([]);
    setScanResult(null);
    setError(null);
    setIsScanning(true);
    await ensureContainer();
    if (!scannerRef.current) scannerRef.current = new Html5Qrcode('qr-reader');
    const onScanSuccess = (decodedText: string) => {
      setScanResult((prev) => (prev === decodedText ? prev : decodedText));
      setError(null);
    };
    const onScanFailure = (_: string) => {};
    try {
      await scannerRef.current.start(
        { facingMode: 'environment' },
        {
          fps: 10,
          qrbox: 250,
          experimentalFeatures: { useBarCodeDetectorIfSupported: true },
          formatsToSupport: [
            Html5QrcodeSupportedFormats.EAN_13,
            Html5QrcodeSupportedFormats.EAN_8,
            Html5QrcodeSupportedFormats.CODE_128,
            Html5QrcodeSupportedFormats.CODE_39,
            Html5QrcodeSupportedFormats.UPC_A,
            Html5QrcodeSupportedFormats.UPC_E,
            Html5QrcodeSupportedFormats.QR_CODE,
          ],
        },
        onScanSuccess,
        onScanFailure
      );
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error('Failed to start camera', e);
      setError('Không mở được camera. Vui lòng kiểm tra quyền truy cập.');
      setIsScanning(false);
    }
  };

  // Load persisted scan state on mount
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as { scanResult?: string | null; products?: Product[] };
        if (typeof parsed.scanResult === 'string' || parsed.scanResult === null) {
          setScanResult(parsed.scanResult ?? null);
        }
        if (Array.isArray(parsed.products)) {
          setProducts(parsed.products as Product[]);
        }
      }
    } catch {}
  }, []);

  // Persist scan state when results change
  useEffect(() => {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ scanResult, products })
      );
    } catch {}
  }, [scanResult, products]);

  const stopScanner = async () => {
    try {
      await scannerRef.current?.stop();
    } catch {}
    try {
      await scannerRef.current?.clear();
    } catch {}
    setIsScanning(false);
  };

  const captureAndScan = async () => {
    setIsLoading(true);
    setError(null);
    let attempted = false;
    try {
      const video: HTMLVideoElement | null = document.querySelector('#qr-reader video');
      if (video && video.videoWidth && video.videoHeight) {
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          const dataUrl = canvas.toDataURL('image/png');
          const blob = await (await fetch(dataUrl)).blob();
          const file = new File([blob], 'capture.png', { type: 'image/png' });
          const form = new FormData();
          form.append('file', file);
          const res = await fetch(`${API_BASE_URL}/products/barcode/scan`, {
            method: 'POST',
            body: form,
            credentials: 'include',
          });
          attempted = true;
          if (res.ok) {
            const payload = await res.json();
            const items = (payload?.results ?? []) as ProductMin[];
            if (items && items.length > 0) {
              setProducts(items.map(toUiProduct));
              setIsLoading(false);
              return;
            }
            // No items; surface message or fallback to code path
            if (payload?.codes && Array.isArray(payload.codes) && payload.codes.length > 0) {
              setError(`Không tìm thấy sản phẩm cho mã: ${payload.codes[0]}`);
            } else {
              setError('Không nhận diện được mã vạch trong ảnh.');
            }
          }
        }
      }
    } catch {
      // fall through to code-based lookup
    }

    // Fallback: use the live decoded text if available
    const code = String(scanResult || '').replace(/\D/g, '');
    if (code && code.length >= 6) {
      try {
        let results: ProductMin[] = [];
        const r1 = await fetch(`${API_BASE_URL}/products/barcode?barcode=${encodeURIComponent(code)}`, {
          credentials: 'include',
        });
        if (r1.ok) {
          const d = await r1.json();
          results = (d?.results ?? []) as ProductMin[];
        } else {
          const r2 = await fetch(`${API_BASE_URL}/products/barcode/${encodeURIComponent(code)}`, {
            credentials: 'include',
          });
          if (r2.ok) {
            const d2 = await r2.json();
            results = (d2?.results ?? []) as ProductMin[];
          }
        }
        if (results && results.length > 0) {
          setProducts(results.map(toUiProduct));
        } else {
          setProducts([]);
          setError('Không tìm thấy sản phẩm cho mã vạch này.');
        }
      } catch {
        setProducts([]);
        setError('Không thể tra cứu sản phẩm bằng mã vạch.');
      } finally {
        setIsLoading(false);
      }
    } else {
      setIsLoading(false);
      if (!attempted) setError('Không thể chụp/đọc mã. Vui lòng đưa mã rõ nét vào khung.');
    }
  };

  useEffect(() => {
    return () => {
      (async () => {
        try {
          await scannerRef.current?.stop();
        } catch {}
        try {
          await scannerRef.current?.clear();
        } catch {}
      })();
    };
  }, []);

  return (
    <div className="flex flex-col items-center">
      {!isScanning && (
        <div className="text-center mb-6">
          <p className="text-gray-600 mb-4">Quét mã vạch để tìm sản phẩm nhanh chóng</p>
          <button onClick={startScanner} className="bg-emerald-600 text-white px-4 py-2 rounded-md flex items-center justify-center">
            <CameraIcon className="w-5 h-5 mr-2" />
            Bắt đầu quét
          </button>
          {error && <div className="mt-2 text-sm text-red-600">{error}</div>}
        </div>
      )}

      {isScanning && (
        <div className="w-full max-w-md">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-medium">Đưa mã vạch vào khung hình</h3>
            <div className="flex items-center gap-2">
              <button onClick={captureAndScan} disabled={isLoading} title="Chụp ảnh & quét"
                className={`px-3 py-1 rounded text-white ${isLoading ? 'bg-gray-300 cursor-wait' : 'bg-emerald-600 hover:bg-emerald-700'}`}>
                Chụp ảnh & quét
              </button>
              <button onClick={stopScanner} title="Dừng" className="text-gray-500 hover:text-gray-700">
                <XIcon className="w-5 h-5" />
              </button>
            </div>
          </div>
          <div id="qr-reader" className="w-full"></div>
          {scanResult && (
            <div className="mt-3 text-sm text-gray-700">
              Mã đã nhận: <span className="font-mono bg-gray-100 px-2 py-1 rounded">{scanResult}</span>
            </div>
          )}
          {error && <div className="mt-2 text-sm text-red-600">{error}</div>}
        </div>
      )}

      {isLoading && (
        <div className="flex items-center justify-center mt-6">
          <Loader2Icon className="animate-spin h-6 w-6 mr-2 text-emerald-600" />
          <span>Đang tìm thông tin sản phẩm...</span>
        </div>
      )}

      {products.length > 0 && (
        <div className="w-full max-w-md mt-6">
          <h3 className="font-medium mb-3">Sản phẩm tìm thấy:</h3>
          <div className="space-y-4">
            {products.map((product) => (
              <Link key={product.id} to={`/product/${product.id}`} className="block bg-white rounded-lg shadow p-3">
                <div className="flex">
                  <img src={product.image} alt={product.name} className="w-16 h-16 object-cover rounded" />
                  <div className="ml-3">
                    <h4 className="font-medium hover:text-emerald-600">{product.name}</h4>
                    <p className="text-emerald-600">{product.price}</p>
                    <div className="flex items-center mt-1 text-sm">
                      <span className="ml-1">{product.rating}/5</span>
                      {product.brand && <span className="mx-2">•</span>}
                      {product.brand && <span>{product.brand}</span>}
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default BarcodeScanner;
