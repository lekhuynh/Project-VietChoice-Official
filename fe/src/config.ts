// Central API configuration
// Uses Vite env var if provided, otherwise defaults to local FastAPI
// const fromVite = (import.meta as any)?.env?.VITE_API_BASE_URL;
// const fromProcess = (typeof process !== 'undefined' ? (process as any).env?.VITE_API_BASE_URL : undefined);
// const fallback = 'http://localhost:8000';

// export const API_BASE_URL: string = String(fromVite ?? fromProcess ?? fallback).replace(/\/+$/, '');
//export const API_BASE_URL = "http://127.0.0.1:8000";
export const API_BASE_URL = "/api";