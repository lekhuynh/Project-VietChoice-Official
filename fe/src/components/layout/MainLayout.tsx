import { type FC } from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';
import Footer from './Footer';

const MainLayout: FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Navbar />
      <main className="flex-grow container mx-auto px-4 py-6 pt-24 md:pt-24">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
};
export default MainLayout;
