import { Product } from '../../types';

interface BarcodeScannerState {
  scanResult: string | null;
  isScanning: boolean;
  isLoading: boolean;
  product: Product | null;
}

export type { BarcodeScannerState };
