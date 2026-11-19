import { useState } from 'react';
import { AuthProvider } from '../../context/AuthContext';
import { useAuth } from '../../context/useAuth';
import { LanguageProvider } from './LanguageContext';
import TouristLogin from './TouristLogin';
import BottomNav from './components/BottomNav';
import HomePage from './pages/HomePage';
import CrimeMapPage from './pages/CrimeMapPage';
import SafeRoutesPage from './pages/SafeRoutesPage';
import AlertsPage from './pages/AlertsPage';
import ProfilePage from './pages/ProfilePage';

function TouristRoot() {
  const { user, loading } = useAuth();
  const [activeTab, setActiveTab] = useState('home');

  if (loading) {
    return (
      <div className="min-h-screen bg-surface flex flex-col items-center justify-center p-4 gap-3">
        <div className="w-14 h-14 rounded-2xl bg-secondary/10 flex items-center justify-center">
          <span className="material-symbols-outlined text-secondary text-3xl animate-pulse">shield</span>
        </div>
        <span className="text-xs text-outline font-mono">Initializing Tourist Guardian...</span>
        <span className="w-5 h-5 border-2 border-secondary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user || user.role !== 'tourist') {
    return <TouristLogin />;
  }

  const renderPage = () => {
    switch (activeTab) {
      case 'map':
        return <CrimeMapPage />;
      case 'routes':
        return <SafeRoutesPage />;
      case 'alerts':
        return <AlertsPage />;
      case 'profile':
        return <ProfilePage />;
      default:
        return <HomePage onTabChange={setActiveTab} />;
    }
  };

  return (
    <div className="h-screen max-h-screen bg-[#0b111e] text-slate-100 flex flex-col max-w-md mx-auto relative shadow-2xl overflow-hidden font-sans antialiased">
      {/* Scrollable page body */}
      <div className="flex-1 min-h-0 overflow-y-auto flex flex-col relative w-full">
        {renderPage()}
      </div>

      {/* Persistent Bottom Navigation */}
      <BottomNav activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  );
}

export default function TouristApp() {
  return (
    <AuthProvider requiredRole="tourist">
      <LanguageProvider>
        <TouristRoot />
      </LanguageProvider>
    </AuthProvider>
  );
}
