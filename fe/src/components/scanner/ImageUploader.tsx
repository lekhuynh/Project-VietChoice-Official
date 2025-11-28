import { type FC, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadIcon, ImageIcon, XIcon, Loader2Icon } from 'lucide-react';
import { type Product } from '../../types';
import { scanProductsByImage, type ProductMin } from '../../api/products';
import ProductCard from '../products/ProductCard';

const currency = (v?: number) =>
  typeof v === 'number'
    ? new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(v)
    : '';

const ImageUploader: FC = () => {
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [ocrResult, setOcrResult] = useState<string | null>(null);
  const [suggestedProducts, setSuggestedProducts] = useState<Product[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const toUiProduct = (p: ProductMin): Product => ({
    id: (p as any).Product_ID,
    name: (p as any).Product_Name,
    image: (p as any).Image_URL || '',
    price: currency(typeof (p as any).Price === 'number' ? (p as any).Price : Number((p as any).Price ?? 0)),
    rating: typeof (p as any).Avg_Rating === 'number' ? (p as any).Avg_Rating : 0,
    positivePercent: typeof (p as any).Positive_Percent === 'number' ? (p as any).Positive_Percent : 0,
    sentiment: ((p as any).Sentiment_Label?.toLowerCase() as Product['sentiment']) || undefined,
    brand: (p as any).Brand,
    origin: (p as any).Origin,
  });

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    const file = files[0];
    if (file && (file.type === 'image/jpeg' || file.type === 'image/png')) {
      setSelectedImage(file);
      setPreviewUrl(URL.createObjectURL(file));
      setOcrResult(null);
      setSuggestedProducts([]);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && (file.type === 'image/jpeg' || file.type === 'image/png')) {
      setSelectedImage(file);
      setPreviewUrl(URL.createObjectURL(file));
      setOcrResult(null);
      setSuggestedProducts([]);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const resetImage = () => {
    setSelectedImage(null);
    setPreviewUrl(null);
    setOcrResult(null);
    setSuggestedProducts([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const processImage = async () => {
    if (!selectedImage) return;
    setIsLoading(true);
    try {
      const raw = (await scanProductsByImage(selectedImage)) as unknown as any[];
      const products = (raw || []).filter((r: any) => r && (r.Product_ID || r.Product_Name));
      const message = (raw || []).find((r: any) => r && typeof r.message === 'string')?.message as string | undefined;
      if (products.length > 0) {
        const mapped = products.map(toUiProduct);
        setSuggestedProducts(mapped);
        setOcrResult('Đã nhận diện xong');
        if (mapped.length === 1) {
          navigate(`/product/${mapped[0].id}`);
        }
      } else if (message) {
        setSuggestedProducts([]);
        setOcrResult(message);
      } else {
        setSuggestedProducts([]);
        setOcrResult('Không nhận diện được nội dung trong ảnh. Hãy chụp rõ hơn hoặc thử quét mã vạch.');
      }
    } catch {
      setOcrResult('Không nhận diện được ảnh');
      setSuggestedProducts([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (selectedImage) {
      const id = window.setTimeout(() => {
        void processImage();
      }, 0);
      return () => window.clearTimeout(id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedImage]);

  return (
    <div className="flex flex-col items-center">
      {!ocrResult && (
        <div
          className={`w-full max-w-md border-2 border-dashed rounded-lg p-6 text-center ${previewUrl ? 'border-emerald-300' : 'border-gray-300'}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
        >
          {!previewUrl ? (
            <div className="space-y-4">
              <div className="flex justify-center">
                <ImageIcon className="h-12 w-12 text-gray-400" />
              </div>
              <div className="text-gray-600">
                <p className="text-sm">Kéo và thả ảnh vào đây hoặc</p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg, image/png"
                  onChange={handleImageSelect}
                  className="hidden"
                  id="image-upload"
                />
                <label
                  htmlFor="image-upload"
                  className="mt-2 inline-block px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-md cursor-pointer hover:bg-emerald-700"
                >
                  Chọn ảnh
                </label>
              </div>
              <p className="text-xs text-gray-500">Chấp nhận định dạng JPG, PNG</p>
            </div>
          ) : (
            <div className="relative">
              <img src={previewUrl} alt="Preview" className="max-h-64 mx-auto rounded" />
              <button
                onClick={resetImage}
                className="absolute top-2 right-2 bg-gray-800 bg-opacity-50 text-white rounded-full p-1 hover:bg-opacity-70"
              >
                <XIcon className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      )}

      {previewUrl && !ocrResult && (
        <button onClick={processImage} className="mt-4 px-4 py-2 bg-emerald-600 text-white rounded-md flex items-center" disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2Icon className="animate-spin h-5 w-5 mr-2" />
              Đang xử lý...
            </>
          ) : (
            <>
              <UploadIcon className="h-5 w-5 mr-2" />
              Xử lý ảnh
            </>
          )}
        </button>
      )}

      {ocrResult && (
        <div className="w-full max-w-5xl mt-6">
          <div className="bg-gray-100 p-4 rounded-md">
            <h3 className="font-medium mb-2">Kết quả nhận diện</h3>
            <p className="text-gray-700 bg-white p-2 rounded border border-gray-200">{ocrResult}</p>
          </div>
          {suggestedProducts.length > 0 && (
            <div className="mt-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-800">Sản phẩm gợi ý</h3>
                <span className="text-sm text-gray-500">{suggestedProducts.length} kết quả</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {suggestedProducts.map((product) => (
                  <ProductCard key={product.id} product={product} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
export default ImageUploader;
