import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

export default function Layout() {
  return (
    <div className="min-h-screen bg-surface">
      <Sidebar />
      <div className="pl-72">
        <Header />
        <main className="w-full pt-16 bg-surface min-h-screen">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

