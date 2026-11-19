import { AuthProvider } from '../../context/AuthContext';
import PoliceDashboard from './PoliceDashboard';

export default function PoliceApp() {
  return (
    <AuthProvider requiredRole="police">
      <PoliceDashboard />
    </AuthProvider>
  );
}
