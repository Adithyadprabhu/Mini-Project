import { BrowserRouter, Routes, Route } from 'react-router-dom';
import TouristApp from './apps/tourist/TouristApp';
import AdminApp from './apps/admin/AdminApp';
import PoliceApp from './apps/police/PoliceApp';
import './index.css';

/**
 * Determines which independent application to mount based on:
 * 1. Subdomain: tourist.yourdomain.com, admin.yourdomain.com, police.yourdomain.com
 * 2. Localhost Subdomain: tourist.localhost, admin.localhost, police.localhost
 * 3. Path Fallback: /tourist, /admin, /police (for environments without local DNS)
 */
function DomainRouter() {
  const hostname = window.location.hostname.toLowerCase();

  // Subdomain detection for production and local development
  if (hostname.startsWith('tourist.') || hostname.startsWith('tourist-')) {
    return <TouristApp />;
  }

  if (hostname.startsWith('police.') || hostname.startsWith('police-')) {
    return <PoliceApp />;
  }

  if (hostname.startsWith('admin.') || hostname.startsWith('admin-')) {
    return <AdminApp basePath="" />;
  }

  // Path-based fallback routing for standard single-port testing
  return (
    <Routes>
      {/* 1. Tourist Application URL */}
      <Route path="/tourist/*" element={<TouristApp />} />

      {/* 2. Police Patrol Application URL */}
      <Route path="/police/*" element={<PoliceApp />} />

      {/* 3. Admin Web Application URL */}
      <Route path="/admin/*" element={<AdminApp basePath="/admin" />} />

      {/* Default root on apex domain directs to Admin Application */}
      <Route path="/*" element={<AdminApp basePath="" />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <DomainRouter />
    </BrowserRouter>
  );
}
