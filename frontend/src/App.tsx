import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';
import Home from './pages/Home';
import Scanner from './pages/Scanner';
import Products from './pages/Products';
import ProductDetail from './pages/ProductDetail';
import Auth from './pages/Auth';
import Profile from './pages/Profile';
import Admin from './pages/Admin';
import ProtectedRoute from './components/auth/ProtectedRoute';

import AdminUsers from './pages/AdminUsers';
export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Home />} />
          <Route path="scanner" element={<Scanner />} />
          <Route path="products" element={<Products />} />
          <Route path="product/:id" element={<ProductDetail />} />
          <Route path="auth" element={<Auth />} />
          <Route path="profile" element={<Profile />} />
          <Route 
            path="admin" 
            element={
              <ProtectedRoute requiredRole="admin">
                <Admin />
              </ProtectedRoute>
            } 
          />
          <Route path="admin" element={<Admin />} />
          <Route path="admin/users" element={<AdminUsers />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
