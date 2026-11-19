import { useState, useEffect } from 'react';
import { AuthContext } from './auth-context-def';
import * as api from '../services/api';

export function AuthProvider({ children, requiredRole = 'admin' }) {
  const getDefaultUser = (role) => ({
    id: `usr_${role}_active`,
    email: `${role}@yourdomain.com`,
    name: role === 'admin' ? 'Command Administrator' : role === 'police' ? 'Officer J. Vance' : null,
    role,
    badgeNumber: role === 'police' ? 'APD-504' : null,
    phone: '404-555-0199',
  });

  const requiresAuth = requiredRole === 'tourist';

  const [user, setUser] = useState(() => {
    if (!requiresAuth) return getDefaultUser(requiredRole);
    try {
      const saved = localStorage.getItem('sentinel_auth_user');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.role === 'tourist') return parsed;
      }
    } catch { /* ignore */ }
    return null;
  });

  const [loading, setLoading] = useState(requiresAuth);

  useEffect(() => {
    if (!requiresAuth) return;
    let cancelled = false;
    async function verify() {
      try {
        const token = localStorage.getItem('sentinel_auth_token');
        if (!token) { setLoading(false); return; }
        const currentUser = await api.fetchCurrentUser();
        if (cancelled) return;
        if (currentUser && currentUser.role === 'tourist') {
          setUser(currentUser);
        } else {
          setUser(null);
          localStorage.removeItem('sentinel_auth_token');
          localStorage.removeItem('sentinel_auth_user');
        }
      } catch {
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    verify();
    return () => { cancelled = true; };
  }, [requiresAuth]);

  const handleLogin = async (email, password, roleRequirement = requiredRole) => {
    const res = await api.login({ email, password, requiredRole: roleRequirement });
    setUser(res.user);
    return res.user;
  };

  const handleRegister = async (payload) => {
    const res = await api.register(payload);
    setUser(res.user);
    return res.user;
  };

  const handleLogout = async () => {
    await api.logout().catch(() => {});
    if (requiresAuth) {
      setUser(null);
    } else {
      setUser(getDefaultUser(requiredRole));
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user: requiresAuth ? user : (user || getDefaultUser(requiredRole)),
        loading,
        login: handleLogin,
        register: handleRegister,
        logout: handleLogout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
