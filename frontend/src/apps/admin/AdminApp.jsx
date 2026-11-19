import { Routes, Route } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import AdminLayout from './AdminLayout';
import ExecutiveOverview from '../../pages/ExecutiveOverview';
import CrimeRiskMap from '../../pages/CrimeRiskMap';
import IncidentPrioritization from '../../pages/IncidentPrioritization';

export default function AdminApp({ basePath = '' }) {
  return (
    <AuthProvider requiredRole="admin">
      <Routes>
        <Route element={<AdminLayout basePath={basePath} />}>
          <Route index element={<ExecutiveOverview />} />
          <Route path="crime-risk-map" element={<CrimeRiskMap />} />
          <Route path="incidents" element={<IncidentPrioritization />} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}
